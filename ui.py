"""
╔══════════════════════════════════════════════════════╗
║   🎨  MediaGrab Pro — Premium UI Messages             ║
║   Multi-language keyboards & messages                 ║
╚══════════════════════════════════════════════════════╝
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import (
    BOT_NAME, BOT_VERSION, DEVELOPER_NAME,
    DEVELOPER_CHANNEL, SUPPORT_LINK,
)
from downloader import format_size, format_duration
from lang import t, LANG_NAMES, QUALITY_NAMES, PLATFORM_NAMES


# ═════════════════════════════════════════════════════
#  KEYBOARDS
# ═════════════════════════════════════════════════════

def main_menu_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_how", lang), callback_data="help"),
            InlineKeyboardButton(t("btn_stats", lang), callback_data="stats"),
        ],
        [
            InlineKeyboardButton(t("btn_hist", lang), callback_data="history"),
            InlineKeyboardButton(t("btn_set", lang), callback_data="settings"),
        ],
        [
            InlineKeyboardButton(t("btn_dev", lang), url=DEVELOPER_CHANNEL),
            InlineKeyboardButton(t("btn_about", lang), callback_data="about"),
        ],
    ])


def back_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_back", lang), callback_data="start")],
    ])


def help_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_reels", lang), callback_data="help_reels"),
            InlineKeyboardButton(t("btn_yt", lang), callback_data="help_yt"),
        ],
        [
            InlineKeyboardButton(t("btn_pin", lang), callback_data="help_pin"),
            InlineKeyboardButton(t("btn_vid", lang), callback_data="help_vid"),
        ],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="start")],
    ])


def settings_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("set_quality", lang), callback_data="setting_quality")],
        [InlineKeyboardButton(t("set_lang", lang), callback_data="setting_lang")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="start")],
    ])


def quality_settings_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Best Quality", callback_data="setq_best")],
        [InlineKeyboardButton("📱 HD 720p", callback_data="setq_720p")],
        [InlineKeyboardButton("📉 SD 360p", callback_data="setq_360p")],
        [InlineKeyboardButton("🎵 Audio Only (MP3)", callback_data="setq_audio")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="settings")],
    ])


def language_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 English", callback_data="setlang_en")],
        [InlineKeyboardButton("🇮🇳 हिंदी", callback_data="setlang_hi")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="settings")],
    ])


def quality_picker_keyboard(lang="en"):
    """Inline keyboard shown when user sends a link to pick download quality."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("qp_best", lang), callback_data="dl_best"),
            InlineKeyboardButton(t("qp_720", lang), callback_data="dl_720p"),
        ],
        [
            InlineKeyboardButton(t("qp_360", lang), callback_data="dl_360p"),
            InlineKeyboardButton(t("qp_audio", lang), callback_data="dl_audio"),
        ],
    ])


def admin_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔧 System", callback_data="admin_system"),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="start")],
    ])


def after_download_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_stats", lang), callback_data="stats"),
            InlineKeyboardButton(t("btn_hist", lang), callback_data="history"),
        ],
        [
            InlineKeyboardButton(t("btn_rate", lang), url=DEVELOPER_CHANNEL),
        ],
    ])


def credit_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_yt_ch", lang), url=DEVELOPER_CHANNEL)],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="start")],
    ])


# ═════════════════════════════════════════════════════
#  MESSAGE TEMPLATES
# ═════════════════════════════════════════════════════

def welcome_message(first_name: str, lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🎬  <b>{BOT_NAME}</b>  v{BOT_VERSION}\n"
        f"{'═' * 32}\n\n"
        f"{t('welcome_greet', lang, name=first_name)}\n\n"
        f"{t('welcome_sub', lang)}\n\n"
        f"<b>{t('welcome_feat', lang)}</b>\n\n"
        f"  {t('feat_reels', lang)}\n"
        f"  {t('feat_yt', lang)}\n"
        f"  {t('feat_shorts', lang)}\n"
        f"  {t('feat_pin', lang)}\n"
        f"  {t('feat_audio', lang)}\n\n"
        f"{'─' * 32}\n"
        f"{t('welcome_tip', lang)}\n"
        f"{'─' * 32}\n\n"
        f"⚡ <i>Powered by {DEVELOPER_NAME}</i>"
    )


def help_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   📖  <b>{t('help_title', lang, bot=BOT_NAME)}</b>\n"
        f"{'═' * 32}\n\n"
        f"<b>📋  Quick Guide:</b>\n\n"
        f"  {t('help_steps', lang)}\n\n"
        f"{'─' * 32}\n\n"
        f"<b>{t('help_supported', lang)}</b>\n\n"
        f"  ✅  <b>Instagram</b> — Reels, Videos, IGTV\n"
        f"  ✅  <b>YouTube</b> — Videos, Shorts\n"
        f"  ✅  <b>Pinterest</b> — Pins\n\n"
        f"<b>{t('help_limits_title', lang)}</b>\n\n"
        f"  {t('help_limit1', lang)}\n"
        f"  {t('help_limit2', lang)}\n"
        f"  {t('help_limit3', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def help_reels_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   📹  <b>{t('help_reels_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"<b>Steps:</b>\n\n  {t('help_reels_steps', lang)}\n\n"
        f"<b>📎  Example:</b>\n<code>{t('help_reels_example', lang)}</code>\n\n"
        f"<b>✨  Features:</b>\n  {t('help_reels_features', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def help_youtube_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🎬  <b>{t('help_yt_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"<b>Steps:</b>\n\n  {t('help_yt_steps', lang)}\n\n"
        f"<b>📎  Example:</b>\n<code>{t('help_yt_example', lang)}</code>\n\n"
        f"<b>✨  Features:</b>\n  {t('help_yt_features', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def help_pinterest_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   📌  <b>{t('help_pin_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"<b>Steps:</b>\n\n  {t('help_pin_steps', lang)}\n\n"
        f"<b>📎  Example:</b>\n<code>{t('help_pin_example', lang)}</code>\n\n"
        f"<b>✨  Features:</b>\n  {t('help_pin_features', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def help_videos_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🎥  <b>{t('help_vid_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"<b>Steps:</b>\n\n  {t('help_vid_steps', lang)}\n\n"
        f"<b>📎  Example:</b>\n<code>{t('help_vid_example', lang)}</code>\n\n"
        f"<b>✨  Features:</b>\n  {t('help_vid_features', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def quality_picker_message(platform: str, lang="en") -> str:
    pname = PLATFORM_NAMES.get(platform, platform.title())
    return (
        f"{'═' * 32}\n"
        f"   ⚡  <b>{t('qp_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('qp_detected', lang)}\n"
        f"  {t('qp_platform', lang, platform=pname)}\n\n"
        f"  {t('qp_prompt', lang)}\n"
    )


def about_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   ℹ️  <b>{t('about_title', lang, bot=BOT_NAME)}</b>\n"
        f"{'═' * 32}\n\n"
        f"🤖  <b>{BOT_NAME}</b> v{BOT_VERSION}\n\n"
        f"{t('about_desc', lang)}\n\n"
        f"{'─' * 32}\n\n"
        f"👨‍💻  <b>{t('about_dev', lang)}</b>\n\n"
        f"  🎮  <b>{DEVELOPER_NAME}</b>\n"
        f"  🎬  <a href='{DEVELOPER_CHANNEL}'>YouTube Channel</a>\n\n"
        f"{'─' * 32}\n\n"
        f"💝  <b>{t('about_support', lang)}</b>\n\n"
        f"  {t('about_support_txt', lang)}\n\n"
        f"{'─' * 32}\n\n"
        f"📜  <b>{t('about_oss', lang)}</b>\n"
        f"    Built with ❤️ by {DEVELOPER_NAME}\n\n"
        f"{'═' * 32}"
    )


def stats_message(user_stats: dict, first_name: str, lang="en") -> str:
    total_size = format_size(user_stats["total_bytes"])
    return (
        f"{'═' * 32}\n"
        f"   📊  <b>{t('stats_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"👤  <b>{first_name}</b>\n\n"
        f"{'─' * 32}\n\n"
        f"  📥  {t('stats_total', lang)}:  <b>{user_stats['total_downloads']}</b>\n"
        f"  📹  {t('stats_videos', lang)}:           <b>{user_stats['videos']}</b>\n"
        f"  🖼  {t('stats_images', lang)}:           <b>{user_stats['images']}</b>\n"
        f"  🎵  {t('stats_audios', lang)}:           <b>{user_stats.get('audios', 0)}</b>\n"
        f"  💾  {t('stats_data', lang)}:       <b>{total_size}</b>\n\n"
        f"{'─' * 32}\n\n"
        f"  🏆  {t('stats_rank', lang)}:  <b>#{user_stats['rank']}</b>\n"
        f"  📅  {t('stats_joined', lang)}: <b>{user_stats['joined_at'][:10]}</b>\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def history_message(history: list, lang="en") -> str:
    if not history:
        return (
            f"{'═' * 32}\n"
            f"   📜  <b>{t('hist_title', lang)}</b>\n"
            f"{'═' * 32}\n\n"
            f"  {t('hist_empty', lang)}\n\n"
            f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
        )

    lines = [
        f"{'═' * 32}\n"
        f"   📜  <b>{t('hist_recent', lang)}</b>\n"
        f"{'═' * 32}\n"
    ]

    for i, item in enumerate(history, 1):
        ct = item.get("content_type", "video")
        icon = "🎵" if ct == "audio" else ("🖼" if ct == "image" else "📹")
        plat = item.get("platform", "instagram")
        plat_icon = {"instagram": "📸", "youtube": "🎬", "pinterest": "📌"}.get(plat, "🔗")
        size = format_size(item.get("file_size", 0))
        date = item["downloaded_at"][:16].replace("T", " ")
        lines.append(
            f"\n  {icon}  <b>#{i}</b>  {plat_icon}  •  {size}\n"
            f"      📅  {date}\n"
        )

    lines.append(f"\n<i>⚡ Powered by {DEVELOPER_NAME}</i>")
    return "".join(lines)


def settings_message(lang="en", current_quality="best", current_lang="en") -> str:
    qname = QUALITY_NAMES.get(current_quality, current_quality)
    lname = LANG_NAMES.get(current_lang, current_lang)
    return (
        f"{'═' * 32}\n"
        f"   ⚙️  <b>{t('set_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('set_sub', lang)}\n\n"
        f"  {t('set_quality', lang)}\n"
        f"    {t('set_quality_current', lang, quality=qname)}\n\n"
        f"  {t('set_lang', lang)}\n"
        f"    {t('set_lang_current', lang, lang_name=lname)}\n\n"
        f"{'─' * 32}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


# ═════════════════════════════════════════════════════
#  DOWNLOAD STATUS MESSAGES
# ═════════════════════════════════════════════════════

def downloading_message(platform="instagram", lang="en") -> str:
    pname = PLATFORM_NAMES.get(platform, platform.title())
    return (
        f"{'═' * 32}\n"
        f"   {t('dl_downloading', lang)}\n"
        f"{'═' * 32}\n\n"
        f"  {t('dl_fetching', lang, platform=pname)}\n\n"
        f"  ▓▓▓▓▓░░░░░░░░░░  <b>33%</b>\n\n"
        f"  <i>Please wait...</i>"
    )


def uploading_message(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   {t('dl_uploading', lang)}\n"
        f"{'═' * 32}\n\n"
        f"  {t('dl_sending', lang)}\n\n"
        f"  ▓▓▓▓▓▓▓▓▓▓▓░░░░  <b>75%</b>\n\n"
        f"  <i>Almost there!</i>"
    )


def download_complete_caption(content_type: str, file_size: int,
                               duration: int = None, platform: str = "instagram",
                               lang="en") -> str:
    size = format_size(file_size)
    dur = format_duration(duration) if content_type in ("video", "audio") and duration else None
    pname = PLATFORM_NAMES.get(platform, platform.title())

    info_lines = f"  📦  Size: <b>{size}</b>\n"
    if dur:
        info_lines += f"  ⏱  Duration: <b>{dur}</b>\n"
    info_lines += f"  📁  Type: <b>{content_type.title()}</b>\n"
    info_lines += f"  🔗  Source: <b>{pname}</b>\n"

    return (
        f"{t('dl_complete', lang)}\n\n"
        f"{'─' * 30}\n"
        f"{info_lines}"
        f"{'─' * 30}\n\n"
        f"⚡ <b>{BOT_NAME}</b> • by <a href='{DEVELOPER_CHANNEL}'>{DEVELOPER_NAME}</a>"
    )


# ═════════════════════════════════════════════════════
#  ERROR MESSAGES
# ═════════════════════════════════════════════════════

def error_invalid_url(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   ❌  <b>{t('err_invalid_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_invalid_body', lang)}\n\n"
        f"  <b>📎  Supported:</b>\n\n"
        f"  • <b>Instagram</b> — Reels, Videos\n"
        f"  • <b>YouTube</b> — Videos, Shorts\n"
        f"  • <b>Pinterest</b> — Pins\n\n"
        f"  {t('err_invalid_tip', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_private_content(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🔒  <b>{t('err_private_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_private_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_not_found(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🔍  <b>{t('err_notfound_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_notfound_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_too_large(file_size: int, lang="en") -> str:
    size = format_size(file_size)
    return (
        f"{'═' * 32}\n"
        f"   ⚠️  <b>{t('err_toolarge_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_toolarge_body', lang, size=size)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_rate_limit(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   ⏱  <b>{t('err_ratelimit_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_ratelimit_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_banned(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   🚫  <b>{t('err_banned_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_banned_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_download_failed(error_msg: str, lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   ❌  <b>{t('err_dlfail_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_dlfail_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def error_upload_failed(lang="en") -> str:
    return (
        f"{'═' * 32}\n"
        f"   ❌  <b>{t('err_upfail_title', lang)}</b>\n"
        f"{'═' * 32}\n\n"
        f"  {t('err_upfail_body', lang)}\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


# ═════════════════════════════════════════════════════
#  ADMIN MESSAGES
# ═════════════════════════════════════════════════════

def admin_panel_message() -> str:
    return (
        f"{'═' * 32}\n"
        f"   🛡️  <b>Admin Panel</b>\n"
        f"{'═' * 32}\n\n"
        f"  Welcome, Administrator.\n\n"
        f"  Select an option below:\n\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )


def admin_stats_message(stats: dict) -> str:
    total_size = format_size(stats["total_bytes"])
    total_cached = stats.get("total_cached", 0)
    cached_size = format_size(stats.get("cached_bytes", 0))
    
    top_lines = ""
    for i, u in enumerate(stats.get("top_users", []), 1):
        name = u.get("first_name") or u.get("username") or str(u["user_id"])
        top_lines += f"  {i}. {name} — <b>{u['total_downloads']}</b> downloads\n"

    return (
        f"{'═' * 32}\n"
        f"   📊  <b>Bot Statistics</b>\n"
        f"{'═' * 32}\n\n"
        f"  👥  Total Users:       <b>{stats['total_users']}</b>\n"
        f"  🟢  Active Today:      <b>{stats['active_today']}</b>\n"
        f"  🚫  Banned:            <b>{stats['banned_users']}</b>\n\n"
        f"{'─' * 32}\n\n"
        f"  📥  Total Downloads:   <b>{stats['total_downloads']}</b>\n"
        f"  📅  Today:             <b>{stats['downloads_today']}</b>\n"
        f"  📹  Videos:            <b>{stats['total_videos']}</b>\n"
        f"  🖼  Images:            <b>{stats['total_images']}</b>\n"
        f"  🎵  Audios:            <b>{stats.get('total_audios', 0)}</b>\n"
        f"  ❌  Failed:            <b>{stats['failed_downloads']}</b>\n"
        f"  💾  Total GB Sent:     <b>{total_size}</b>\n\n"
        f"{'─' * 32}\n\n"
        f"  ⚡  <b>System Health & Cache</b>\n"
        f"  📦  Cached Files:      <b>{total_cached} items</b>\n"
        f"  💽  Cache Footprint:   <b>{cached_size}</b>\n\n"
        f"{'─' * 32}\n\n"
        f"  🏆  <b>Top Users:</b>\n\n"
        f"{top_lines}\n"
        f"<i>⚡ Powered by {DEVELOPER_NAME}</i>"
    )
