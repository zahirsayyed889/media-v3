"""Media downloader and URL normalization utilities."""

import asyncio
import glob
import logging
import os
import re
import shutil
import time
from functools import partial
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse, urlunparse

import yt_dlp

from config import (
    COOKIES_FILE,
    DOWNLOAD_DIR,
    MAX_DOWNLOAD_FOLDER_MB,
    MAX_FILE_AGE_SECONDS,
    QUALITY_OPTIONS,
)

logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_HAS_FFMPEG = bool(shutil.which("ffmpeg"))


# ====================================================
# Storage Management
# ====================================================

def get_folder_size_mb() -> float:
    total_bytes = 0
    for path in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            if os.path.isfile(path):
                total_bytes += os.path.getsize(path)
        except OSError:
            continue
    return total_bytes / (1024 * 1024)


def is_storage_safe() -> bool:
    return get_folder_size_mb() < MAX_DOWNLOAD_FOLDER_MB


def cleanup_files(pattern: str) -> None:
    targets = glob.glob(pattern) if any(ch in pattern for ch in "*?[]") else [pattern]
    for path in targets:
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.isfile(path):
                os.remove(path)
        except OSError:
            continue


def cleanup_job_files(job_prefix: str) -> None:
    cleanup_files(os.path.join(DOWNLOAD_DIR, f"{job_prefix}*"))


def cleanup_old_files(max_age_seconds: int | None = None) -> int:
    max_age = max_age_seconds or MAX_FILE_AGE_SECONDS
    now = time.time()
    removed = 0

    for path in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            if not os.path.exists(path):
                continue
            age = now - os.path.getmtime(path)
            if age > max_age:
                cleanup_files(path)
                removed += 1
        except OSError:
            continue

    if removed:
        logger.info("[Cleanup] Removed %s old file(s) from %s", removed, DOWNLOAD_DIR)
    return removed


def cleanup_all_downloads() -> None:
    cleanup_files(os.path.join(DOWNLOAD_DIR, "*"))


def _trim_storage_until_safe() -> int:
    current = get_folder_size_mb()
    if current <= MAX_DOWNLOAD_FOLDER_MB:
        return 0

    entries: list[tuple[float, str]] = []
    for path in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            if os.path.isfile(path):
                entries.append((os.path.getmtime(path), path))
        except OSError:
            continue

    entries.sort(key=lambda item: item[0])
    target_mb = MAX_DOWNLOAD_FOLDER_MB * 0.75
    removed = 0

    for _, path in entries:
        if get_folder_size_mb() <= target_mb:
            break
        cleanup_files(path)
        removed += 1

    if removed:
        logger.warning(
            "[Cleanup] Storage pressure: removed %s file(s), current %.1f MB",
            removed,
            get_folder_size_mb(),
        )
    return removed


def ensure_storage_space() -> int:
    removed = cleanup_old_files()
    removed += _trim_storage_until_safe()
    return removed


# ====================================================
# URL Detection and Normalization
# ====================================================

_URL_PATTERN = re.compile(
    r"(https?://[^\s<>'\"]+|(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\s<>'\"]*)",
    re.IGNORECASE,
)

_INSTAGRAM_HOSTS = {
    "instagram.com",
    "www.instagram.com",
    "m.instagram.com",
    "instagr.am",
    "www.instagr.am",
}

_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
    "youtu.be",
    "www.youtu.be",
}


def _strip_trailing_punctuation(url: str) -> str:
    while url and url[-1] in ")]}>,.!?;:'\"":
        url = url[:-1]
    return url


def _iter_candidate_urls(text: str):
    for match in _URL_PATTERN.finditer(text):
        raw = _strip_trailing_punctuation(match.group(0).strip())
        if not raw:
            continue
        if raw.startswith(("http://", "https://")):
            yield raw
            continue
        # Only auto-prefix plausible links.
        if "/" in raw and "." in raw.split("/")[0]:
            yield f"https://{raw}"


def _normalize_host(host: str) -> str:
    return host.lower().strip()


def _clean_url(url: str, keep_query: bool = True) -> str:
    parsed = urlparse(url)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    query = parsed.query if keep_query else ""
    return urlunparse((scheme, netloc, parsed.path, "", query, ""))


def _extract_wrapped_target(query_map: dict[str, list[str]]) -> str | None:
    for key in ("u", "url", "q", "target", "dest", "destination"):
        value = query_map.get(key, [""])[0]
        if value:
            return value
    return None


def _resolve_wrapped_url(url: str, max_depth: int = 3) -> str:
    current = url
    for _ in range(max_depth):
        parsed = urlparse(current)
        host = _normalize_host(parsed.netloc)
        query_map = parse_qs(parsed.query)

        wrapped = None
        if host in {"l.instagram.com", "lm.instagram.com"}:
            wrapped = _extract_wrapped_target(query_map)
        elif host.endswith("youtube.com") and parsed.path == "/redirect":
            wrapped = _extract_wrapped_target(query_map)
        elif host.startswith("pinterest.") and parsed.path.startswith("/offsite"):
            wrapped = _extract_wrapped_target(query_map)

        if not wrapped:
            break

        next_url = unquote(wrapped).strip()
        if not next_url:
            break
        if next_url.startswith("//"):
            next_url = f"https:{next_url}"
        elif not next_url.startswith(("http://", "https://")):
            next_url = f"https://{next_url}"

        if next_url == current:
            break
        current = next_url

    return current


def _normalize_youtube_url(url: str) -> str | None:
    url = _resolve_wrapped_url(url)
    parsed = urlparse(url)
    host = _normalize_host(parsed.netloc)
    path = parsed.path.strip("/")

    if host not in _YOUTUBE_HOSTS:
        return None

    video_id = ""

    if host.endswith("youtu.be"):
        video_id = path.split("/")[0] if path else ""
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
    elif path.startswith("shorts/"):
        video_id = path.split("/", 1)[1].split("/")[0]
    elif path.startswith("live/"):
        video_id = path.split("/", 1)[1].split("/")[0]
    elif path.startswith("embed/"):
        video_id = path.split("/", 1)[1].split("/")[0]

    video_id = video_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", video_id):
        return f"https://www.youtube.com/watch?v={video_id}"

    # Allow additional public YouTube URL types (clip/share/embed variations)
    # and let yt-dlp resolve them.
    if path and path.split("/")[0] in {"watch", "clip", "playlist", "embed", "shorts", "live", "@"}:
        return _clean_url(url, keep_query=True)

    if path.startswith("@"):
        return _clean_url(url, keep_query=True)

    return None


def _normalize_instagram_url(url: str) -> str | None:
    url = _resolve_wrapped_url(url)
    parsed = urlparse(url)
    host = _normalize_host(parsed.netloc)

    if host == "l.instagram.com":
        forwarded = parse_qs(parsed.query).get("u", [""])[0]
        if forwarded:
            return _normalize_instagram_url(unquote(forwarded))
        return None

    if host not in _INSTAGRAM_HOSTS:
        return None

    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None

    root = parts[0].lower()
    if root in {"reel", "reels", "p", "tv"} and len(parts) >= 2:
        return f"https://www.instagram.com/{root}/{parts[1]}/"

    # Username-based public media routes:
    # /<username>/reel/<id>/, /<username>/p/<id>/, /<username>/tv/<id>/
    if len(parts) >= 3 and parts[1].lower() in {"reel", "reels", "p", "tv"}:
        return f"https://www.instagram.com/{parts[0]}/{parts[1].lower()}/{parts[2]}/"

    # Public story/highlight links can work without cookies for some accounts.
    if root == "stories" and len(parts) >= 3:
        return f"https://www.instagram.com/stories/{parts[1]}/{parts[2]}/"

    if root == "share" and len(parts) >= 2:
        share_path = "/".join(parts[1:]).strip("/")
        if parsed.query:
            return f"https://www.instagram.com/share/{share_path}/?{parsed.query}"
        return f"https://www.instagram.com/share/{share_path}/"

    # Accept additional public media-ish routes and let yt-dlp decide.
    if root in {"explore", "reels", "reel", "p", "tv"}:
        return _clean_url(url, keep_query=True)

    return None


def _normalize_pinterest_url(url: str) -> str | None:
    url = _resolve_wrapped_url(url)
    parsed = urlparse(url)
    host = _normalize_host(parsed.netloc)
    parts = [p for p in parsed.path.split("/") if p]

    if host == "pin.it":
        if parts:
            return f"https://pin.it/{parts[0]}"
        return None

    if host.startswith("www."):
        host = host[4:]

    if not host.startswith("pinterest."):
        return None

    if len(parts) >= 2 and parts[0].lower() == "pin":
        return f"https://www.pinterest.com/pin/{parts[1]}/"

    # Support broader public Pinterest URLs (videos, idea pins, boards links).
    if parts:
        return _clean_url(url, keep_query=True)

    return None


def detect_platform(text: str) -> str | None:
    for raw in _iter_candidate_urls(text):
        resolved = _resolve_wrapped_url(raw)
        if _normalize_instagram_url(resolved):
            return "instagram"
        if _normalize_youtube_url(resolved):
            return "youtube"
        if _normalize_pinterest_url(resolved):
            return "pinterest"
    return None


def extract_url(text: str) -> str | None:
    for raw in _iter_candidate_urls(text):
        resolved = _resolve_wrapped_url(raw)
        normalized = (
            _normalize_instagram_url(resolved)
            or _normalize_youtube_url(resolved)
            or _normalize_pinterest_url(resolved)
        )
        if normalized:
            return normalized
    return None


# Backward compatibility helpers
def is_instagram_url(text: str) -> bool:
    for raw in _iter_candidate_urls(text):
        if _normalize_instagram_url(_resolve_wrapped_url(raw)):
            return True
    return False


def extract_instagram_url(text: str) -> str | None:
    for raw in _iter_candidate_urls(text):
        normalized = _normalize_instagram_url(_resolve_wrapped_url(raw))
        if normalized:
            return normalized
    return None


# ====================================================
# File Utilities
# ====================================================

def get_file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def format_duration(seconds: int | float | None) -> str:
    if seconds is None or seconds < 0:
        return "Unknown"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# ====================================================
# yt-dlp Options
# ====================================================

def _youtube_clients_for_attempt(attempt_idx: int) -> list[str]:
    variants = [
        ["ios", "android_vr", "mweb", "web"],
        ["android_creator", "tv_embedded", "web"],
        ["web", "android"],
    ]
    return variants[min(attempt_idx, len(variants) - 1)]


def _fallback_format_without_ffmpeg(quality: str, is_audio: bool) -> str:
    """Use single-file formats when ffmpeg is unavailable (no merge required)."""
    if is_audio:
        return "bestaudio[ext=m4a]/bestaudio/best"

    mapping = {
        "best": "best[ext=mp4][height<=1080]/best[height<=1080]/best",
        "720p": "best[ext=mp4][height<=720]/best[height<=720]/best",
        "360p": "best[ext=mp4][height<=360]/best[height<=360]/best",
    }
    return mapping.get(quality, mapping["best"])


def _platform_format_without_ffmpeg(quality: str, is_audio: bool, platform: str) -> str:
    """Return safer no-ffmpeg format strings per platform.

    YouTube uses dedicated fallback logic; other platforms should avoid
    restrictive AV selectors that can drop single-stream Instagram/Pinterest media.
    """
    if platform == "youtube":
        return _fallback_format_without_ffmpeg(quality, is_audio)

    if is_audio:
        return "bestaudio[ext=m4a]/bestaudio/best"

    mapping = {
        "best": "best[ext=mp4]/best",
        "720p": "best[ext=mp4][height<=720]/best[height<=720]/best",
        "360p": "best[ext=mp4][height<=360]/best[height<=360]/best",
    }
    return mapping.get(quality, mapping["best"])


def _youtube_format_candidates(quality: str, is_audio: bool) -> list[str]:
    """Return an ordered fallback chain for YouTube formats."""
    if is_audio:
        if _HAS_FFMPEG:
            return [
                QUALITY_OPTIONS.get("audio", "bestaudio"),
                "bestaudio[ext=m4a]/bestaudio/best",
                "bestaudio/best",
            ]
        return [
            _fallback_format_without_ffmpeg(quality, is_audio=True),
            "bestaudio/best",
        ]

    if not _HAS_FFMPEG:
        return [
            _fallback_format_without_ffmpeg(quality, is_audio=False),
            "best*[vcodec!=none][acodec!=none]/best",
            "best[ext=mp4]/best",
            "best",
        ]

    merged_by_quality = {
        "best": [
            QUALITY_OPTIONS.get("best", "bestvideo+bestaudio/best"),
            "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "bestvideo+bestaudio/best",
            "best[ext=mp4]/best",
            "best",
        ],
        "720p": [
            QUALITY_OPTIONS.get("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]/best"),
            "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "bestvideo+bestaudio/best",
            "best[ext=mp4][height<=720]/best[height<=720]/best",
            "best[ext=mp4]/best",
            "best",
        ],
        "360p": [
            QUALITY_OPTIONS.get("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]/best"),
            "bestvideo[height<=360]+bestaudio/best[height<=360]/best",
            "bestvideo+bestaudio/best",
            "best[ext=mp4][height<=360]/best[height<=360]/best",
            "best[ext=mp4]/best",
            "best",
        ],
    }

    base = merged_by_quality.get(quality, merged_by_quality["best"])
    # Preserve order while removing duplicates.
    return list(dict.fromkeys(base))


def _build_ydl_opts(
    output_template: str,
    format_str: str,
    is_audio: bool,
    platform: str,
    yt_attempt_idx: int = 0,
) -> dict:
    opts: dict = {
        "source_address": "0.0.0.0",
        "sleep_interval_requests": 1.0,
        "sleep_interval": 1,
        "max_sleep_interval": 3,
        "sleep_interval_subtitles": 1,
        "outtmpl": output_template,
        "paths": {"home": DOWNLOAD_DIR, "temp": DOWNLOAD_DIR},
        "restrictfilenames": True,
        "noplaylist": True,
        "format": format_str,
        "socket_timeout": 30,
        "retries": 8,
        "fragment_retries": 8,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "concurrent_fragment_downloads": 1,
        "buffersize": 1024 * 64,
        "http_chunk_size": 1024 * 1024 * 8,
        "noprogress": True,
        "quiet": True,
        "no_warnings": True,
        "writethumbnail": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "writedescription": False,
        "writeinfojson": False,
        "writeannotations": False,
        "ignoreerrors": False,
        "geo_bypass": True,
    }

    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE

    if _HAS_FFMPEG:
        opts["merge_output_format"] = "mp4"
        opts["ffmpeg_location"] = shutil.which("ffmpeg")
        if is_audio:
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

    if platform == "youtube":
        opts["extractor_args"] = {
            "youtube": {
                "player_client": _youtube_clients_for_attempt(yt_attempt_idx),
                "player_skip": ["configs"],
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
            "Referer": "https://www.pinterest.com/",
        }

    return opts


def _is_youtube_verification_error(err_text: str) -> bool:
    text = err_text.lower()
    markers = (
        "sign in to confirm you're not a bot",
        "sign in to confirm you\u2019re not a bot",
        "sign in to confirm you are not a bot",
        "this helps protect our community",
        "please sign in",
        "youtube said",
        "confirm your age",
    )
    return any(marker in text for marker in markers)


def _is_requested_format_unavailable(err_text: str) -> bool:
    text = err_text.lower()
    markers = (
        "requested format is not available",
        "requested format not available",
        "no video formats found",
        "no suitable formats",
    )
    return any(marker in text for marker in markers)


def _classify_error(err_text: str) -> str:
    text = err_text.lower()
    if _is_youtube_verification_error(text):
        return "youtube_verification"
    if _is_requested_format_unavailable(text):
        return "format_unavailable"
    if any(token in text for token in ("private", "login", "authentication", "requires", "sign in")):
        return "private"
    if any(token in text for token in ("not found", "404", "does not exist", "video unavailable")):
        return "not_found"
    return f"Download failed: {err_text}"


# ====================================================
# Multi-platform Download Engine
# ====================================================

VIDEO_EXT = (".mp4", ".mkv", ".webm", ".mov", ".avi")
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
AUDIO_EXT = (".mp3", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".wma")


def _flatten_info(info: dict | None) -> dict | None:
    if not isinstance(info, dict):
        return None
    if info.get("_type") in {"playlist", "multi_video"}:
        entries = info.get("entries") or []
        for entry in entries:
            if entry:
                return entry
    return info


def _download_with_ydl(url: str, ydl_opts: dict):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        info = _flatten_info(info)
        filepath = ydl.prepare_filename(info) if info else None
        return info, filepath


def _resolve_downloaded_file(filepath: str | None, job_prefix: str, is_audio: bool) -> str | None:
    # 1) direct path from yt-dlp.
    if filepath and os.path.isfile(filepath):
        return filepath

    # 2) extension swap after ffmpeg post-processing.
    base = os.path.splitext(filepath)[0] if filepath else None
    if base:
        search_order = AUDIO_EXT if is_audio else (*VIDEO_EXT, *AUDIO_EXT, *IMAGE_EXT)
        for ext in search_order:
            candidate = base + ext
            if os.path.isfile(candidate):
                return candidate

    # 3) fallback to job-prefixed files.
    candidates = sorted(
        [
            file_path
            for file_path in glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_prefix}*"))
            if os.path.isfile(file_path) and not file_path.endswith((".json", ".part", ".ytdl"))
        ],
        key=os.path.getmtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


async def download_media(
    url: str,
    chat_id: int,
    quality: str = "best",
    platform: str = "instagram",
    job_prefix: str | None = None,
) -> dict:
    """Download media via yt-dlp and return normalized metadata/result."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ensure_storage_space()

    if not job_prefix:
        job_prefix = f"{chat_id}_{int(time.time() * 1000)}"

    output_template = os.path.join(DOWNLOAD_DIR, f"{job_prefix}_%(id)s.%(ext)s")
    is_audio = quality == "audio"
    format_str = QUALITY_OPTIONS.get(quality, QUALITY_OPTIONS["best"])
    if not _HAS_FFMPEG:
        format_str = _platform_format_without_ffmpeg(quality, is_audio, platform)
        logger.warning(
            "ffmpeg not found: using non-merge fallback format for quality '%s' on %s",
            quality,
            platform,
        )

    if platform == "youtube":
        format_candidates = _youtube_format_candidates(quality, is_audio)
    else:
        # Try a couple of safe progressive fallbacks for non-YouTube platforms.
        if is_audio:
            format_candidates = [format_str, "bestaudio/best", "best"]
        else:
            format_candidates = [format_str, "best[ext=mp4]/best", "best"]

    result = {
        "success": False,
        "type": "audio" if is_audio else "video",
        "path": None,
        "thumbnail": None,
        "duration": None,
        "width": None,
        "height": None,
        "title": "",
        "error": None,
        "file_size": 0,
        "platform": platform,
        "job_prefix": job_prefix,
    }

    loop = asyncio.get_running_loop()
    client_attempts = 3 if platform == "youtube" else 1
    last_error: str | None = None

    for format_index, attempt_format in enumerate(format_candidates):
        for attempt_idx in range(client_attempts):
            ydl_opts = _build_ydl_opts(
                output_template=output_template,
                format_str=attempt_format,
                is_audio=is_audio,
                platform=platform,
                yt_attempt_idx=attempt_idx,
            )

            try:
                info, filepath = await loop.run_in_executor(
                    None,
                    partial(_download_with_ydl, url, ydl_opts),
                )
            except yt_dlp.utils.DownloadError as exc:
                classification = _classify_error(str(exc))
                last_error = classification

                if platform == "youtube" and classification == "youtube_verification":
                    if attempt_idx < client_attempts - 1:
                        logger.warning(
                            "[yt-dlp] YouTube verification on client attempt %s/%s, trying next client",
                            attempt_idx + 1,
                            client_attempts,
                        )
                        continue
                    # Move to next format candidate.
                    break

                if platform == "youtube" and classification == "format_unavailable":
                    if attempt_idx < client_attempts - 1:
                        logger.warning(
                            "[yt-dlp] Format unavailable for quality=%s using client %s/%s, trying next client",
                            quality,
                            attempt_idx + 1,
                            client_attempts,
                        )
                        continue

                    logger.warning(
                        "[yt-dlp] Format unavailable for quality=%s (candidate %s/%s), trying next fallback format",
                        quality,
                        format_index + 1,
                        len(format_candidates),
                    )
                    break

                if platform == "youtube" and attempt_idx < client_attempts - 1:
                    logger.warning(
                        "[yt-dlp] YouTube error on client attempt %s/%s: %s",
                        attempt_idx + 1,
                        client_attempts,
                        classification,
                    )
                    continue

                result["error"] = classification
                return result
            except Exception as exc:
                last_error = f"Unexpected error: {exc}"
                if platform == "youtube" and attempt_idx < client_attempts - 1:
                    logger.warning(
                        "[yt-dlp] YouTube client attempt %s/%s failed: %s",
                        attempt_idx + 1,
                        client_attempts,
                        exc,
                    )
                    continue

                # Try next format candidate before giving up.
                if platform == "youtube" and format_index < len(format_candidates) - 1:
                    logger.warning(
                        "[yt-dlp] Switching format fallback after client failures (%s/%s)",
                        format_index + 1,
                        len(format_candidates),
                    )
                    break

                result["error"] = last_error
                logger.exception("[download_media] Unexpected failure | platform=%s | url=%s", platform, url)
                return result

            if info is None:
                last_error = "Could not extract content from this link."
                if platform == "youtube" and attempt_idx < client_attempts - 1:
                    continue
                # Move to next format candidate.
                break

            downloaded_file = _resolve_downloaded_file(filepath, job_prefix, is_audio)
            if not downloaded_file or not os.path.isfile(downloaded_file):
                last_error = "Download completed but file not found."
                if platform == "youtube" and attempt_idx < client_attempts - 1:
                    continue
                # Move to next format candidate.
                break

            ext = Path(downloaded_file).suffix.lower()
            if is_audio or ext in AUDIO_EXT:
                media_type = "audio"
            elif ext in IMAGE_EXT:
                media_type = "image"
            else:
                media_type = "video"

            result["type"] = media_type
            result["path"] = downloaded_file
            result["success"] = True
            result["file_size"] = get_file_size(downloaded_file)
            result["duration"] = info.get("duration")
            result["width"] = info.get("width")
            result["height"] = info.get("height")
            result["title"] = (info.get("title") or info.get("description") or "")[:200]

            ensure_storage_space()
            return result

    if platform == "youtube" and last_error == "format_unavailable":
        result["error"] = "Requested quality is unavailable right now. Try Best quality."
    elif last_error:
        result["error"] = last_error
    else:
        result["error"] = "Download failed after all fallback attempts."
    return result


# Backward compatibility
async def download_instagram(url: str, chat_id: int) -> dict:
    return await download_media(url, chat_id, quality="best", platform="instagram")
