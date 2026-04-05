"""
╔══════════════════════════════════════════════════════╗
║                                                          ║
║    🎬   M E D I A G R A B   P R O   v3.0.0              ║
║                                                          ║
║    Premium Multi-Platform Downloader for Telegram        ║
║    ────────────────────────────────────────────────       ║
║    Instagram • YouTube • Pinterest • Audio (MP3)         ║
║                                                          ║
║    Developed by ProofyGamerz                             ║
║    https://www.youtube.com/@ProofyGamerz                 ║
║                                                          ║
╚══════════════════════════════════════════════════════╝
"""

import os
import asyncio
import logging
import time
import uuid
import shutil
from collections import deque

from telegram import Update, constants, BotCommand
from telegram.error import BadRequest, NetworkError, RetryAfter, TimedOut
from telegram.request import HTTPXRequest
from telegram.ext import (
    AIORateLimiter,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN, BOT_NAME, BOT_VERSION,
    DOWNLOAD_DIR, MAX_FILE_SIZE,
    ADMIN_IDS, MAX_DOWNLOADS_PER_MINUTE,
    MAX_CONCURRENT_DOWNLOADS,
    AUTO_CLEANUP_SECONDS,
    TELEGRAM_API_RETRIES,
    TELEGRAM_API_RETRY_DELAY_SECONDS,
    validate_environment,
    DEVELOPER_NAME, DEVELOPER_CHANNEL,
)
from database import (
    init_database, register_user, is_user_banned,
    get_user_stats, get_user_history, record_download,
    get_global_stats,
    get_all_user_ids, ban_user, unban_user, log_event,
    get_user_lang, set_user_lang, get_user_quality, set_user_quality,
)
from downloader import (
    detect_platform, extract_url,
    download_media, cleanup_job_files,
    ensure_storage_space, get_folder_size_mb,
)
from ui import (
    main_menu_keyboard, back_keyboard, help_keyboard,
    settings_keyboard, quality_settings_keyboard, language_keyboard,
    quality_picker_keyboard, admin_keyboard, after_download_keyboard,
    credit_keyboard,
    welcome_message, help_message, about_message,
    stats_message, history_message, settings_message,
    help_reels_message, help_youtube_message,
    help_pinterest_message, help_videos_message,
    quality_picker_message,
    downloading_message, uploading_message,
    download_complete_caption,
    error_invalid_url, error_private_content,
    error_not_found, error_too_large,
    error_rate_limit, error_banned,
    error_download_failed, error_upload_failed,
    admin_panel_message, admin_stats_message,
)
from lang import LANG_NAMES, QUALITY_NAMES

# ── Logging ──────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s │ %(name)s │ %(levelname)s │ %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ── Concurrent download guard ─────────────────────────
# Prevents the same user from triggering two downloads at the same time,
# which would waste Railway CPU/disk and could cause file mix-ups.
_active_downloads: set[int] = set()
_active_downloads_lock = asyncio.Lock()
_global_download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)

# In-memory token bucket for race-safe per-user rate limiting.
_user_rate_windows: dict[int, deque[float]] = {}
_rate_limit_lock = asyncio.Lock()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _make_job_prefix(chat_id: int, user_id: int) -> str:
    return f"{chat_id}_{user_id}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


async def _reserve_rate_slot(user_id: int) -> bool:
    now = time.monotonic()
    async with _rate_limit_lock:
        bucket = _user_rate_windows.setdefault(user_id, deque())
        while bucket and now - bucket[0] >= 60.0:
            bucket.popleft()
        if len(bucket) >= MAX_DOWNLOADS_PER_MINUTE:
            return False
        bucket.append(now)
        return True


async def _telegram_with_retry(call_factory, action: str):
    retries = max(0, TELEGRAM_API_RETRIES)
    base_delay = max(0.5, TELEGRAM_API_RETRY_DELAY_SECONDS)

    for attempt in range(retries + 1):
        try:
            return await call_factory()
        except BadRequest as exc:
            # Benign case while updating progress text.
            if "message is not modified" in str(exc).lower():
                return None
            raise
        except RetryAfter as exc:
            wait_seconds = max(float(getattr(exc, "retry_after", 1)), 1.0)
            if attempt >= retries:
                raise
            logger.warning("Telegram retry-after during %s, sleeping %.1fs", action, wait_seconds)
            await asyncio.sleep(wait_seconds)
        except (TimedOut, NetworkError) as exc:
            if attempt >= retries:
                raise
            wait_seconds = base_delay * (attempt + 1)
            logger.warning(
                "Telegram network issue during %s (attempt %s/%s): %s",
                action,
                attempt + 1,
                retries + 1,
                exc,
            )
            await asyncio.sleep(wait_seconds)


async def _handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Unhandled exception in update handler", exc_info=context.error)


# ═════════════════════════════════════════════════════
#  COMMAND HANDLERS
# ═════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    log_event("start", str(user.id))
    lang = get_user_lang(user.id)

    await update.message.reply_text(
        welcome_message(user.first_name or "User", lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=main_menu_keyboard(lang),
        disable_web_page_preview=True,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    lang = get_user_lang(user.id)
    await update.message.reply_text(
        help_message(lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=help_keyboard(lang),
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    lang = get_user_lang(user.id)
    await update.message.reply_text(
        about_message(lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=credit_keyboard(lang),
        disable_web_page_preview=True,
    )


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    lang = get_user_lang(user.id)
    user_data = get_user_stats(user.id)
    await update.message.reply_text(
        stats_message(user_data, user.first_name or "User", lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=back_keyboard(lang),
    )


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    lang = get_user_lang(user.id)
    history = get_user_history(user.id)
    await update.message.reply_text(
        history_message(history, lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=back_keyboard(lang),
    )


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user)
    lang    = get_user_lang(user.id)
    quality = get_user_quality(user.id)
    await update.message.reply_text(
        settings_message(lang, quality, lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=settings_keyboard(lang),
    )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            "🚫  Not authorized.", parse_mode=constants.ParseMode.HTML
        )
        return
    await update.message.reply_text(
        admin_panel_message(),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=admin_keyboard(),
    )


async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "📢  <b>Broadcast</b>\n\nUsage: <code>/broadcast Your message here</code>",
            parse_mode=constants.ParseMode.HTML,
        )
        return

    user_ids = get_all_user_ids()
    success = failed = 0
    status = await _telegram_with_retry(
        lambda: update.message.reply_text(
            f"📢  Broadcasting to <b>{len(user_ids)}</b> users...",
            parse_mode=constants.ParseMode.HTML,
        ),
        "send broadcast status",
    )

    broadcast_text = (
        f"{'═' * 32}\n   📢  <b>Announcement</b>\n{'═' * 32}\n\n"
        f"{text}\n\n{'─' * 32}\n<i>⚡ {BOT_NAME} by {DEVELOPER_NAME}</i>"
    )

    for uid in user_ids:
        try:
            await _telegram_with_retry(
                lambda uid=uid: context.bot.send_message(
                    chat_id=uid,
                    text=broadcast_text,
                    parse_mode=constants.ParseMode.HTML,
                    disable_web_page_preview=True,
                ),
                "broadcast user message",
            )
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    if status is not None:
        await _telegram_with_retry(
            lambda: status.edit_text(
                f"📢  <b>Broadcast Complete</b>\n\n"
                f"  ✅  Sent: <b>{success}</b>\n  ❌  Failed: <b>{failed}</b>\n"
                f"  📊  Total: <b>{len(user_ids)}</b>",
                parse_mode=constants.ParseMode.HTML,
            ),
            "finalize broadcast status",
        )
    log_event("broadcast", f"sent={success}, failed={failed}")


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: <code>/ban &lt;user_id&gt;</code>",
            parse_mode=constants.ParseMode.HTML,
        )
        return
    try:
        target_id = int(context.args[0])
        ban_user(target_id)
        await update.message.reply_text(
            f"🚫  User <code>{target_id}</code> <b>banned</b>.",
            parse_mode=constants.ParseMode.HTML,
        )
        log_event("ban", str(target_id))
    except ValueError:
        await update.message.reply_text("❌  Invalid user ID.")


async def cmd_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "Usage: <code>/unban &lt;user_id&gt;</code>",
            parse_mode=constants.ParseMode.HTML,
        )
        return
    try:
        target_id = int(context.args[0])
        unban_user(target_id)
        await update.message.reply_text(
            f"✅  User <code>{target_id}</code> <b>unbanned</b>.",
            parse_mode=constants.ParseMode.HTML,
        )
        log_event("unban", str(target_id))
    except ValueError:
        await update.message.reply_text("❌  Invalid user ID.")


async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"🆔  Your Telegram ID: <code>{user.id}</code>",
        parse_mode=constants.ParseMode.HTML,
    )


# ═════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ═════════════════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    data = query.data
    lang = get_user_lang(user.id)

    try:
        # ── Navigation ──────────────────────────────
        if data == "start":
            await query.edit_message_text(
                welcome_message(user.first_name or "User", lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=main_menu_keyboard(lang),
                disable_web_page_preview=True,
            )

        elif data == "help":
            await query.edit_message_text(
                help_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=help_keyboard(lang),
            )

        elif data == "help_reels":
            await query.edit_message_text(
                help_reels_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "help_yt":
            await query.edit_message_text(
                help_youtube_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "help_pin":
            await query.edit_message_text(
                help_pinterest_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "help_vid":
            await query.edit_message_text(
                help_videos_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "stats":
            user_data = get_user_stats(user.id)
            await query.edit_message_text(
                stats_message(user_data, user.first_name or "User", lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "history":
            history = get_user_history(user.id)
            await query.edit_message_text(
                history_message(history, lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=back_keyboard(lang),
            )

        elif data == "about":
            await query.edit_message_text(
                about_message(lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=credit_keyboard(lang),
                disable_web_page_preview=True,
            )

        # ── Settings ────────────────────────────────
        elif data == "settings":
            quality = get_user_quality(user.id)
            await query.edit_message_text(
                settings_message(lang, quality, lang),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=settings_keyboard(lang),
            )

        elif data == "setting_quality":
            quality = get_user_quality(user.id)
            qname   = QUALITY_NAMES.get(quality, quality)
            await query.edit_message_text(
                f"{'═' * 32}\n   🎬  <b>Default Quality</b>\n{'═' * 32}\n\n"
                f"  Current: <b>{qname}</b>\n\n"
                f"  Choose your default download quality:",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=quality_settings_keyboard(lang),
            )

        elif data == "setting_lang":
            lname = LANG_NAMES.get(lang, lang)
            await query.edit_message_text(
                f"{'═' * 32}\n   🌐  <b>Language / भाषा</b>\n{'═' * 32}\n\n"
                f"  Current: <b>{lname}</b>\n\n"
                f"  Choose your language:",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=language_keyboard(lang),
            )

        # ── Set quality preference ──────────────────
        elif data.startswith("setq_"):
            q = data.replace("setq_", "")
            set_user_quality(user.id, q)
            qname = QUALITY_NAMES.get(q, q)
            await query.edit_message_text(
                f"{'═' * 32}\n   ✅  <b>Quality Updated</b>\n{'═' * 32}\n\n"
                f"  Default quality set to <b>{qname}</b>\n\n"
                f"  All future downloads will use this quality.\n"
                f"  You can still pick a different quality per download.",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=settings_keyboard(lang),
            )

        # ── Set language preference ─────────────────
        elif data.startswith("setlang_"):
            new_lang = data.replace("setlang_", "")
            set_user_lang(user.id, new_lang)
            lname = LANG_NAMES.get(new_lang, new_lang)
            lang  = new_lang   # use new lang immediately in this response
            await query.edit_message_text(
                f"{'═' * 32}\n   ✅  <b>Language Updated</b>\n{'═' * 32}\n\n"
                f"  Language set to <b>{lname}</b>\n\n"
                f"  All messages will now be in {lname}.",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=settings_keyboard(lang),
            )

        # ── Quality picker (download flow) ──────────
        elif data.startswith("dl_"):
            quality  = data.replace("dl_", "")
            pending = context.user_data.get("pending_download", {})

            url = pending.get("url") if isinstance(pending, dict) else None
            platform = pending.get("platform", "instagram") if isinstance(pending, dict) else "instagram"
            created_at = pending.get("created_at", 0) if isinstance(pending, dict) else 0

            if not url or not created_at or time.time() - created_at > 600:
                await query.edit_message_text(
                    "⚠️  Link expired. Please send the link again.",
                    parse_mode=constants.ParseMode.HTML,
                )
                context.user_data.pop("pending_download", None)
                return

            # Clear pending
            context.user_data.pop("pending_download", None)

            await _perform_download(
                query.message, user, url, platform, quality, lang, context
            )

        # ── Admin callbacks ─────────────────────────
        elif data == "admin_stats" and is_admin(user.id):
            stats = get_global_stats()
            await query.edit_message_text(
                admin_stats_message(stats),
                parse_mode=constants.ParseMode.HTML,
                reply_markup=admin_keyboard(),
            )

        elif data == "admin_users" and is_admin(user.id):
            stats = get_global_stats()
            await query.edit_message_text(
                f"{'═' * 32}\n   👥  <b>User Management</b>\n{'═' * 32}\n\n"
                f"  Total:  <b>{stats['total_users']}</b>\n"
                f"  Active: <b>{stats['active_today']}</b>\n"
                f"  Banned: <b>{stats['banned_users']}</b>\n\n"
                f"  <code>/ban &lt;user_id&gt;</code>\n"
                f"  <code>/unban &lt;user_id&gt;</code>",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=admin_keyboard(),
            )

        elif data == "admin_broadcast" and is_admin(user.id):
            await query.edit_message_text(
                f"{'═' * 32}\n   📢  <b>Broadcast</b>\n{'═' * 32}\n\n"
                f"  <code>/broadcast Your message here</code>\n\n  ⚠️  Use responsibly!",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=admin_keyboard(),
            )

        elif data == "admin_system" and is_admin(user.id):
            import platform as plat
            import sys
            folder_mb = get_folder_size_mb()
            await query.edit_message_text(
                f"{'═' * 32}\n   🔧  <b>System Info</b>\n{'═' * 32}\n\n"
                f"  🤖  Bot:    <b>{BOT_NAME} v{BOT_VERSION}</b>\n"
                f"  🐍  Python: <b>{sys.version.split()[0]}</b>\n"
                f"  💻  OS:     <b>{plat.system()} {plat.release()}</b>\n"
                f"  📂  Dir:    <code>{DOWNLOAD_DIR}</code>\n"
                f"  💾  Disk:   <b>{folder_mb:.1f} MB used</b>\n\n"
                f"  <i>⚡ All systems operational</i>",
                parse_mode=constants.ParseMode.HTML,
                reply_markup=admin_keyboard(),
            )

    except Exception as e:
        logger.warning(f"Callback error [{data}]: {e}")


# ═════════════════════════════════════════════════════
#  MESSAGE HANDLER (Media links)
# ═════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    user = update.effective_user
    register_user(user)

    lang = get_user_lang(user.id)

    if is_user_banned(user.id):
        await update.message.reply_text(
            error_banned(lang), parse_mode=constants.ParseMode.HTML
        )
        return

    # Detect platform
    platform = detect_platform(text)
    if not platform:
        await update.message.reply_text(
            error_invalid_url(lang),
            parse_mode=constants.ParseMode.HTML,
            reply_markup=back_keyboard(lang),
        )
        return

    # Race-safe in-memory rate limiter to avoid concurrent bypass.
    if not await _reserve_rate_slot(user.id):
        await update.message.reply_text(
            error_rate_limit(lang), parse_mode=constants.ParseMode.HTML
        )
        return

    url = extract_url(text)
    if not url:
        await update.message.reply_text(
            error_invalid_url(lang), parse_mode=constants.ParseMode.HTML
        )
        return

    # Store pending URL and show quality picker.
    context.user_data["pending_download"] = {
        "url": url,
        "platform": platform,
        "created_at": time.time(),
    }

    await update.message.reply_text(
        quality_picker_message(platform, lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=quality_picker_keyboard(lang),
    )


# ═════════════════════════════════════════════════════
#  DOWNLOAD EXECUTION
# ═════════════════════════════════════════════════════

async def _perform_download(message, user, url, platform, quality, lang, context):
    """Execute the download immediately with per-user and global concurrency guards."""
    chat_id = message.chat_id
    job_prefix = _make_job_prefix(chat_id, user.id)
    semaphore_acquired = False

    # Prevent same user from running multiple downloads at once.
    async with _active_downloads_lock:
        if user.id in _active_downloads:
            await _telegram_with_retry(
                lambda: message.reply_text(
                    "⏳  You already have a download in progress.\nPlease wait for it to finish first.",
                    parse_mode=constants.ParseMode.HTML,
                ),
                "notify existing active download",
            )
            return
        _active_downloads.add(user.id)

    try:
        try:
            await asyncio.wait_for(_global_download_semaphore.acquire(), timeout=20)
            semaphore_acquired = True
        except asyncio.TimeoutError:
            await _telegram_with_retry(
                lambda: message.reply_text(
                    "⚠️  Server is busy right now. Please retry in a few seconds.",
                    parse_mode=constants.ParseMode.HTML,
                ),
                "notify busy server",
            ),
            return

        status_msg = await _telegram_with_retry(
            lambda: message.reply_text(
                downloading_message(platform, lang),
                parse_mode=constants.ParseMode.HTML,
            ),
            "send downloading status",
        )
        if status_msg is None:
            raise RuntimeError("Could not send status message.")

        result = await download_media(
            url,
            chat_id,
            quality=quality,
            platform=platform,
            job_prefix=job_prefix,
        )

        if not result["success"]:
            error = str(result.get("error"))
            if error == "private":
                msg = error_private_content(lang)
            elif error == "not_found":
                msg = error_not_found(lang)
            elif error == "youtube_verification":
                msg = error_download_failed(
                    "YouTube asked for bot verification on this datacenter IP. Please retry.",
                    lang,
                )
            elif error == "format_unavailable":
                msg = error_download_failed(
                    "Requested quality is unavailable for this video. Try another quality.",
                    lang,
                )
            else:
                msg = error_download_failed(error, lang)

            await _telegram_with_retry(
                lambda: status_msg.edit_text(msg, parse_mode=constants.ParseMode.HTML),
                "send download failure status",
            )
            record_download(user.id, url, "unknown", 0,
                            status="failed", error_message=error,
                            platform=platform)
            return

        file_size = int(result.get("file_size") or 0)
        if file_size > MAX_FILE_SIZE:
            await _telegram_with_retry(
                lambda: status_msg.edit_text(
                    error_too_large(file_size, lang),
                    parse_mode=constants.ParseMode.HTML,
                ),
                "send size limit status",
            )
            record_download(user.id, url, result["type"], file_size,
                            status="failed", error_message="too_large",
                            platform=platform)
            return

        await _telegram_with_retry(
            lambda: status_msg.edit_text(
                uploading_message(lang),
                parse_mode=constants.ParseMode.HTML,
            ),
            "send uploading status",
        )

        caption = download_complete_caption(
            result["type"], file_size, result["duration"], platform, lang
        )

        sent = False
        max_attempts = max(2, TELEGRAM_API_RETRIES + 1)
        for attempt in range(max_attempts):
            try:
                if result["type"] == "audio":
                    with open(result["path"], "rb") as f:
                        await message.reply_audio(
                            chat_id=chat_id,
                            audio=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            title=result["title"][:64] if result["title"] else None,
                            duration=int(result["duration"]) if result["duration"] else None,
                            read_timeout=600,
                            write_timeout=600,
                            connect_timeout=60,
                            pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                elif result["type"] == "video":
                    with open(result["path"], "rb") as f:
                        await message.reply_video(
                            chat_id=chat_id,
                            video=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            duration=result["duration"],
                            width=result["width"],
                            height=result["height"],
                            supports_streaming=True,
                            read_timeout=600,
                            write_timeout=600,
                            connect_timeout=60,
                            pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                else:
                    with open(result["path"], "rb") as f:
                        await message.reply_photo(
                            chat_id=chat_id,
                            photo=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            read_timeout=600,
                            write_timeout=600,
                            connect_timeout=60,
                            pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                sent = True
                break
            except RetryAfter as exc:
                wait = max(float(getattr(exc, "retry_after", 1)), 1.0)
                if attempt < max_attempts - 1:
                    await asyncio.sleep(wait)
            except (TimedOut, NetworkError):
                if attempt < max_attempts - 1:
                    await asyncio.sleep(max(1.0, TELEGRAM_API_RETRY_DELAY_SECONDS) * (attempt + 1))
            except Exception as exc:
                logger.warning("Upload attempt %s/%s failed: %s", attempt + 1, max_attempts, exc)
                break

        if sent:
            record_download(user.id, url, result["type"], file_size,
                            result["duration"], status="success", platform=platform)
            log_event(
                "download",
                f"user={user.id}, type={result['type']}, platform={platform}, size={file_size}",
            )
            try:
                await _telegram_with_retry(
                    lambda: status_msg.delete(),
                    "delete status message",
                )
            except Exception:
                pass
        else:
            await _telegram_with_retry(
                lambda: status_msg.edit_text(
                    error_upload_failed(lang),
                    parse_mode=constants.ParseMode.HTML,
                ),
                "send upload failure status",
            )
            record_download(user.id, url, result["type"], file_size,
                            status="failed", error_message="upload_timeout",
                            platform=platform)

    except Exception as exc:
        logger.exception("Download failed unexpectedly for user %s: %s", user.id, exc)
        try:
            await _telegram_with_retry(
                lambda: message.reply_text(
                    error_download_failed("Unexpected processing error", lang),
                    parse_mode=constants.ParseMode.HTML,
                ),
                "send unexpected download error",
            )
        except Exception:
            pass
    finally:
        if semaphore_acquired:
            _global_download_semaphore.release()
        async with _active_downloads_lock:
            _active_downloads.discard(user.id)
        cleanup_job_files(job_prefix)


# ═════════════════════════════════════════════════════
#  BACKGROUND CLEANUP TASK
# ═════════════════════════════════════════════════════

async def _storage_cleanup_loop():
    """
    Runs forever in the background.
    Every 3 minutes: remove files older than MAX_FILE_AGE_SECONDS.
    This keeps /tmp healthy on Railway's limited disk.
    """
    while True:
        try:
            removed = ensure_storage_space()
            if removed:
                logger.info(f"[AutoCleanup] Removed {removed} stale file(s).")
        except Exception as e:
            logger.warning(f"[AutoCleanup] Error: {e}")
        await asyncio.sleep(AUTO_CLEANUP_SECONDS)


# ═════════════════════════════════════════════════════
#  BOT SETUP & LAUNCH
# ═════════════════════════════════════════════════════

async def post_init(application):
    # Register bot commands in Telegram menu
    commands = [
        BotCommand("start",    "🏠 Main Menu"),
        BotCommand("help",     "📖 How to Use"),
        BotCommand("stats",    "📊 My Statistics"),
        BotCommand("history",  "📜 Download History"),
        BotCommand("settings", "⚙️ Settings"),
        BotCommand("about",    "ℹ️ About & Credits"),
        BotCommand("id",       "🆔 Show My ID"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands registered successfully.")

    # Start the background storage cleanup task
    asyncio.create_task(_storage_cleanup_loop())
    logger.info("Storage auto-cleanup task started.")


def main():
    startup_errors = validate_environment()
    if startup_errors:
        print(
            "\n"
            "Configuration error(s):\n"
            + "\n".join(f"- {err}" for err in startup_errors)
            + "\n"
        )
        return

    if not shutil.which("ffmpeg"):
        logger.warning(
            "ffmpeg not found in PATH. YouTube merged quality may be lower (video-only fallbacks)."
        )

    if not ADMIN_IDS:
        logger.warning("ADMIN_IDS is empty. Admin-only commands will be inaccessible.")

    init_database()
    logger.info("Database initialized.")

    print(
        "\n"
        "╔══════════════════════════════════════════════════╗\n"
        f"║  🎬  {BOT_NAME} v{BOT_VERSION}"
        f"{' ' * (39 - len(BOT_NAME) - len(BOT_VERSION))}║\n"
        "║  ──────────────────────────────────────────────  ║\n"
        "║  Platforms: Instagram • YouTube • Pinterest      ║\n"
        "║  Features:  Quality Picker • Audio • Multi-Lang  ║\n"
        "║  ──────────────────────────────────────────────  ║\n"
        "║  Status:  ✅  Running                            ║\n"
        f"║  Dev:     🎮  {DEVELOPER_NAME}"
        f"{' ' * (35 - len(DEVELOPER_NAME))}║\n"
        "║  ──────────────────────────────────────────────  ║\n"
        "║  Press Ctrl+C to stop                            ║\n"
        "╚══════════════════════════════════════════════════╝\n"
    )

    request = HTTPXRequest(
        connection_pool_size=max(50, MAX_CONCURRENT_DOWNLOADS * 20),
        connect_timeout=30,
        read_timeout=600,
        write_timeout=600,
        pool_timeout=120,
    )

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .request(request)
        .get_updates_request(request)
        .concurrent_updates(max(64, MAX_CONCURRENT_DOWNLOADS * 16))
        .rate_limiter(AIORateLimiter(max_retries=3))
        .post_init(post_init)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("about",    cmd_about))
    app.add_handler(CommandHandler("stats",    cmd_stats))
    app.add_handler(CommandHandler("history",  cmd_history))
    app.add_handler(CommandHandler("settings", cmd_settings))
    app.add_handler(CommandHandler("id",       cmd_id))

    # Admin commands
    app.add_handler(CommandHandler("admin",     cmd_admin))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CommandHandler("ban",       cmd_ban))
    app.add_handler(CommandHandler("unban",     cmd_unban))

    # Callbacks (inline buttons)
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Text messages (media links)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    app.add_error_handler(_handle_error)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
