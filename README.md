<div align="center">

# 🌸 Cutiepii Robot

**A powerful, modular, and cute Telegram group management bot.**

![Upgraded](https://img.shields.io/badge/Upgraded-PTB%2020.0a0%20→%2022.8-brightgreen?style=for-the-badge&logo=telegram&logoColor=white)

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-22.8-00b2ff?style=for-the-badge&logo=telegram&logoColor=white)](https://github.com/python-telegram-bot/python-telegram-bot)
[![Telethon](https://img.shields.io/badge/Telethon-1.42%2B-0088cc?style=for-the-badge&logo=telegram&logoColor=white)](https://github.com/LonamiWebs/Telethon)
[![License](https://img.shields.io/badge/License-BSD_2--Clause-orange?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/Awesome-RJ/CutiepiiRobot?style=for-the-badge&logo=github)](https://github.com/Awesome-RJ/CutiepiiRobot)

</div>

---

## ✨ What is Cutiepii?

Cutiepii Robot is a fully-featured, modular Telegram bot built for group management. It's fast, reliable, and packed with features — from bans and warnings to AI chatbot and anime search.

> 🚀 **Major Comeback!** Last publicly released ~4 years ago on `python-telegram-bot v20.0a0`.
> This version is a **complete rewrite and upgrade** to **PTB v22.8** with async/await, full Python 3.9+ support, and many new modules.

---

## ⬆️ Migration Highlights

| Before (4 years ago) | Now |
|---|---|
| PTB `20.0a0` (alpha) | PTB `22.8` (stable) |
| Sync handlers | Fully `async/await` |
| Basic admin modules | 50+ modules |
| No AI chatbot | Gemini + OpenRouter AI chatbot |
| No welcome image | Dynamic Pillow welcome cards |
| Single language | 5 languages (EN, HI, ES, JA, RU) |
| Redis optional | Redis + PostgreSQL required |

---

## 📦 Core Libraries

| Library | Version | Purpose |
|---|---|---|
| `python-telegram-bot` | 22.8 | Primary bot framework |
| `telethon` | ≥ 1.42.0 | MTProto client for advanced features |
| `SQLAlchemy` | 1.4.x | SQL database ORM |
| `redis` | ≥ 5.0 | Caching & rate limiting |
| `aiohttp` | 3.9.5 | Async HTTP requests |
| `Pillow` | ≥ 10.2 | Image processing & welcome cards |
| `APScheduler` | ≥ 3.10 | Scheduled jobs & reminders |
| `yt-dlp` | ≥ 2024.1 | Media downloading |

---

## 🚀 Features

- 🛡️ **Admin Tools** — Ban, kick, mute, warn, and purge
- 👋 **Welcome & Goodbye** — Custom messages with dynamic placeholders
- 🤖 **AI Chatbot** — Powered by Gemini & OpenRouter (bring your own API key)
- 📝 **Filters & Notes** — Save and trigger custom text or media
- ⚠️ **Warnings System** — Configurable warn limits with auto-action
- 🔒 **Locks & Anti-Spam** — Flood control, blacklists, NSFW detection
- 🎌 **Anime & Fun** — AniList, Jikan, wallpapers, memes, and more
- ⏰ **Reminders** — Set personal or group reminders
- 🌍 **Multi-language** — English, Hindi, Spanish, Japanese, Russian

---

## ⚙️ Setup

1. Clone the repo and install dependencies:
   ```bash
   git clone https://github.com/Awesome-RJ/CutiepiiRobot
   cd CutiepiiRobot
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your values:
   ```bash
   cp .env.example .env
   ```

3. Run the bot:
   ```bash
   python -m Cutiepii_Robot
   ```

> See `.env.example` for all available configuration options.

---

## 🙏 Credits

| Contributor | Role |
|---|---|
| [Awesome-RJ](https://github.com/Awesome-RJ) | Creator & Lead Developer |
| [Paul Larsen](https://github.com/PaulSonOfLars) | Original Marie Bot base |
| [python-telegram-bot team](https://github.com/python-telegram-bot) | Core bot framework |
| [LonamiWebs](https://github.com/LonamiWebs/Telethon) | Telethon MTProto library |

---

<div align="center">

Made with ❤️ by [Awesome-RJ](https://github.com/Awesome-RJ)

</div>
