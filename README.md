# Likutei Halachot Yomi 📚

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot that sends two random halachot from **Likutei Halachot** every day, featuring texts from Rebbe Nachman's teachings as compiled by Rebbe Natan of Breslov.

## ✨ Features

- **Daily Inspiration**: Two halachot delivered every day at 6 AM Israel time
- **Fresh Content**: Different selection each year (Jan 1, 2026 ≠ Jan 1, 2027)
- **Interactive Commands**: `/start`, `/today`, `/about`
- **Hebrew + English**: Original Hebrew text with English translation
- **Sefaria Links**: Direct links to continue learning
- **Rate Limited**: Protection against abuse (10 requests/user/minute)

## 🚀 Deployment

### Deploy to Vercel (Recommended - Free)

1. **Fork this repository**

2. **Go to [vercel.com](https://vercel.com)** and sign in with GitHub

3. **Import your forked repo**

4. **Add Environment Variables**:
   - `TELEGRAM_BOT_TOKEN` - from [@BotFather](https://t.me/botfather)
   - `TELEGRAM_CHAT_ID` - your chat/group ID

5. **Deploy!**

6. **Set the Telegram webhook** (one-time):
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://<YOUR_APP>.vercel.app/api/webhook"
   ```

That's it! The bot will respond to commands and GitHub Actions sends daily messages at 6 AM Israel time.

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/today` | Get today's halachot |
| `/about` | About the bot |

## 🏗️ Architecture

```
├── api/webhook.py      # Vercel serverless function (handles commands)
├── main.py             # CLI for daily broadcast (GitHub Actions)
├── src/
│   ├── bot.py          # Telegram bot logic
│   ├── sefaria.py      # Sefaria API client
│   ├── selector.py     # Halacha selection
│   └── formatter.py    # Message formatting
├── .github/workflows/
│   ├── daily.yml       # 6 AM Israel time broadcast
│   └── ci.yml          # Tests & linting
└── vercel.json         # Vercel config
```

## 📖 About Likutei Halachot

**Likutei Halachot** is written by Rebbe Natan of Breslov (1780-1844), providing mystical insights on the Shulchan Aruch through Rebbe Nachman's teachings.

Four sections:
- **Orach Chaim** - Daily conduct, prayer, Shabbat
- **Yoreh Deah** - Dietary laws, charity, Torah study
- **Even HaEzer** - Marriage and family
- **Choshen Mishpat** - Civil law

## 🔧 Local Development

```bash
# Install
pip install -r requirements.txt

# Preview today's message
python main.py --preview

# Run tests
pytest
```

## 📄 License

MIT License

---

<div align="center">

**נ נח נחמ נחמן מאומן**

*Spreading the light of Rebbe Nachman's teachings*

</div>
