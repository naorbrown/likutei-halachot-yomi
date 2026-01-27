<p align="center">
  <img src="bot_logo.png" alt="Likutei Halachot Yomi" width="400">
</p>

<h1 align="center">ליקוטי הלכות יומי</h1>

<p align="center">
  <strong>Daily wisdom from Reb Noson of Breslov, delivered to your Telegram.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#free-hosting">Free Hosting</a> •
  <a href="#about">About</a>
</p>

---

Every day, receive the Hebrew text of **Likutei Halachot** — Reb Noson's masterwork that reveals the hidden light within every halacha. Each law becomes a doorway to deeper understanding, connecting the revealed Torah to the inner teachings of Rebbe Nachman.

## Features

- **Automatic Hebrew Calendar** — Knows today's Hebrew date, handles leap years
- **Complete Yearly Cycle** — 635 chapters distributed across all 12 months
- **Direct from Sefaria** — Full Hebrew text with links to continue learning
- **Beautiful Formatting** — Clean Telegram messages, auto-splits long texts
- **100% Free** — Runs on GitHub Actions, no server costs
- **Zero Maintenance** — Set it once, receive daily Torah forever

## Quick Start

### 1. Create Your Bot

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the prompts
3. Save your bot token

### 2. Get Your Chat ID

1. Message your new bot (say anything)
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}` — that number is your chat ID

### 3. Fork & Configure

1. Fork this repository
2. Go to **Settings → Secrets and variables → Actions**
3. Add two secrets:
   - `TELEGRAM_BOT_TOKEN` — your bot token
   - `TELEGRAM_CHAT_ID` — your chat ID

### 4. Enable the Workflow

1. Go to **Actions** tab
2. Enable workflows if prompted
3. That's it — you'll receive Likutei Halachot every morning at 6 AM Israel time

### Manual Test

To test immediately, go to **Actions → Daily Likutei Halachot → Run workflow**.

---

## Free Hosting

This bot runs entirely free using **GitHub Actions**:

- **2,000 minutes/month** free for private repos
- **Unlimited** for public repos
- Each run takes ~30 seconds
- No server, no costs, no maintenance

The workflow runs daily at 4:00 AM UTC (6:00 AM Israel time).

---

## Local Development

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/likutei-halachot-yomi.git
cd likutei-halachot-yomi

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Preview today's portion
python run.py --preview

# Send to Telegram
python run.py
```

### CLI Options

```
python run.py [OPTIONS]

  --preview           Preview without sending
  --test              Test mode (no Telegram)
  --date YYYY-MM-DD   Override the date
  --verbose, -v       Debug logging
```

---

## Project Structure

```
├── src/
│   ├── app.py               # Main application
│   ├── config.py            # Configuration
│   ├── hebrew_calendar.py   # Hebrew date handling
│   ├── message_formatter.py # Telegram formatting
│   ├── schedule.py          # Learning schedule
│   ├── sefaria_client.py    # Sefaria API
│   └── telegram_bot.py      # Telegram integration
├── data/
│   └── schedule.json        # Daily schedule
├── .github/workflows/
│   └── daily.yml            # GitHub Actions
├── run.py                   # Entry point
└── requirements.txt
```

---

## The Schedule

The bot cycles through all of Likutei Halachot:

| Section | Topics | Chapters |
|---------|--------|----------|
| **Orach Chaim** | Prayer, Shabbat, Holidays | ~280 |
| **Yoreh Deah** | Kashrus, Purity, Ritual | ~200 |
| **Even HaEzer** | Marriage, Family | ~80 |
| **Choshen Mishpat** | Civil Law, Business | ~75 |

635 chapters across 355 days of the Hebrew year.

---

## About Likutei Halachot

<img align="right" src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Rebbe_Nachman_of_Breslov.jpg/220px-Rebbe_Nachman_of_Breslov.jpg" width="150">

**Likutei Halachot** (ליקוטי הלכות) was written by **Reb Noson of Breslov** (1780–1844), the primary disciple of Rebbe Nachman of Breslov.

This eight-volume masterwork follows the structure of the Shulchan Aruch, but reveals the soul within each law. Every halacha becomes illuminated through the teachings of Rebbe Nachman, connecting the practical to the mystical.

> *"סִפְרֵי לִקּוּטֵי הֲלָכוֹת שֶׁלִּי הֵם הַגַּן עֵדֶן בְּעַצְמוֹ"*
>
> "My Likutei Halachot books are the Garden of Eden itself."
>
> — Reb Noson of Breslov

---

## Contributing

Found a bug? Have a suggestion? Open an issue or PR.

## Acknowledgments

- [Sefaria](https://www.sefaria.org/) for free access to Jewish texts
- The Breslov community for preserving these teachings

## License

MIT — Use freely, spread Torah.

---

<p align="center">
  <em>נ נח נחמ נחמן מאומן</em>
</p>
