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

### 3. Add GitHub Secrets

1. Fork this repo
2. Go to your fork's **Settings** → **Secrets and variables** → **Actions**
3. Add two secrets:
   - `TELEGRAM_BOT_TOKEN` — Your bot token from @BotFather
   - `TELEGRAM_CHAT_ID` — Your chat ID from @userinfobot

### 4. Daily Broadcasts

Daily broadcasts run automatically via **GitHub Actions** at ~6:00 AM Israel time (4:00 AM UTC).

To test immediately: **Actions** → **Daily Halachot** → **Run workflow**

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message with instructions |
| `/today` | Get today's two halachot |
| `/about` | About the bot and sources |
| `/help` | Help and usage information |

### Troubleshooting

**Not receiving daily messages?**

1. **Check GitHub Actions** — Go to Actions tab, verify "Daily Halachot" workflow runs successfully
2. **Check secrets** — Ensure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set correctly
3. **Test manually** — Actions → Daily Halachot → Run workflow

**Want real-time commands?** (/start, /today, etc.)

Run locally:
```bash
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"
python scripts/run_polling.py
```

## 🏗️ Architecture

```
likutei-halachot-yomi/
├── src/
│   ├── bot.py           # Telegram bot with polling
│   ├── sefaria.py       # Sefaria API client
│   ├── selector.py      # Deterministic halacha selection
│   └── formatter.py     # Message formatting (HTML)
├── scripts/
│   └── run_polling.py   # Bot runner script (local dev)
├── main.py              # Daily broadcast CLI
└── .github/workflows/
    ├── daily.yml        # Daily 6 AM broadcast (cron)
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
