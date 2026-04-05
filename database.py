"""SQLite storage for users, downloads, and bot analytics."""

import os
import sqlite3
import time
from typing import Any, Callable, TypeVar

from config import (
    DATABASE_FILE,
    SQLITE_BUSY_TIMEOUT_MS,
    SQLITE_RETRY_ATTEMPTS,
    SQLITE_RETRY_BACKOFF_MS,
)

T = TypeVar("T")


def get_db():
    # Ensure parent directory exists (critical for /tmp/... paths on Railway).
    db_dir = os.path.dirname(os.path.abspath(DATABASE_FILE))
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE, timeout=max(SQLITE_BUSY_TIMEOUT_MS / 1000, 1))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    # FULL is slower but safer on abrupt restart or container recycle.
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def _is_retryable_sqlite_error(exc: sqlite3.OperationalError) -> bool:
    text = str(exc).lower()
    return "database is locked" in text or "database is busy" in text or "locked" in text


def _run_db(fn: Callable[[sqlite3.Connection], T], *, write: bool = False) -> T:
    last_error: Exception | None = None
    for attempt in range(SQLITE_RETRY_ATTEMPTS):
        conn = None
        try:
            conn = get_db()
            if write:
                conn.execute("BEGIN IMMEDIATE")
            result = fn(conn)
            if write:
                conn.commit()
            return result
        except sqlite3.OperationalError as exc:
            if conn is not None and write:
                conn.rollback()
            if _is_retryable_sqlite_error(exc) and attempt < SQLITE_RETRY_ATTEMPTS - 1:
                time.sleep((SQLITE_RETRY_BACKOFF_MS / 1000.0) * (attempt + 1))
                last_error = exc
                continue
            raise
        finally:
            if conn is not None:
                conn.close()
    if last_error:
        raise last_error
    raise RuntimeError("Database operation failed unexpectedly.")


def _safe_add_column(cursor, table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass


def init_database():
    def _op(conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id           INTEGER PRIMARY KEY,
                username          TEXT,
                first_name        TEXT,
                last_name         TEXT,
                language_code     TEXT    DEFAULT 'en',
                is_premium        INTEGER DEFAULT 0,
                is_banned         INTEGER DEFAULT 0,
                joined_at         TEXT    DEFAULT (datetime('now')),
                last_active       TEXT    DEFAULT (datetime('now')),
                total_downloads   INTEGER DEFAULT 0,
                total_bytes       INTEGER DEFAULT 0,
                preferred_lang    TEXT    DEFAULT 'en',
                preferred_quality TEXT    DEFAULT 'best'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER,
                url           TEXT    NOT NULL,
                content_type  TEXT    DEFAULT 'video',
                platform      TEXT    DEFAULT 'instagram',
                file_size     INTEGER DEFAULT 0,
                duration      INTEGER,
                status        TEXT    DEFAULT 'success',
                error_message TEXT,
                downloaded_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_stats (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Helpful indexes for high-volume stat/history queries.
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_user_time ON downloads(user_id, downloaded_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)")

        # Migration: add columns to existing deployments without data loss.
        _safe_add_column(cursor, "users", "preferred_lang", "TEXT DEFAULT 'en'")
        _safe_add_column(cursor, "users", "preferred_quality", "TEXT DEFAULT 'best'")
        _safe_add_column(cursor, "downloads", "platform", "TEXT DEFAULT 'instagram'")

    _run_db(_op, write=True)


# ═════════════════════════════════════════════════════
#  USER OPERATIONS
# ═════════════════════════════════════════════════════

def register_user(user):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute("""
            INSERT INTO users (user_id, username, first_name, last_name, language_code, last_active)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                username    = excluded.username,
                first_name  = excluded.first_name,
                last_name   = excluded.last_name,
                language_code = excluded.language_code,
                last_active = datetime('now')
        """, (
            user.id,
            user.username or "",
            user.first_name or "",
            user.last_name or "",
            user.language_code or "en",
        ))

    _run_db(_op, write=True)


def is_user_banned(user_id: int) -> bool:
    def _op(conn: sqlite3.Connection):
        return conn.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

    row = _run_db(_op)
    return bool(row and row["is_banned"])


def ban_user(user_id: int):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))

    _run_db(_op, write=True)


def unban_user(user_id: int):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))

    _run_db(_op, write=True)


def get_user_lang(user_id: int) -> str:
    def _op(conn: sqlite3.Connection):
        return conn.execute(
            "SELECT preferred_lang FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

    row = _run_db(_op)
    return row["preferred_lang"] if (row and row["preferred_lang"]) else "en"


def set_user_lang(user_id: int, lang: str):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE users SET preferred_lang = ? WHERE user_id = ?", (lang, user_id)
        )

    _run_db(_op, write=True)


def get_user_quality(user_id: int) -> str:
    def _op(conn: sqlite3.Connection):
        return conn.execute(
            "SELECT preferred_quality FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

    row = _run_db(_op)
    return row["preferred_quality"] if (row and row["preferred_quality"]) else "best"


def set_user_quality(user_id: int, quality: str):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE users SET preferred_quality = ? WHERE user_id = ?", (quality, user_id)
        )

    _run_db(_op, write=True)


def get_user_stats(user_id: int) -> dict:
    def _op(conn: sqlite3.Connection) -> dict:
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if not user:
            return {
                "total_downloads": 0,
                "total_bytes": 0,
                "videos": 0,
                "images": 0,
                "audios": 0,
                "joined_at": "Unknown",
                "rank": 0,
            }

        videos = conn.execute(
            "SELECT COUNT(*) as c FROM downloads "
            "WHERE user_id = ? AND content_type = 'video' AND status = 'success'",
            (user_id,)
        ).fetchone()["c"]

        images = conn.execute(
            "SELECT COUNT(*) as c FROM downloads "
            "WHERE user_id = ? AND content_type = 'image' AND status = 'success'",
            (user_id,)
        ).fetchone()["c"]

        audios = conn.execute(
            "SELECT COUNT(*) as c FROM downloads "
            "WHERE user_id = ? AND content_type = 'audio' AND status = 'success'",
            (user_id,)
        ).fetchone()["c"]

        rank = conn.execute("""
            SELECT COUNT(*) + 1 as rank FROM users
            WHERE total_downloads > (
                SELECT total_downloads FROM users WHERE user_id = ?
            )
        """, (user_id,)).fetchone()["rank"]

        return {
            "total_downloads": user["total_downloads"],
            "total_bytes": user["total_bytes"],
            "videos": videos,
            "images": images,
            "audios": audios,
            "joined_at": user["joined_at"],
            "rank": rank,
        }

    return _run_db(_op)


def get_user_history(user_id: int, limit: int = 10) -> list:
    def _op(conn: sqlite3.Connection):
        return conn.execute("""
            SELECT url, content_type, platform, file_size, duration, status, downloaded_at
            FROM downloads
            WHERE user_id = ? AND status = 'success'
            ORDER BY downloaded_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()

    rows = _run_db(_op)
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════
#  DOWNLOAD OPERATIONS
# ═════════════════════════════════════════════════════

def record_download(user_id: int, url: str, content_type: str,
                    file_size: int, duration: int = None,
                    status: str = "success", error_message: str = None,
                    platform: str = "instagram"):
    def _op(conn: sqlite3.Connection) -> None:
        # Make this idempotent-safe for newly seen users after restarts.
        conn.execute(
            "INSERT OR IGNORE INTO users (user_id, last_active) VALUES (?, datetime('now'))",
            (user_id,),
        )

        conn.execute("""
            INSERT INTO downloads
                (user_id, url, content_type, platform, file_size, duration, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, url, content_type, platform,
              file_size, duration, status, error_message))

        if status == "success":
            conn.execute("""
                UPDATE users SET
                    total_downloads = total_downloads + 1,
                    total_bytes     = total_bytes + ?,
                    last_active     = datetime('now')
                WHERE user_id = ?
            """, (file_size, user_id))

    _run_db(_op, write=True)


def get_downloads_last_minute(user_id: int) -> int:
    def _op(conn: sqlite3.Connection):
        return conn.execute("""
            SELECT COUNT(*) as c FROM downloads
            WHERE user_id = ? AND downloaded_at > datetime('now', '-1 minute')
        """, (user_id,)).fetchone()["c"]

    count = _run_db(_op)
    return count


# ═════════════════════════════════════════════════════
#  GLOBAL STATS (Admin)
# ═════════════════════════════════════════════════════

def get_global_stats() -> dict:
    def _op(conn: sqlite3.Connection) -> dict:
        def _count(sql: str, *args: Any) -> int:
            return conn.execute(sql, args).fetchone()[0]

        total_users = _count("SELECT COUNT(*) FROM users")
        active_today = _count(
            "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')"
        )
        total_downloads = _count("SELECT COUNT(*) FROM downloads WHERE status = 'success'")
        total_bytes = conn.execute(
            "SELECT COALESCE(SUM(file_size), 0) FROM downloads WHERE status = 'success'"
        ).fetchone()[0]
        total_videos = _count(
            "SELECT COUNT(*) FROM downloads WHERE content_type = 'video' AND status = 'success'"
        )
        total_images = _count(
            "SELECT COUNT(*) FROM downloads WHERE content_type = 'image' AND status = 'success'"
        )
        total_audios = _count(
            "SELECT COUNT(*) FROM downloads WHERE content_type = 'audio' AND status = 'success'"
        )
        failed_downloads = _count("SELECT COUNT(*) FROM downloads WHERE status = 'failed'")
        banned_users = _count("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        downloads_today = _count(
            "SELECT COUNT(*) FROM downloads "
            "WHERE status = 'success' AND downloaded_at > datetime('now', '-1 day')"
        )

        top_users = conn.execute("""
            SELECT user_id, first_name, username, total_downloads
            FROM users ORDER BY total_downloads DESC LIMIT 5
        """).fetchall()

        return {
            "total_users": total_users,
            "active_today": active_today,
            "total_downloads": total_downloads,
            "downloads_today": downloads_today,
            "total_bytes": total_bytes,
            "total_videos": total_videos,
            "total_images": total_images,
            "total_audios": total_audios,
            "failed_downloads": failed_downloads,
            "banned_users": banned_users,
            "top_users": [dict(u) for u in top_users],
        }

    return _run_db(_op)


def get_all_user_ids() -> list:
    def _op(conn: sqlite3.Connection):
        return conn.execute(
            "SELECT user_id FROM users WHERE is_banned = 0"
        ).fetchall()

    rows = _run_db(_op)
    return [r["user_id"] for r in rows]


def log_event(event_type: str, event_data: str = None):
    def _op(conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT INTO bot_stats (event_type, event_data) VALUES (?, ?)",
            (event_type, event_data)
        )

    _run_db(_op, write=True)
