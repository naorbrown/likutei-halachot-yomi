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

### 3. Deploy (Choose One)

#### Option A: Render (Recommended)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Fork this repo
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your forked repo
4. Add environment variables:
   - `TELEGRAM_BOT_TOKEN` — Your bot token
   - `TELEGRAM_CHAT_ID` — Your chat ID
5. Deploy!

#### Option B: Self-Host

```bash
git clone https://github.com/naorbrown/likutei-halachot-yomi.git
cd likutei-halachot-yomi
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run the bot
python scripts/run_polling.py
```

### 4. Daily Broadcasts

Daily broadcasts are handled automatically by the Render worker at **6:00 AM Israel time**. The bot uses python-telegram-bot's built-in job scheduler for precise timing.

For manual testing/recovery, you can trigger broadcasts via GitHub Actions:
- Go to Actions → Daily Halachot → Run workflow

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
│   └── run_polling.py   # Bot runner script
├── main.py              # Daily broadcast CLI
├── render.yaml          # Render deployment config
└── .github/workflows/
    ├── daily.yml        # Manual broadcast trigger
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
