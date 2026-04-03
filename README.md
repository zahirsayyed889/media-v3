# 🎬 MediaGrab Pro v3.0.0

### Premium Multi-Platform Media Downloader Bot for Telegram
> Developed by **[ProofyGamerz](https://www.youtube.com/@ProofyGamerz)**

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)](https://python.org)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red?style=flat-square)](https://github.com/yt-dlp/yt-dlp)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-purple?style=flat-square&logo=railway)](https://railway.app)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=flat-square&logo=telegram)](https://telegram.org)

---

## ✨ Features

### 📥 Download Engine
- 📹 **Instagram** — Reels, Posts, IGTV, Carousels
- 🎬 **YouTube** — Videos, Shorts (HD with audio merge)
- 📌 **Pinterest** — Images & Videos
- 🎵 **Audio Extraction** — MP3 from any supported platform
- 🔀 **Quality Picker** — Best, 720p, 360p, Audio Only

### 🎨 UI & Experience
- Clean formatted messages with emoji
- Inline keyboard navigation
- Progress status updates (Downloading → Uploading)
- Hindi 🇮🇳 & English 🇺🇸 language support

### 👤 User System
- Auto user registration
- Personal download statistics
- Download history (last 10)
- User ranking system
- Rate limiting (5 downloads/min)
- Ban / Unban system

### 🛡️ Admin Panel
- `/admin` — Admin control panel
- `/broadcast <msg>` — Message all users
- `/ban <id>` — Ban a user
- `/unban <id>` — Unban a user
- Global bot statistics + top users leaderboard
- Live disk usage monitor

### 🔒 Security & Stability
- Concurrent download lock (one download per user at a time)
- Auto storage cleanup every 3 minutes
- Rate limiting per user
- Input validation & error tracking
- Railway-safe /tmp storage management

---

## 🚀 Deploy on Railway

### 1. Fork / Clone this repo
```bash
git clone https://github.com/yourname/mediagrab-pro
cd mediagrab-pro
```

### 2. Get a Bot Token
1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow the prompts
3. Copy the **API Token**

### 3. Get your Telegram ID
Start the bot and send `/id` — or use [@userinfobot](https://t.me/userinfobot)

### 4. Deploy to Railway
1. Go to [railway.app](https://railway.app) → **New Project**
2. Select **Deploy from GitHub repo**
3. Choose this repository
4. Go to **Variables** tab and add:

| Variable | Value |
|---|---|
| `BOT_TOKEN` | your bot token from @BotFather |
| `ADMIN_IDS` | your Telegram user ID |

5. Railway auto-detects `nixpacks.toml` → installs **FFmpeg + Python 3.11**
6. ✅ Bot is live!

> 💡 No other configuration needed. All paths are automatically set for Railway's `/tmp` storage.

---

## 🖥️ Run Locally

### Requirements
- Python 3.11+
- FFmpeg installed (`sudo apt install ffmpeg` or `brew install ffmpeg`)

### Setup
```bash
pip install -r requirements.txt
```

### Configure
Set environment variables or edit `config.py`:
```bash
export BOT_TOKEN="your_token_here"
export ADMIN_IDS="your_telegram_id"
```

### Run
```bash
python bot.py
```

---

## 📋 Commands

| Command | Description |
|---|---|
| `/start` | 🏠 Main Menu |
| `/help` | 📖 How to use |
| `/stats` | 📊 Personal download statistics |
| `/history` | 📜 Recent download history |
| `/settings` | ⚙️ Quality & language preferences |
| `/about` | ℹ️ About & credits |
| `/id` | 🆔 Show your Telegram ID |

### Admin Commands
| Command | Description |
|---|---|
| `/admin` | 🛡️ Admin control panel |
| `/broadcast <msg>` | 📢 Send message to all users |
| `/ban <user_id>` | 🚫 Ban a user |
| `/unban <user_id>` | ✅ Unban a user |

---

## 📁 Project Structure

```
MediaGrab Pro/
├── bot.py            # Main bot — handlers, download flow, cleanup task
├── config.py         # Configuration — env vars, quality strings, paths
├── database.py       # SQLite layer — users, downloads, stats
├── downloader.py     # yt-dlp engine — URL detection, platform options
├── ui.py             # UI messages & inline keyboards
├── lang.py           # English + Hindi translations
├── requirements.txt  # Python dependencies
├── nixpacks.toml     # Railway build config (FFmpeg + Python 3.11)
└── README.md
```

---

## ⚙️ Tech Stack

| Tool | Purpose |
|---|---|
| **Python 3.11** | Runtime |
| **python-telegram-bot 21.6** | Telegram Bot API |
| **yt-dlp** | Media extraction engine |
| **FFmpeg** | Video/audio merging for HD quality |
| **SQLite** | Local database (users, stats, history) |
| **Railway** | Cloud deployment platform |

---

## 🔧 How It Works

```
User pastes link
      │
      ▼
Platform detected (Instagram / YouTube / Pinterest)
      │
      ▼
Quality picker shown (Best / 720p / 360p / Audio)
      │
      ▼
yt-dlp downloads to /tmp with platform-specific options
  • YouTube  → iOS client UA (bypasses bot check)
  • Instagram → Mobile Safari UA
  • Pinterest → Chrome desktop UA
      │
      ▼
FFmpeg merges video + audio (HD quality)
      │
      ▼
File sent to Telegram → /tmp cleaned up immediately
```

---

## ⚠️ Notes

- Only **public** content can be downloaded
- Telegram file size limit: **50 MB**
- FFmpeg is required for HD YouTube quality (auto-installed on Railway)
- Database and downloads are stored in `/tmp` on Railway (resets on redeploy)
- For persistent stats across redeploys, add a Railway Volume and set `DATABASE_FILE=/data/mediagrab_pro.db`

---

## 📜 Credits

**Developed by [ProofyGamerz](https://www.youtube.com/@ProofyGamerz)**

- 🎬 YouTube: [youtube.com/@ProofyGamerz](https://www.youtube.com/@ProofyGamerz)
