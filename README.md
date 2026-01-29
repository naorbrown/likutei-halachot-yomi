# Likutei Halachot Yomi 📚

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot delivering two daily halachot from **Likutei Halachot** by Rebbe Natan of Breslov — spreading the light of Rebbe Nachman's teachings.

**The bot runs entirely on GitHub Actions — no server required!**

## ✨ Features

- **Daily Inspiration** — Two halachot delivered at 6 AM Israel time
- **Fresh Content** — Different selections each day, never recycling year over year
- **Interactive Commands** — `/start`, `/today`, `/about`, `/help`
- **Bilingual** — Hebrew text with English translation
- **Deep Links** — Direct Sefaria links to continue learning
- **Free Hosting** — Runs on GitHub Actions, no paid services needed

## 🚀 Quick Start

### 1. Create Your Bot
Talk to [@BotFather](https://t.me/botfather) on Telegram:
```
/newbot
```
Save the token you receive.

### 2. Get Your Chat ID
Add [@userinfobot](https://t.me/userinfobot) to your group or message it directly to get your chat ID.

### 3. Add GitHub Secrets

Go to repo **Settings** → **Secrets and variables** → **Actions** and add:
- `TELEGRAM_BOT_TOKEN` — Your bot token from BotFather
- `TELEGRAM_CHAT_ID` — Your chat ID

That's it! The bot will:
- Send daily broadcasts at 6 AM Israel time
- Respond to commands every 5 minutes

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions |
| `/today` | Get today's two halachot |
| `/about` | About the bot and sources |
| `/help` | Help and usage information |

> **Note**: Commands have up to 5-minute response latency due to the GitHub Actions polling interval.

## 🏗️ Architecture

```
likutei-halachot-yomi/
├── src/
│   ├── bot.py           # Bot logic and command handlers
│   ├── sefaria.py       # Sefaria API client
│   ├── selector.py      # Deterministic halacha selection
│   └── formatter.py     # Message formatting (HTML)
├── scripts/
│   ├── poll_commands.py # Command polling (GitHub Actions)
│   └── run_polling.py   # Local development
├── main.py              # Daily broadcast CLI
├── tests/
│   ├── test_bot.py      # Bot unit tests
│   ├── test_formatter.py
│   └── conftest.py      # Test fixtures
└── .github/
    ├── workflows/
    │   ├── daily.yml        # Daily broadcast (6 AM Israel time)
    │   ├── poll-commands.yml # Command polling (every 5 min)
    │   └── ci.yml           # Tests & linting
    └── state/
        └── last_update_id.json  # Tracks processed messages
```

### How It Works

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `daily.yml` | 6 AM Israel time | Send daily halachot broadcast |
| `poll-commands.yml` | Every 5 minutes | Respond to user commands |
| `ci.yml` | On push/PR | Run tests and linting |

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

# Test command polling locally
python scripts/poll_commands.py
```

## 📄 License

MIT License — feel free to use, modify, and distribute.

---

<div align="center">

**נ נח נחמ נחמן מאומן**

*Spreading the light of Rebbe Nachman's teachings, one halacha at a time*

</div>
