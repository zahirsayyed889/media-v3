"""
╔══════════════════════════════════════════════════════╗
║   💾  MediaGrab Pro — Database Layer                  ║
║   SQLite storage for users, downloads & analytics     ║
╚══════════════════════════════════════════════════════╝
"""

import os
import sqlite3
import time
from config import DATABASE_FILE


def get_db():
    # Ensure parent directory exists (critical for /tmp/... paths on Railway)
    db_dir = os.path.dirname(os.path.abspath(DATABASE_FILE))
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")   # safer than OFF, faster than FULL
    return conn


def _safe_add_column(cursor, table, column, col_type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass


def init_database():
    conn = get_db()
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

    # Migration: add new columns to existing deployments without data loss
    _safe_add_column(cursor, "users",     "preferred_lang",    "TEXT DEFAULT 'en'")
    _safe_add_column(cursor, "users",     "preferred_quality", "TEXT DEFAULT 'best'")
    _safe_add_column(cursor, "downloads", "platform",          "TEXT DEFAULT 'instagram'")

    conn.commit()
    conn.close()


# ═════════════════════════════════════════════════════
#  USER OPERATIONS
# ═════════════════════════════════════════════════════

def register_user(user):
    conn = get_db()
    conn.execute("""
        INSERT INTO users (user_id, username, first_name, last_name, language_code, last_active)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            username    = excluded.username,
            first_name  = excluded.first_name,
            last_name   = excluded.last_name,
            last_active = datetime('now')
    """, (
        user.id,
        user.username  or "",
        user.first_name or "",
        user.last_name  or "",
        user.language_code or "en",
    ))
    conn.commit()
    conn.close()


def is_user_banned(user_id: int) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return bool(row and row["is_banned"])


def ban_user(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def unban_user(user_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_user_lang(user_id: int) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT preferred_lang FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["preferred_lang"] if (row and row["preferred_lang"]) else "en"


def set_user_lang(user_id: int, lang: str):
    conn = get_db()
    conn.execute(
        "UPDATE users SET preferred_lang = ? WHERE user_id = ?", (lang, user_id)
    )
    conn.commit()
    conn.close()


def get_user_quality(user_id: int) -> str:
    conn = get_db()
    row = conn.execute(
        "SELECT preferred_quality FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row["preferred_quality"] if (row and row["preferred_quality"]) else "best"


def set_user_quality(user_id: int, quality: str):
    conn = get_db()
    conn.execute(
        "UPDATE users SET preferred_quality = ? WHERE user_id = ?", (quality, user_id)
    )
    conn.commit()
    conn.close()


def get_user_stats(user_id: int) -> dict:
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()

    if not user:
        conn.close()
        return {
            "total_downloads": 0, "total_bytes": 0,
            "videos": 0, "images": 0, "audios": 0,
            "joined_at": "Unknown", "rank": 0,
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

    conn.close()
    return {
        "total_downloads": user["total_downloads"],
        "total_bytes":     user["total_bytes"],
        "videos":  videos,
        "images":  images,
        "audios":  audios,
        "joined_at": user["joined_at"],
        "rank":    rank,
    }


def get_user_history(user_id: int, limit: int = 10) -> list:
    conn = get_db()
    rows = conn.execute("""
        SELECT url, content_type, platform, file_size, duration, status, downloaded_at
        FROM downloads
        WHERE user_id = ? AND status = 'success'
        ORDER BY downloaded_at DESC LIMIT ?
    """, (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ═════════════════════════════════════════════════════
#  DOWNLOAD OPERATIONS
# ═════════════════════════════════════════════════════

def record_download(user_id: int, url: str, content_type: str,
                    file_size: int, duration: int = None,
                    status: str = "success", error_message: str = None,
                    platform: str = "instagram"):
    conn = get_db()
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
                total_bytes     = total_bytes + ?
            WHERE user_id = ?
        """, (file_size, user_id))

    conn.commit()
    conn.close()


def get_downloads_last_minute(user_id: int) -> int:
    conn = get_db()
    count = conn.execute("""
        SELECT COUNT(*) as c FROM downloads
        WHERE user_id = ? AND downloaded_at > datetime('now', '-1 minute')
    """, (user_id,)).fetchone()["c"]
    conn.close()
    return count


# ═════════════════════════════════════════════════════
#  GLOBAL STATS (Admin)
# ═════════════════════════════════════════════════════

def get_global_stats() -> dict:
    conn = get_db()

    def _count(sql, *args):
        return conn.execute(sql, args).fetchone()[0]

    total_users      = _count("SELECT COUNT(*) FROM users")
    active_today     = _count(
        "SELECT COUNT(*) FROM users WHERE last_active > datetime('now', '-1 day')")
    total_downloads  = _count(
        "SELECT COUNT(*) FROM downloads WHERE status = 'success'")
    total_bytes      = conn.execute(
        "SELECT COALESCE(SUM(file_size), 0) FROM downloads WHERE status = 'success'"
    ).fetchone()[0]
    total_videos     = _count(
        "SELECT COUNT(*) FROM downloads WHERE content_type = 'video' AND status = 'success'")
    total_images     = _count(
        "SELECT COUNT(*) FROM downloads WHERE content_type = 'image' AND status = 'success'")
    total_audios     = _count(
        "SELECT COUNT(*) FROM downloads WHERE content_type = 'audio' AND status = 'success'")
    failed_downloads = _count(
        "SELECT COUNT(*) FROM downloads WHERE status = 'failed'")
    banned_users     = _count(
        "SELECT COUNT(*) FROM users WHERE is_banned = 1")
    downloads_today  = _count(
        "SELECT COUNT(*) FROM downloads "
        "WHERE status = 'success' AND downloaded_at > datetime('now', '-1 day')")

    top_users = conn.execute("""
        SELECT user_id, first_name, username, total_downloads
        FROM users ORDER BY total_downloads DESC LIMIT 5
    """).fetchall()

    conn.close()
    return {
        "total_users":      total_users,
        "active_today":     active_today,
        "total_downloads":  total_downloads,
        "downloads_today":  downloads_today,
        "total_bytes":      total_bytes,
        "total_videos":     total_videos,
        "total_images":     total_images,
        "total_audios":     total_audios,
        "failed_downloads": failed_downloads,
        "banned_users":     banned_users,
        "top_users":        [dict(u) for u in top_users],
    }


def get_all_user_ids() -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT user_id FROM users WHERE is_banned = 0"
    ).fetchall()
    conn.close()
    return [r["user_id"] for r in rows]


def log_event(event_type: str, event_data: str = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO bot_stats (event_type, event_data) VALUES (?, ?)",
        (event_type, event_data)
    )
    conn.commit()
    conn.close()
