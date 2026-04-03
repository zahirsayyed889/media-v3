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

from telegram import Update, constants, BotCommand
from telegram.ext import (
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
    DEVELOPER_NAME, DEVELOPER_CHANNEL,
)
from database import (
    init_database, register_user, is_user_banned,
    get_user_stats, get_user_history, record_download,
    get_downloads_last_minute, get_global_stats,
    get_all_user_ids, ban_user, unban_user, log_event,
    get_user_lang, set_user_lang, get_user_quality, set_user_quality,
)
from downloader import (
    detect_platform, extract_url,
    download_media, cleanup_files, cleanup_old_files,
    format_size, get_folder_size_mb,
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


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


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
    status = await update.message.reply_text(
        f"📢  Broadcasting to <b>{len(user_ids)}</b> users...",
        parse_mode=constants.ParseMode.HTML,
    )

    broadcast_text = (
        f"{'═' * 32}\n   📢  <b>Announcement</b>\n{'═' * 32}\n\n"
        f"{text}\n\n{'─' * 32}\n<i>⚡ {BOT_NAME} by {DEVELOPER_NAME}</i>"
    )

    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid, text=broadcast_text,
                parse_mode=constants.ParseMode.HTML,
                disable_web_page_preview=True,
            )
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(
        f"📢  <b>Broadcast Complete</b>\n\n"
        f"  ✅  Sent: <b>{success}</b>\n  ❌  Failed: <b>{failed}</b>\n"
        f"  📊  Total: <b>{len(user_ids)}</b>",
        parse_mode=constants.ParseMode.HTML,
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
            pending  = context.user_data.get("pending_url")
            platform = context.user_data.get("pending_platform", "instagram")

            if not pending:
                await query.edit_message_text(
                    "⚠️  Link expired. Please send the link again.",
                    parse_mode=constants.ParseMode.HTML,
                )
                return

            # Clear pending
            context.user_data.pop("pending_url",      None)
            context.user_data.pop("pending_platform", None)

            await _perform_download(
                query.message, user, pending, platform, quality, lang, context
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

    # Rate limiting
    recent = get_downloads_last_minute(user.id)
    if recent >= MAX_DOWNLOADS_PER_MINUTE:
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

    # Store pending URL and show quality picker
    context.user_data["pending_url"]      = url
    context.user_data["pending_platform"] = platform

    await update.message.reply_text(
        quality_picker_message(platform, lang),
        parse_mode=constants.ParseMode.HTML,
        reply_markup=quality_picker_keyboard(lang),
    )


# ═════════════════════════════════════════════════════
#  DOWNLOAD EXECUTION
# ═════════════════════════════════════════════════════

async def _perform_download(message, user, url, platform, quality, lang, context):
    """Execute the download after quality is picked."""
    chat_id = message.chat_id

    # ── Concurrent download guard ────────────────────
    if user.id in _active_downloads:
        await message.reply_text(
            "⏳  You already have a download in progress.\n"
            "Please wait for it to finish first.",
            parse_mode=constants.ParseMode.HTML,
        )
        return

    _active_downloads.add(user.id)

    try:
        # Show downloading status
        status_msg = await message.reply_text(
            downloading_message(platform, lang),
            parse_mode=constants.ParseMode.HTML,
        )

        # Download
        result = await download_media(url, chat_id, quality=quality, platform=platform)

        if not result["success"]:
            error = result["error"]
            if error == "private":
                msg = error_private_content(lang)
            elif error == "not_found":
                msg = error_not_found(lang)
            else:
                msg = error_download_failed(str(error), lang)

            await status_msg.edit_text(msg, parse_mode=constants.ParseMode.HTML)
            record_download(user.id, url, "unknown", 0,
                            status="failed", error_message=str(error),
                            platform=platform)
            cleanup_files(os.path.join(DOWNLOAD_DIR, f"{chat_id}_*"))
            return

        # Check file size
        file_size = result["file_size"]
        if file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(
                error_too_large(file_size, lang),
                parse_mode=constants.ParseMode.HTML,
            )
            record_download(user.id, url, result["type"], file_size,
                            status="failed", error_message="too_large",
                            platform=platform)
            cleanup_files(os.path.join(DOWNLOAD_DIR, f"{chat_id}_*"))
            return

        # Update status to uploading
        try:
            await status_msg.edit_text(
                uploading_message(lang), parse_mode=constants.ParseMode.HTML
            )
        except Exception:
            pass

        # Build caption
        caption = download_complete_caption(
            result["type"], file_size, result["duration"], platform, lang
        )

        # Upload to Telegram (2 attempts)
        sent = False
        for attempt in range(2):
            try:
                if result["type"] == "audio":
                    with open(result["path"], "rb") as f:
                        await message.reply_audio(
                            audio=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            title=result["title"][:64] if result["title"] else None,
                            duration=int(result["duration"]) if result["duration"] else None,
                            read_timeout=600, write_timeout=600,
                            connect_timeout=60, pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                elif result["type"] == "video":
                    with open(result["path"], "rb") as f:
                        await message.reply_video(
                            video=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            duration=result["duration"],
                            width=result["width"],
                            height=result["height"],
                            supports_streaming=True,
                            read_timeout=600, write_timeout=600,
                            connect_timeout=60, pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                else:  # image
                    with open(result["path"], "rb") as f:
                        await message.reply_photo(
                            photo=f,
                            caption=caption,
                            parse_mode=constants.ParseMode.HTML,
                            read_timeout=600, write_timeout=600,
                            connect_timeout=60, pool_timeout=600,
                            reply_markup=after_download_keyboard(lang),
                        )
                sent = True
                break
            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1}/2 failed: {e}")
                if attempt < 1:
                    await asyncio.sleep(2)

        if sent:
            record_download(user.id, url, result["type"], file_size,
                            result["duration"], status="success", platform=platform)
            log_event("download",
                      f"user={user.id}, type={result['type']}, "
                      f"platform={platform}, size={file_size}")
            try:
                await status_msg.delete()
            except Exception:
                pass
        else:
            await status_msg.edit_text(
                error_upload_failed(lang), parse_mode=constants.ParseMode.HTML
            )
            record_download(user.id, url, result["type"], file_size,
                            status="failed", error_message="upload_timeout",
                            platform=platform)

    finally:
        # Always release the lock and clean up files
        _active_downloads.discard(user.id)
        cleanup_files(os.path.join(DOWNLOAD_DIR, f"{chat_id}_*"))


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
            removed = cleanup_old_files()
            if removed:
                logger.info(f"[AutoCleanup] Removed {removed} stale file(s).")
        except Exception as e:
            logger.warning(f"[AutoCleanup] Error: {e}")
        await asyncio.sleep(180)   # every 3 minutes


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
    # ── Token validation ─────────────────────────────
    if not BOT_TOKEN:
        print(
            "\n"
            "╔══════════════════════════════════════════════════╗\n"
            "║  ⚠️   BOT TOKEN NOT SET                          ║\n"
            "║  Set BOT_TOKEN in Railway → Variables            ║\n"
            "╚══════════════════════════════════════════════════╝\n"
        )
        return

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

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(600)
        .write_timeout(600)
        .connect_timeout(60)
        .pool_timeout(600)
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

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
