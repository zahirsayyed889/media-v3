# ╔══════════════════════════════════════════════════════╗
# ║   🎬  MediaGrab Pro — Configuration                  ║
# ║   Developed by ProofyGamerz                          ║
# ╚══════════════════════════════════════════════════════╝

import os

# ─── Helpers ─────────────────────────────────────────
def _parse_admin_ids(value: str | None) -> list[int]:
    if not value:
        return []
    parts = [p.strip() for p in value.replace(";", ",").replace(" ", ",").split(",")]
    ids = []
    for p in parts:
        if not p:
            continue
        try:
            ids.append(int(p))
        except ValueError:
            pass
    return ids


# ─── Bot Token (set BOT_TOKEN in Railway Variables) ──
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ─── Admin Settings (set ADMIN_IDS in Railway Variables) ─
ADMIN_IDS = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))

# ─── Download Settings ───────────────────────────────
# Use /tmp on Railway — ephemeral but always writable
DOWNLOAD_DIR    = os.getenv("DOWNLOAD_DIR", "/tmp/mediagrab_downloads")
MAX_FILE_SIZE   = 50 * 1024 * 1024   # 50 MB — Telegram bot API limit
MAX_DOWNLOADS_PER_MINUTE  = 5
MAX_CONCURRENT_DOWNLOADS  = 3
MAX_DOWNLOAD_FOLDER_MB    = 400       # keep well under Railway's 512 MB /tmp
AUTO_CLEANUP_SECONDS      = 300
MAX_FILE_AGE_SECONDS      = 90        # delete files after 90 seconds

# ─── Database ────────────────────────────────────────
# Use /tmp on Railway (no Volume needed for basic usage)
DATABASE_FILE = os.getenv("DATABASE_FILE", "/tmp/mediagrab_pro.db")

# ─── Cookies (optional, leave blank if not using) ────
COOKIES_FILE = os.getenv("COOKIES_FILE", "")

# ─── Bot Branding ────────────────────────────────────
BOT_NAME     = "MediaGrab Pro"
BOT_VERSION  = "3.0.0"
BOT_USERNAME = ""

# ─── Credits ─────────────────────────────────────────
DEVELOPER_NAME    = "ProofyGamerz"
DEVELOPER_CHANNEL = "https://www.youtube.com/@ProofyGamerz"
DEVELOPER_TELEGRAM = ""

# ─── Messages ────────────────────────────────────────
SUPPORT_LINK = "https://www.youtube.com/@ProofyGamerz"

# ─── Quality Presets (yt-dlp format strings) ─────────
# These use bestvideo+bestaudio merge (requires ffmpeg)
# with proper MP4/M4A fallbacks for Telegram compatibility
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

# ─── Supported Languages ────────────────────────────
SUPPORTED_LANGUAGES = ["en", "hi"]
DEFAULT_LANGUAGE    = "en"
