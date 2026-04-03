"""
╔══════════════════════════════════════════════════════╗
║   📥  MediaGrab Pro — Multi-Platform Download Engine  ║
║   Instagram • YouTube • Pinterest via yt-dlp          ║
╚══════════════════════════════════════════════════════╝
"""

import os
import re
import glob
import shutil
import asyncio
import logging
from pathlib import Path

import yt_dlp

from config import (
    DOWNLOAD_DIR, MAX_FILE_SIZE,
    MAX_DOWNLOAD_FOLDER_MB, MAX_FILE_AGE_SECONDS,
    QUALITY_OPTIONS, COOKIES_FILE,
)

logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_HAS_FFMPEG = bool(shutil.which("ffmpeg"))


# ═════════════════════════════════════════════════════
#  STORAGE MANAGEMENT
# ═════════════════════════════════════════════════════

def get_folder_size_mb() -> float:
    total = 0
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            total += os.path.getsize(f)
        except OSError:
            pass
    return total / (1024 * 1024)


def is_storage_safe() -> bool:
    return get_folder_size_mb() < MAX_DOWNLOAD_FOLDER_MB


def cleanup_old_files() -> int:
    """Remove files older than MAX_FILE_AGE_SECONDS. Returns count removed."""
    import time as _time
    now = _time.time()
    removed = 0
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            if now - os.path.getmtime(f) > MAX_FILE_AGE_SECONDS:
                os.remove(f)
                removed += 1
        except OSError:
            pass
    if removed:
        logger.info(f"[Cleanup] Removed {removed} old file(s) from {DOWNLOAD_DIR}")
    return removed


def cleanup_all_downloads():
    """Wipe the entire downloads folder."""
    removed = 0
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            os.remove(f)
            removed += 1
        except OSError:
            pass
    logger.info(f"[Cleanup] Wiped {removed} file(s) from {DOWNLOAD_DIR}")


# ═════════════════════════════════════════════════════
#  URL DETECTION — Multi-Platform
# ═════════════════════════════════════════════════════

INSTAGRAM_PATTERN = re.compile(
    r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/"
    r"(reel|p|tv|reels)/[\w\-]+"
)

INSTAGRAM_SHARE_PATTERN = re.compile(
    r"(https?://)?(www\.)?(instagram\.com|instagr\.am)/share/[\w\-]+"
)

YOUTUBE_PATTERN = re.compile(
    r"(https?://)?(www\.|m\.)?"
    r"(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)"
    r"[\w\-]+"
)

PINTEREST_PATTERN = re.compile(
    r"(https?://)?(www\.)?"
    r"(pinterest\.\w+/pin/[\w\-]+|pin\.it/[\w\-]+)"
)


def detect_platform(text: str) -> str | None:
    """Detect which platform a URL belongs to."""
    if INSTAGRAM_PATTERN.search(text) or INSTAGRAM_SHARE_PATTERN.search(text):
        return "instagram"
    if YOUTUBE_PATTERN.search(text):
        return "youtube"
    if PINTEREST_PATTERN.search(text):
        return "pinterest"
    return None


def extract_url(text: str) -> str | None:
    """Extract and clean a media URL from text."""
    for pattern in [INSTAGRAM_PATTERN, INSTAGRAM_SHARE_PATTERN,
                    YOUTUBE_PATTERN, PINTEREST_PATTERN]:
        match = pattern.search(text)
        if match:
            url = match.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            # Keep query params for YouTube (v= is needed)
            if "youtube.com/watch" in url:
                parts = url.split("&")
                return parts[0]
            return url.split("?")[0]
    return None


# Backward compatibility helpers
def is_instagram_url(text: str) -> bool:
    return bool(INSTAGRAM_PATTERN.search(text) or INSTAGRAM_SHARE_PATTERN.search(text))


def extract_instagram_url(text: str) -> str | None:
    match = INSTAGRAM_PATTERN.search(text) or INSTAGRAM_SHARE_PATTERN.search(text)
    if not match:
        return None
    url = match.group(0)
    if not url.startswith("http"):
        url = "https://" + url
    return url.split("?")[0]


# ═════════════════════════════════════════════════════
#  FILE UTILITIES
# ═════════════════════════════════════════════════════

def cleanup_files(pattern: str) -> None:
    for f in glob.glob(pattern):
        try:
            os.remove(f)
        except OSError:
            pass


def get_file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_duration(seconds: int | float | None) -> str:
    if seconds is None or seconds < 0:
        return "Unknown"
    seconds = int(seconds)
    hours   = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs    = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# ═════════════════════════════════════════════════════
#  PLATFORM-SPECIFIC YT-DLP OPTIONS
# ═════════════════════════════════════════════════════

def _build_ydl_opts(output_template: str, format_str: str,
                    is_audio: bool, platform: str) -> dict:
    """Build yt-dlp options tailored per platform."""

    opts = {
        "outtmpl":                      output_template,
        "noplaylist":                   True,
        "format":                       format_str,
        "socket_timeout":               20,
        "retries":                      5,
        "fragment_retries":             5,
        "concurrent_fragment_downloads": 4,
        "buffersize":                   1024 * 64,
        "http_chunk_size":              1024 * 1024 * 10,
        "prefer_insecure":              True,
        "nocheckcertificate":           True,
        "noprogress":                   True,
        "no_warnings":                  True,
        "quiet":                        True,
        "extract_flat":                 False,
        "writethumbnail":               False,
        "writesubtitles":               False,
        "writeautomaticsub":            False,
        "writedescription":             False,
        "writeinfojson":                False,
        "writeannotations":             False,
        # Ignore errors on individual fragments so partial downloads don't crash
        "ignoreerrors":                 False,
    }

    # ── Cookies (optional) ──────────────────────────
    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE

    # ── FFmpeg post-processors ──────────────────────
    if is_audio and _HAS_FFMPEG:
        opts["postprocessors"] = [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "mp3",
            "preferredquality": "192",
        }]
    elif not is_audio and _HAS_FFMPEG:
        opts["merge_output_format"] = "mp4"
        opts["postprocessors"] = [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
        ]

    # ── Platform-specific tweaks ────────────────────

    if platform == "youtube":
        # Use the iOS client — treated as a legitimate mobile app by YouTube,
        # bypasses bot-detection checks on datacenter IPs (Railway etc.)
        opts["socket_timeout"] = 30
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["ios", "mweb", "web"],
            }
        }
        opts["http_headers"] = {
            "User-Agent": (
                "com.google.ios.youtube/19.29.1 "
                "(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    elif platform == "instagram":
        # Standard browser UA — avoids Instagram's bot headers check
        opts["http_headers"] = {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.5 Mobile/15E148 Safari/604.1"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    elif platform == "pinterest":
        opts["http_headers"] = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    return opts


# ═════════════════════════════════════════════════════
#  MULTI-PLATFORM DOWNLOAD ENGINE
# ═════════════════════════════════════════════════════

VIDEO_EXT = (".mp4", ".mkv", ".webm", ".mov", ".avi")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
AUDIO_EXT = (".mp3", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".wma")


async def download_media(url: str, chat_id: int,
                         quality: str = "best",
                         platform: str = "instagram") -> dict:
    """
    Download media from Instagram / YouTube / Pinterest via yt-dlp.

    Args:
        url:      The media URL
        chat_id:  Telegram chat ID (used for unique filenames)
        quality:  One of 'best', '720p', '360p', 'audio'
        platform: One of 'instagram', 'youtube', 'pinterest'

    Returns a dict with keys:
        success, type, path, thumbnail, duration, width, height,
        title, error, file_size, platform
    """
    # Ensure download dir exists (important after Railway container restart)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    # Proactive cleanup before every download to keep /tmp healthy
    cleanup_old_files()

    output_template = os.path.join(DOWNLOAD_DIR, f"{chat_id}_%(id)s.%(ext)s")
    is_audio   = (quality == "audio")
    format_str = QUALITY_OPTIONS.get(quality, "best")

    ydl_opts = _build_ydl_opts(output_template, format_str, is_audio, platform)

    result = {
        "success":  False,
        "type":     "audio" if is_audio else "video",
        "path":     None,
        "thumbnail": None,
        "duration": None,
        "width":    None,
        "height":   None,
        "title":    "",
        "error":    None,
        "file_size": 0,
        "platform": platform,
    }

    try:
        loop = asyncio.get_event_loop()

        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info     = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info) if info else None
                return info, filepath

        info, filepath = await loop.run_in_executor(None, _download)

        if info is None:
            result["error"] = "Could not extract content from this link."
            return result

        # ── Locate the downloaded file ──────────────
        downloaded_file = None

        # Audio: extension may change after FFmpeg post-processing
        if is_audio and _HAS_FFMPEG:
            base = (
                os.path.splitext(filepath)[0]
                if filepath
                else os.path.join(DOWNLOAD_DIR, f"{chat_id}_{info.get('id', 'unknown')}")
            )
            for ext in AUDIO_EXT:
                candidate = base + ext
                if os.path.isfile(candidate):
                    downloaded_file = candidate
                    break

        if not downloaded_file:
            if filepath and os.path.isfile(filepath):
                downloaded_file = filepath
            else:
                base = (
                    os.path.splitext(filepath)[0]
                    if filepath
                    else os.path.join(DOWNLOAD_DIR, f"{chat_id}_{info.get('id', 'unknown')}")
                )
                for ext in (*AUDIO_EXT, *VIDEO_EXT, *IMAGE_EXT):
                    candidate = base + ext
                    if os.path.isfile(candidate):
                        downloaded_file = candidate
                        break

        # Last resort: glob newest file for this chat_id
        if not downloaded_file:
            candidates = sorted(
                [f for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{chat_id}_*"))
                 if not f.endswith((".json", ".part"))],
                key=os.path.getmtime,
                reverse=True,
            )
            if candidates:
                downloaded_file = candidates[0]

        if not downloaded_file or not os.path.isfile(downloaded_file):
            result["error"] = "Download completed but file not found."
            return result

        # ── Determine media type ─────────────────────
        ext_lower = Path(downloaded_file).suffix.lower()
        if is_audio or ext_lower in AUDIO_EXT:
            result["type"] = "audio"
        elif ext_lower in IMAGE_EXT:
            result["type"] = "image"
        else:
            result["type"] = "video"

        result["path"]      = downloaded_file
        result["success"]   = True
        result["file_size"] = get_file_size(downloaded_file)
        result["duration"]  = info.get("duration")
        result["width"]     = info.get("width")
        result["height"]    = info.get("height")
        result["title"]     = (
            info.get("title", "") or info.get("description", "") or ""
        )[:200]

        return result

    except yt_dlp.utils.DownloadError as e:
        err = str(e).lower()
        if any(k in err for k in ("private", "login", "authentication",
                                   "requires", "sign in", "confirm")):
            result["error"] = "private"
        elif "not found" in err or "404" in err or "does not exist" in err:
            result["error"] = "not_found"
        else:
            logger.warning(f"[yt-dlp DownloadError] platform={platform} | {e}")
            result["error"] = f"Download failed: {e}"
        return result

    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        logger.exception(f"[download_media] Unexpected error | platform={platform} | url={url}")
        return result


# Backward compatibility
async def download_instagram(url: str, chat_id: int) -> dict:
    return await download_media(url, chat_id, quality="best", platform="instagram")
