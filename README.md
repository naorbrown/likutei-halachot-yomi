# Likutei Halachot Yomi 📚

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot delivering two daily halachot from **Likutei Halachot** by Rebbe Natan of Breslov — spreading the light of Rebbe Nachman's teachings.

## ✨ Features

- **Daily Inspiration** — Two halachot delivered at 6 AM Israel time
- **Fresh Content** — Different selections each day, never recycling year over year
- **Interactive Commands** — `/start`, `/today`, `/about`, `/help`
- **Bilingual** — Hebrew text with English translation
- **Deep Links** — Direct Sefaria links to continue learning

## 🚀 Quick Start

### 1. Create Your Bot
Talk to [@BotFather](https://t.me/botfather) on Telegram:
```
/newbot
```
Save the token you receive.

### 2. Get Your Chat ID
Add [@userinfobot](https://t.me/userinfobot) to your group or message it directly to get your chat ID.

### 3. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your forked `likutei-halachot-yomi` repo
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` — Your bot token
   - `TELEGRAM_CHAT_ID` — Your chat ID
5. Deploy!

The bot will run 24/7 and respond to commands instantly.

### 4. Add GitHub Secrets (for backup broadcasts)

Go to repo **Settings** → **Secrets and variables** → **Actions** and add:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

This enables the GitHub Actions cron job as a backup for daily broadcasts.

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions |
| `/today` | Get today's two halachot |
| `/about` | About the bot and sources |
| `/help` | Help and usage information |

## 🏗️ Architecture

```
likutei-halachot-yomi/
├── src/
│   ├── bot.py           # Telegram bot with polling
│   ├── sefaria.py       # Sefaria API client
│   ├── selector.py      # Deterministic halacha selection
│   └── formatter.py     # Message formatting (HTML)
├── scripts/
│   └── run_polling.py   # Bot entry point
├── main.py              # Daily broadcast CLI
├── Dockerfile           # Container build
├── railway.toml         # Railway deployment config
└── .github/workflows/
    ├── daily.yml        # Backup daily broadcast (cron)
    └── ci.yml           # Tests & linting
```

## 📖 About Likutei Halachot

**Likutei Halachot** ("Collected Laws") was written by Rebbe Natan of Breslov (1780-1844), the primary student of Rebbe Nachman. It reveals mystical depths within the Shulchan Aruch, connecting practical law to spiritual insight.

**Sections:**
- **Orach Chaim** — Daily life, prayer, Shabbat, holidays
- **Yoreh Deah** — Dietary laws, charity, Torah study
- **Even HaEzer** — Marriage and family
- **Choshen Mishpat** — Civil and monetary law

Texts sourced from [Sefaria.org](https://www.sefaria.org/Likutei_Halakhot).

## 🧪 Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Preview today's message
python main.py --preview

# Run bot locally
python scripts/run_polling.py
```

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

<div align="center">

**נ נח נחמ נחמן מאומן**

*Spreading the light of Rebbe Nachman's teachings, one halacha at a time*

</div>
