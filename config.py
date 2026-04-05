# ╔══════════════════════════════════════════════════════╗
# ║   MediaGrab Pro - Configuration                      ║
# ║   Developed by ProofyGamerz                          ║
# ╚══════════════════════════════════════════════════════╝

import os
import re


def _parse_int_env(name: str, default: int, min_value: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= min_value else default


def _parse_float_env(name: str, default: float, min_value: float = 0.0) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value >= min_value else default


def _parse_admin_ids(value: str | None) -> tuple[list[int], list[str]]:
    if not value:
        return [], []
    parts = [p.strip() for p in value.replace(";", ",").replace(" ", ",").split(",")]
    ids: list[int] = []
    invalid: list[str] = []
    for part in parts:
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            invalid.append(part)
    return ids, invalid


# -- Bot Token --
# For local testing (without env vars), paste your token below.
# Keep this empty in production and use BOT_TOKEN env variable.
LOCAL_BOT_TOKEN = ""
BOT_TOKEN = (LOCAL_BOT_TOKEN or os.getenv("BOT_TOKEN", "")).strip()

# -- Admin Settings (set ADMIN_IDS in Railway Variables) --
ADMIN_IDS, INVALID_ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

# -- Download Settings --
# Use /tmp on Railway - ephemeral but always writable.
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "/tmp/mediagrab_downloads")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB Telegram Bot API limit
MAX_DOWNLOADS_PER_MINUTE = _parse_int_env("MAX_DOWNLOADS_PER_MINUTE", 3, min_value=1)
MAX_CONCURRENT_DOWNLOADS = _parse_int_env("MAX_CONCURRENT_DOWNLOADS", 3, min_value=1)
MAX_DOWNLOAD_FOLDER_MB = _parse_int_env("MAX_DOWNLOAD_FOLDER_MB", 400, min_value=128)
AUTO_CLEANUP_SECONDS = _parse_int_env("AUTO_CLEANUP_SECONDS", 120, min_value=30)
MAX_FILE_AGE_SECONDS = _parse_int_env("MAX_FILE_AGE_SECONDS", 180, min_value=30)

# -- SQLite Reliability --
SQLITE_BUSY_TIMEOUT_MS = _parse_int_env("SQLITE_BUSY_TIMEOUT_MS", 15000, min_value=1000)
SQLITE_RETRY_ATTEMPTS = _parse_int_env("SQLITE_RETRY_ATTEMPTS", 6, min_value=1)
SQLITE_RETRY_BACKOFF_MS = _parse_int_env("SQLITE_RETRY_BACKOFF_MS", 150, min_value=10)

# -- Telegram API Reliability --
TELEGRAM_API_RETRIES = _parse_int_env("TELEGRAM_API_RETRIES", 3, min_value=0)
TELEGRAM_API_RETRY_DELAY_SECONDS = _parse_float_env(
    "TELEGRAM_API_RETRY_DELAY_SECONDS", 1.5, min_value=0.1
)

# -- Database --
# Use /tmp on Railway (or set to volume path like /data/...)
DATABASE_FILE = os.getenv("DATABASE_FILE", "/tmp/mediagrab_pro.db")

# -- Cookies (optional, leave blank if not using) --
COOKIES_FILE = os.getenv("COOKIES_FILE", "")

# -- Bot Branding --
BOT_NAME = "MediaGrab Pro"
BOT_VERSION = "3.0.0"
BOT_USERNAME = ""

# -- Credits --
DEVELOPER_NAME = "ProofyGamerz"
DEVELOPER_CHANNEL = "https://www.youtube.com/@ProofyGamerz"
DEVELOPER_TELEGRAM = ""

# -- Messages --
SUPPORT_LINK = "https://www.youtube.com/@ProofyGamerz"

# -- Quality Presets (yt-dlp format strings) --
# These intentionally use bestvideo+bestaudio merge (needs ffmpeg).
QUALITY_OPTIONS = {
    "best": (
        "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]"
        "/bestvideo[height<=1080]+bestaudio"
        "/best[ext=mp4]/best"
    ),
    "720p": (
        "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]"
        "/bestvideo[height<=720]+bestaudio"
        "/best[ext=mp4][height<=720]/best[height<=720]/best"
    ),
    "360p": (
        "bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]"
        "/bestvideo[height<=360]+bestaudio"
        "/best[height<=360]/best"
    ),
    "audio": "bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best",
}

# -- Supported Languages --
SUPPORTED_LANGUAGES = ["en", "hi"]
DEFAULT_LANGUAGE = "en"


def validate_environment() -> list[str]:
    """Return startup validation errors. Empty list means config is valid."""
    errors: list[str] = []

    if not BOT_TOKEN:
        errors.append(
            "BOT_TOKEN is missing. Set LOCAL_BOT_TOKEN in config.py for local testing "
            "or set BOT_TOKEN in Railway Variables."
        )
    elif not re.match(r"^\d{6,}:[A-Za-z0-9_-]{20,}$", BOT_TOKEN):
        errors.append("BOT_TOKEN format looks invalid. Expected '<digits>:<token>'.")

    if INVALID_ADMIN_IDS:
        errors.append(
            "ADMIN_IDS contains invalid values: "
            + ", ".join(INVALID_ADMIN_IDS)
            + ". Use comma-separated numeric Telegram user IDs."
        )

    if MAX_CONCURRENT_DOWNLOADS < 1:
        errors.append("MAX_CONCURRENT_DOWNLOADS must be at least 1.")
    if MAX_DOWNLOADS_PER_MINUTE < 1:
        errors.append("MAX_DOWNLOADS_PER_MINUTE must be at least 1.")
    if AUTO_CLEANUP_SECONDS < 30:
        errors.append("AUTO_CLEANUP_SECONDS must be >= 30.")
    if MAX_FILE_AGE_SECONDS < 30:
        errors.append("MAX_FILE_AGE_SECONDS must be >= 30.")

    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        test_path = os.path.join(DOWNLOAD_DIR, ".write_test")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
    except Exception as exc:  # pragma: no cover - deployment dependent
        errors.append(f"DOWNLOAD_DIR is not writable: {DOWNLOAD_DIR} ({exc})")

    db_dir = os.path.dirname(os.path.abspath(DATABASE_FILE))
    try:
        os.makedirs(db_dir, exist_ok=True)
        test_path = os.path.join(db_dir, ".db_write_test")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
    except Exception as exc:  # pragma: no cover - deployment dependent
        errors.append(f"DATABASE_FILE directory is not writable: {db_dir} ({exc})")

    return errors
