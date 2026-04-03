"""
╔══════════════════════════════════════════════════════╗
║   🌍  MediaGrab Pro — Multi-Language System           ║
║   English (en) • Hindi (hi)                          ║
╚══════════════════════════════════════════════════════╝
"""

TEXTS = {
    "en": {
        # ── Welcome ──
        "welcome_greet": "Hey <b>{name}</b>!",
        "welcome_sub": "Welcome to the <b>fastest</b> media\ndownloader on Telegram! 🚀",
        "welcome_feat": "🎯  What I can do:",
        "feat_reels": "📹  Download <b>Instagram Reels</b>",
        "feat_yt": "🎬  Download <b>YouTube Videos</b>",
        "feat_shorts": "📱  Grab <b>YouTube Shorts</b>",
        "feat_pin": "📌  Save <b>Pinterest</b> content",
        "feat_audio": "🎵  Extract <b>Audio (MP3)</b>",
        "welcome_tip": "💡  Just <b>paste any link</b>\n     and I'll handle the rest!",

        # ── Help ──
        "help_title": "How to Use {bot}",
        "help_steps": (
            "1️⃣  Open <b>Instagram / YouTube / Pinterest</b>\n"
            "2️⃣  Find any content you want to save\n"
            "3️⃣  Tap <b>Share</b> → <b>Copy Link</b>\n"
            "4️⃣  <b>Paste the link here</b>\n"
            "5️⃣  Choose your quality ⚡\n"
            "6️⃣  Done! ✅"
        ),
        "help_supported": "🔗  Supported Platforms:",
        "help_limits_title": "⚠️  Limitations:",
        "help_limit1": "🔒  Only <b>public</b> content",
        "help_limit2": "📏  Max file size: <b>50 MB</b>",
        "help_limit3": "⏱  Rate limit: <b>5/min</b>",

        # ── Help sub-sections ──
        "help_reels_title": "Downloading Reels",
        "help_reels_steps": "1️⃣  Open the Reel in Instagram\n2️⃣  Tap the <b>⋯</b> menu → <b>Copy Link</b>\n3️⃣  Paste the link here",
        "help_reels_example": "https://www.instagram.com/reel/ABC123/",
        "help_reels_features": "• Full HD quality\n• With audio\n• Duration preview",

        "help_yt_title": "Downloading YouTube Videos",
        "help_yt_steps": "1️⃣  Open the video on YouTube\n2️⃣  Tap <b>Share</b> → <b>Copy Link</b>\n3️⃣  Paste the link here",
        "help_yt_example": "https://www.youtube.com/watch?v=ABC123",
        "help_yt_features": "• Multiple quality options\n• Shorts supported\n• Audio extraction (MP3)",

        "help_pin_title": "Downloading Pinterest",
        "help_pin_steps": "1️⃣  Open the Pin in Pinterest\n2️⃣  Tap <b>⋯</b> → <b>Copy Link</b>\n3️⃣  Paste the link here",
        "help_pin_example": "https://www.pinterest.com/pin/123456/",
        "help_pin_features": "• Images & Videos\n• Original resolution",

        "help_vid_title": "Downloading Videos / IGTV",
        "help_vid_steps": "1️⃣  Open the Video or IGTV in Instagram\n2️⃣  Tap <b>⋯</b> → <b>Copy Link</b>\n3️⃣  Paste the link here",
        "help_vid_example": "https://www.instagram.com/tv/DEF456/",
        "help_vid_features": "• Best available quality\n• Streaming support\n• Duration & size info",

        # ── Quality Picker ──
        "qp_title": "Choose Download Quality",
        "qp_detected": "✨  Link detected!",
        "qp_platform": "Platform: <b>{platform}</b>",
        "qp_prompt": "Select your preferred quality:",
        "qp_best": "🎬 Best Quality",
        "qp_720": "📱 HD 720p",
        "qp_360": "📉 SD 360p",
        "qp_audio": "🎵 Audio Only",

        # ── Download Status ──
        "dl_downloading": "📥  <b>Downloading...</b>",
        "dl_fetching": "⏳  Fetching from {platform}...",
        "dl_uploading": "📤  <b>Uploading...</b>",
        "dl_sending": "⏳  Sending to Telegram...",
        "dl_complete": "✅  <b>Download Complete!</b>",

        # ── Errors ──
        "err_invalid_title": "Invalid URL",
        "err_invalid_body": "That doesn't look like a supported link.",
        "err_invalid_tip": "💡  Tip: Copy the link directly from the app!",
        "err_private_title": "Private Content",
        "err_private_body": "Cannot access this content.\nThis is from a <b>private account</b>.\nOnly public content can be downloaded.",
        "err_notfound_title": "Not Found",
        "err_notfound_body": "This content may have been <b>deleted</b>\nor the link is <b>incorrect</b>.",
        "err_toolarge_title": "File Too Large",
        "err_toolarge_body": "File size: <b>{size}</b>\nTelegram limit: <b>50 MB</b>\n\n💡  Try a lower quality!",
        "err_ratelimit_title": "Slow Down!",
        "err_ratelimit_body": "You're downloading too fast.\nPlease wait <b>1 minute</b>.",
        "err_banned_title": "Access Denied",
        "err_banned_body": "Your account has been <b>restricted</b>.",
        "err_dlfail_title": "Download Failed",
        "err_dlfail_body": "Something went wrong.\n\n💡  Make sure:\n• The link is correct\n• The content is public\n• The post still exists",
        "err_upfail_title": "Upload Failed",
        "err_upfail_body": "Could not send the file.\nPlease try again.",

        # ── Stats ──
        "stats_title": "Your Statistics",
        "stats_total": "Total Downloads",
        "stats_videos": "Videos",
        "stats_images": "Images",
        "stats_audios": "Audios",
        "stats_data": "Data Saved",
        "stats_rank": "Rank",
        "stats_joined": "Joined",

        # ── History ──
        "hist_title": "Download History",
        "hist_empty": "📭  No downloads yet!\n\nSend a link to get started. 🚀",
        "hist_recent": "Recent Downloads",

        # ── Settings ──
        "set_title": "Settings",
        "set_sub": "Configure your preferences.",
        "set_quality": "🎬  Download Quality",
        "set_lang": "🌐  Language",
        "set_quality_current": "Current: <b>{quality}</b>",
        "set_lang_current": "Current: <b>{lang_name}</b>",
        "set_quality_changed": "✅  Default quality set to <b>{quality}</b>",
        "set_lang_changed": "✅  Language changed to <b>English</b> 🇺🇸",

        # ── About ──
        "about_title": "About {bot}",
        "about_desc": "A premium Telegram bot for downloading\nmedia content — fast, reliable,\nand completely <b>free</b>.",
        "about_dev": "Developer",
        "about_support": "Support the Developer",
        "about_support_txt": "If you enjoy this bot,\nplease subscribe to the channel!\nYour support keeps this bot alive. 🙏",
        "about_oss": "Open Source & Free Forever",

        # ── Buttons ──
        "btn_how": "📖 How to Use",
        "btn_stats": "📊 My Stats",
        "btn_hist": "📜 History",
        "btn_set": "⚙️ Settings",
        "btn_dev": "👨‍💻 Developer",
        "btn_about": "ℹ️ About",
        "btn_back": "🔙 Back to Menu",
        "btn_reels": "📹 Reels",
        "btn_yt": "🎬 YouTube",
        "btn_pin": "📌 Pinterest",
        "btn_vid": "🎥 Videos/IGTV",
        "btn_rate": "⭐ Rate Bot",
        "btn_yt_ch": "🎬 YouTube Channel",
        "btn_quality": "🎬 Quality",
        "btn_language": "🌐 Language",
        "btn_en": "🇺🇸 English",
        "btn_hi": "🇮🇳 हिंदी",

        # ── Admin (English only) ──
        "admin_title": "Admin Panel",
        "admin_welcome": "Welcome, Administrator.",
    },

    "hi": {
        "welcome_greet": "नमस्ते <b>{name}</b>! 🙏",
        "welcome_sub": "Telegram पर सबसे <b>तेज़</b> मीडिया\nडाउनलोडर में आपका स्वागत है! 🚀",
        "welcome_feat": "🎯  मैं क्या कर सकता हूँ:",
        "feat_reels": "📹  <b>Instagram Reels</b> डाउनलोड",
        "feat_yt": "🎬  <b>YouTube Videos</b> डाउनलोड",
        "feat_shorts": "📱  <b>YouTube Shorts</b> सेव",
        "feat_pin": "📌  <b>Pinterest</b> कंटेंट सेव",
        "feat_audio": "🎵  <b>ऑडियो (MP3)</b> निकालें",
        "welcome_tip": "💡  बस कोई भी <b>लिंक पेस्ट करें</b>\n     बाकी मैं संभाल लूँगा!",

        "help_title": "{bot} कैसे इस्तेमाल करें",
        "help_steps": (
            "1️⃣  <b>Instagram / YouTube / Pinterest</b> खोलें\n"
            "2️⃣  कोई भी कंटेंट ढूंढें\n"
            "3️⃣  <b>Share</b> → <b>Copy Link</b> पर टैप करें\n"
            "4️⃣  <b>यहाँ लिंक पेस्ट करें</b>\n"
            "5️⃣  क्वालिटी चुनें ⚡\n"
            "6️⃣  हो गया! ✅"
        ),
        "help_supported": "🔗  सपोर्टेड प्लेटफॉर्म:",
        "help_limits_title": "⚠️  सीमाएँ:",
        "help_limit1": "🔒  सिर्फ <b>पब्लिक</b> कंटेंट",
        "help_limit2": "📏  फ़ाइल लिमिट: <b>50 MB</b>",
        "help_limit3": "⏱  रेट लिमिट: <b>5/मिनट</b>",

        "help_reels_title": "Reels डाउनलोड करें",
        "help_reels_steps": "1️⃣  Instagram में Reel खोलें\n2️⃣  <b>⋯</b> मेनू → <b>Copy Link</b>\n3️⃣  यहाँ लिंक पेस्ट करें",
        "help_reels_example": "https://www.instagram.com/reel/ABC123/",
        "help_reels_features": "• Full HD क्वालिटी\n• ऑडियो के साथ\n• अवधि प्रीव्यू",

        "help_yt_title": "YouTube Videos डाउनलोड करें",
        "help_yt_steps": "1️⃣  YouTube पर वीडियो खोलें\n2️⃣  <b>Share</b> → <b>Copy Link</b>\n3️⃣  यहाँ लिंक पेस्ट करें",
        "help_yt_example": "https://www.youtube.com/watch?v=ABC123",
        "help_yt_features": "• कई क्वालिटी विकल्प\n• Shorts सपोर्ट\n• ऑडियो (MP3) निकालें",

        "help_pin_title": "Pinterest डाउनलोड करें",
        "help_pin_steps": "1️⃣  Pinterest में Pin खोलें\n2️⃣  <b>⋯</b> → <b>Copy Link</b>\n3️⃣  यहाँ लिंक पेस्ट करें",
        "help_pin_example": "https://www.pinterest.com/pin/123456/",
        "help_pin_features": "• तस्वीरें और वीडियो\n• ओरिजिनल रेज़ॉल्यूशन",

        "help_vid_title": "Videos / IGTV डाउनलोड करें",
        "help_vid_steps": "1️⃣  Instagram में Video/IGTV खोलें\n2️⃣  <b>⋯</b> → <b>Copy Link</b>\n3️⃣  यहाँ लिंक पेस्ट करें",
        "help_vid_example": "https://www.instagram.com/tv/DEF456/",
        "help_vid_features": "• बेस्ट क्वालिटी\n• स्ट्रीमिंग सपोर्ट\n• अवधि और साइज़ जानकारी",

        "qp_title": "डाउनलोड क्वालिटी चुनें",
        "qp_detected": "✨  लिंक मिल गया!",
        "qp_platform": "प्लेटफॉर्म: <b>{platform}</b>",
        "qp_prompt": "अपनी पसंदीदा क्वालिटी चुनें:",
        "qp_best": "🎬 बेस्ट क्वालिटी",
        "qp_720": "📱 HD 720p",
        "qp_360": "📉 SD 360p",
        "qp_audio": "🎵 सिर्फ ऑडियो",

        "dl_downloading": "📥  <b>डाउनलोड हो रहा है...</b>",
        "dl_fetching": "⏳  {platform} से फ़ेच कर रहे हैं...",
        "dl_uploading": "📤  <b>अपलोड हो रहा है...</b>",
        "dl_sending": "⏳  Telegram पर भेज रहे हैं...",
        "dl_complete": "✅  <b>डाउनलोड पूरा!</b>",

        "err_invalid_title": "अमान्य URL",
        "err_invalid_body": "यह एक सपोर्टेड लिंक नहीं लग रहा।",
        "err_invalid_tip": "💡  टिप: ऐप से सीधे लिंक कॉपी करें!",
        "err_private_title": "प्राइवेट कंटेंट",
        "err_private_body": "इस कंटेंट को एक्सेस नहीं कर सकते।\nयह एक <b>प्राइवेट अकाउंट</b> से है।",
        "err_notfound_title": "नहीं मिला",
        "err_notfound_body": "यह कंटेंट शायद <b>डिलीट</b> हो गया\nया लिंक <b>गलत</b> है।",
        "err_toolarge_title": "फ़ाइल बहुत बड़ी",
        "err_toolarge_body": "फ़ाइल साइज़: <b>{size}</b>\nTelegram लिमिट: <b>50 MB</b>\n\n💡  कम क्वालिटी आज़माएँ!",
        "err_ratelimit_title": "धीरे चलें!",
        "err_ratelimit_body": "बहुत तेज़ डाउनलोड हो रहा है।\nकृपया <b>1 मिनट</b> रुकें।",
        "err_banned_title": "एक्सेस नहीं है",
        "err_banned_body": "आपका अकाउंट <b>प्रतिबंधित</b> किया गया है।",
        "err_dlfail_title": "डाउनलोड फ़ेल",
        "err_dlfail_body": "कुछ गड़बड़ हो गई।\n\n💡  सुनिश्चित करें:\n• लिंक सही है\n• कंटेंट पब्लिक है\n• पोस्ट मौजूद है",
        "err_upfail_title": "अपलोड फ़ेल",
        "err_upfail_body": "फ़ाइल नहीं भेज पाए।\nकृपया फिर से कोशिश करें।",

        "stats_title": "आपके आंकड़े",
        "stats_total": "कुल डाउनलोड",
        "stats_videos": "वीडियो",
        "stats_images": "तस्वीरें",
        "stats_audios": "ऑडियो",
        "stats_data": "डेटा सेव किया",
        "stats_rank": "रैंक",
        "stats_joined": "जुड़े",

        "hist_title": "डाउनलोड इतिहास",
        "hist_empty": "📭  अभी तक कोई डाउनलोड नहीं!\n\nशुरू करने के लिए लिंक भेजें। 🚀",
        "hist_recent": "हालिया डाउनलोड",

        "set_title": "सेटिंग्स",
        "set_sub": "अपनी प्राथमिकताएँ सेट करें।",
        "set_quality": "🎬  डाउनलोड क्वालिटी",
        "set_lang": "🌐  भाषा",
        "set_quality_current": "वर्तमान: <b>{quality}</b>",
        "set_lang_current": "वर्तमान: <b>{lang_name}</b>",
        "set_quality_changed": "✅  डिफ़ॉल्ट क्वालिटी <b>{quality}</b> सेट हो गई",
        "set_lang_changed": "✅  भाषा <b>हिंदी</b> में बदल गई 🇮🇳",

        "about_title": "{bot} के बारे में",
        "about_desc": "मीडिया डाउनलोड करने के लिए एक प्रीमियम\nTelegram बॉट — तेज़, भरोसेमंद,\nऔर पूरी तरह <b>मुफ़्त</b>।",
        "about_dev": "डेवलपर",
        "about_support": "डेवलपर को सपोर्ट करें",
        "about_support_txt": "अगर आपको यह बॉट पसंद है,\nतो कृपया चैनल सब्सक्राइब करें!\nआपका सपोर्ट इस बॉट को जिंदा रखता है। 🙏",
        "about_oss": "ओपन सोर्स और हमेशा मुफ़्त",

        "btn_how": "📖 कैसे करें",
        "btn_stats": "📊 मेरे आंकड़े",
        "btn_hist": "📜 इतिहास",
        "btn_set": "⚙️ सेटिंग्स",
        "btn_dev": "👨‍💻 डेवलपर",
        "btn_about": "ℹ️ जानकारी",
        "btn_back": "🔙 वापस जाएँ",
        "btn_reels": "📹 Reels",
        "btn_yt": "🎬 YouTube",
        "btn_pin": "📌 Pinterest",
        "btn_vid": "🎥 Videos/IGTV",
        "btn_rate": "⭐ रेट करें",
        "btn_yt_ch": "🎬 YouTube चैनल",
        "btn_quality": "🎬 क्वालिटी",
        "btn_language": "🌐 भाषा",
        "btn_en": "🇺🇸 English",
        "btn_hi": "🇮🇳 हिंदी",

        "admin_title": "एडमिन पैनल",
        "admin_welcome": "स्वागत है, एडमिन।",
    },
}

# ── Language display names ──
LANG_NAMES = {"en": "English 🇺🇸", "hi": "हिंदी 🇮🇳"}
QUALITY_NAMES = {"best": "Best Quality", "720p": "HD 720p", "360p": "SD 360p", "audio": "Audio Only"}
PLATFORM_NAMES = {"instagram": "Instagram", "youtube": "YouTube", "pinterest": "Pinterest"}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get a translated string with optional formatting."""
    texts = TEXTS.get(lang, TEXTS["en"])
    text = texts.get(key, TEXTS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
