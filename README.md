# Likutei Halachot Yomi

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot that sends two daily halachot from **Likutei Halachot** by Rebbe Natan of Breslov, with optional Hebrew voice audio readings. Runs entirely on GitHub Actions — no server, no hosting costs, no maintenance.

## What You Get

- **Two halachot every morning** at 6 AM Israel time, delivered as text messages with links to [Sefaria.org](https://www.sefaria.org/Likutei_Halakhot)
- **Hebrew voice readings** (optional) — native pronunciation with playback speed controls
- **On-demand access** — send `/today` anytime to get the day's halachot
- **Personal subscriptions** — users can subscribe to receive broadcasts directly
- **Completely free** — runs on GitHub's free tier with zero ongoing costs

---

## Setup Guide

No coding experience needed. The entire setup takes about 10 minutes using only your web browser.

### What You'll Need

- A **Telegram** account (the messaging app — [download here](https://telegram.org/) if you don't have it)
- A **GitHub** account (free — [sign up here](https://github.com/signup) if you don't have one)
- *(Optional)* A **Google** account, if you want voice audio readings

---

### Step 1: Create a Telegram Bot

A "bot" is an automated Telegram account that sends messages on your behalf.

1. Open Telegram and search for **@BotFather** (this is Telegram's official tool for making bots)
2. Tap **Start**, then send the message `/newbot`
3. BotFather will ask you to choose a **name** for your bot (this is what people see, e.g. "My Halachot Bot")
4. Then it will ask for a **username** (must end in `bot`, e.g. `my_halachot_bot`)
5. BotFather will reply with a message containing your **bot token** — it looks something like `7123456789:AAHx9kLmN...`

> **Important:** Copy this token and save it somewhere safe. You'll need it in Step 4. Don't share it publicly — anyone with this token can control your bot.

---

### Step 2: Get Your Chat ID

Your "chat ID" tells the bot where to send messages.

1. Open Telegram and search for **@userinfobot**
2. Tap **Start** — it will reply with your **ID** (a number like `123456789`)
3. Copy this number — you'll need it in Step 4

<details>
<summary><strong>Want to send to a Telegram channel instead?</strong></summary>

If you want the bot to post to a public or private channel:

1. Create a Telegram channel (or use an existing one)
2. Go to the channel settings and **add your bot as an administrator** (it needs permission to post messages)
3. To find the channel's ID: forward any message from the channel to **@userinfobot** — it will show the channel ID (starts with `-100...`, e.g. `-1001234567890`)
4. Use this channel ID instead of your personal chat ID in Step 4

</details>

---

### Step 3: Copy This Project to Your GitHub

"Forking" a project on GitHub means creating your own personal copy that you control.

1. Make sure you're signed in to [GitHub](https://github.com)
2. Go to the top of [this project's page](https://github.com/naorbrown/likutei-halachot-yomi)
3. Click the **Fork** button (near the top-right of the page)
4. On the next screen, just click **Create fork** — the default settings are fine
5. After a few seconds, you'll be on your own copy of the project

---

### Step 4: Add Your Bot Settings

GitHub "secrets" are private settings that are stored encrypted — only your automated tasks can read them.

1. In your forked project on GitHub, click the **Settings** tab (near the top of the page)
2. In the left sidebar, click **Secrets and variables**, then click **Actions**
3. Click the green **New repository secret** button
4. Add your first secret:
   - **Name:** `TELEGRAM_BOT_TOKEN`
   - **Secret:** Paste the bot token you saved from Step 1
   - Click **Add secret**
5. Click **New repository secret** again and add your second secret:
   - **Name:** `TELEGRAM_CHAT_ID`
   - **Secret:** Paste the chat ID (or channel ID) from Step 2
   - Click **Add secret**

| Secret name | What to paste |
|---|---|
| `TELEGRAM_BOT_TOKEN` | The bot token from BotFather (Step 1) |
| `TELEGRAM_CHAT_ID` | Your chat ID or channel ID (Step 2) |

**Your bot is now live!** It will start sending daily halachot at 6 AM Israel time and respond to commands within 5 minutes.

---

### Step 5: Add Voice Audio (Optional)

Voice readings use Google Cloud Text-to-Speech to generate native Hebrew audio. The free tier allows 1 million characters per month — far more than this bot will ever use.

<details>
<summary><strong>Click here to expand the voice setup instructions</strong></summary>

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and sign in with your Google account
2. If prompted, agree to the terms of service
3. Click **Select a project** at the top of the page, then click **New Project**
   - Give it any name (e.g. "halachot-bot") and click **Create**
4. In the search bar at the top, type **Text-to-Speech API** and select it from the results
5. Click the blue **Enable** button
6. Now you need to create a "service account" (a special login for your bot):
   - In the search bar, type **Service Accounts** and select **IAM & Admin > Service Accounts**
   - Click **Create Service Account**
   - Give it any name (e.g. "tts-bot") and click **Create and Continue**
   - Skip the optional permissions steps — just click **Done**
7. Click on the service account you just created
8. Go to the **Keys** tab
9. Click **Add Key** > **Create new key** > select **JSON** > click **Create**
10. A `.json` file will download to your computer — this is your credentials file
11. Open the downloaded file with any text editor (Notepad, TextEdit, etc.), select everything inside, and copy it
12. Back in your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**
13. Add two new secrets:

| Secret name | What to paste |
|---|---|
| `GOOGLE_TTS_ENABLED` | `true` |
| `GOOGLE_TTS_CREDENTIALS_JSON` | The entire contents of the JSON file you copied |

Voice messages will now accompany every text delivery — daily broadcasts and on-demand commands.

</details>

---

### Step 6: Verify Everything Works

Your bot runs automatically, but here's how to check that it's working:

**Option A: Send a command**
- Open Telegram and find your bot by its username
- Send `/start` — you should receive a welcome message and today's halachot within 5 minutes

**Option B: Check the Actions tab**
- In your GitHub repository, click the **Actions** tab
- You should see recent runs of "Daily Broadcast" and "Poll Commands"
- A green checkmark means it ran successfully

**Option C: Wait for the daily broadcast**
- At 6 AM Israel time, your bot will send that day's halachot to the chat ID you configured

> If nothing happens, see the [Troubleshooting](#troubleshooting) section below.

---

## Bot Commands

Send these commands to your bot in Telegram:

| Command | What it does |
|---|---|
| `/start` | Welcome message + today's halachot + voice (auto-subscribes to daily broadcasts) |
| `/today` | Today's two halachot + voice |
| `/info` | About the bot, sources, and available commands |
| `/subscribe` | Subscribe to daily 6 AM broadcasts |
| `/unsubscribe` | Stop receiving daily broadcasts |

> **Note:** Commands are processed every 5 minutes, so there may be a short delay before you get a response.

---

## How It Works

Every morning at 6 AM Israel time, GitHub automatically runs the bot. It picks two teachings from different volumes of Likutei Halachot (using the [Sefaria](https://www.sefaria.org/Likutei_Halakhot) library), formats them as messages with links to the original text, and sends them to your Telegram chat or channel. If voice is enabled, it also generates Hebrew audio and sends voice messages.

The bot also checks for new commands every 5 minutes. When someone sends `/start` or `/today`, it responds with today's halachot. Users who send `/start` are automatically subscribed to the daily broadcast.

The same two halachot are selected for everyone on any given day — the selection is tied to the date, so it's consistent and reproducible.

---

## Troubleshooting

<details>
<summary><strong>I'm not getting any messages</strong></summary>

1. **Check your secrets:** Go to Settings > Secrets and variables > Actions and make sure both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
2. **Check the Actions tab:** Click Actions in your repository. If you see red X marks, click on the failed run to see what went wrong
3. **Verify the chat ID:** Make sure you copied the correct number from @userinfobot. If sending to a channel, make sure the bot is added as an admin
4. **Check the token:** Make sure you copied the full bot token from BotFather, including the numbers before the colon

</details>

<details>
<summary><strong>Commands aren't working</strong></summary>

- Commands are checked every 5 minutes, so wait at least 5 minutes after sending a command
- Make sure you're sending commands directly to your bot (not in a group)
- Check the Actions tab — the "Poll Commands" workflow should be running every 5 minutes

</details>

<details>
<summary><strong>Voice messages aren't playing</strong></summary>

- Verify `GOOGLE_TTS_ENABLED` is set to exactly `true` (lowercase)
- Verify `GOOGLE_TTS_CREDENTIALS_JSON` contains the full JSON file contents
- Check the Actions tab for error messages mentioning TTS
- Voice failures won't block text delivery — you'll still get the text messages

</details>

<details>
<summary><strong>I want to change the delivery time</strong></summary>

The bot is set to deliver at 6 AM Israel time. To change this:

1. In your repository, open `.github/workflows/daily.yml`
2. Find the `cron` lines near the top (e.g. `'0 3 * * *'`)
3. Adjust the UTC times. Israel is UTC+2 in winter, UTC+3 in summer
4. Also update the `is_broadcast_hour()` check in `main.py` to match

</details>

<details>
<summary><strong>How do I get new features and updates?</strong></summary>

When the original project gets improvements, you can pull them into your fork:

1. Go to your fork on GitHub
2. You'll see a message like "This branch is X commits behind naorbrown:main"
3. Click **Sync fork** > **Update branch**
4. Your bot will automatically use the updated code on its next run

</details>

---

<details>
<summary><h2>For Developers</h2></summary>

### Architecture

```
src/
├── models.py         # Data classes (Halacha, DailyPair, HalachaSection)
├── sefaria.py        # Sefaria API client
├── selector.py       # Deterministic daily halacha selection + caching
├── formatter.py      # HTML message formatting + text splitting
├── commands.py       # Command text generation (/start, /today, /info)
├── tts.py            # Hebrew text-to-speech (Google Cloud TTS WaveNet)
├── subscribers.py    # Subscriber list management
├── config.py         # Environment variable configuration
└── unified/
    └── publisher.py  # Multi-channel publishing (Torah Yomi unified channel)
scripts/
├── poll_commands.py  # Command polling (runs via GitHub Actions)
├── test_tts.py       # Manual TTS test script
└── run_polling.py    # Local development polling
main.py               # Daily broadcast entry point
```

### Workflows

| Workflow | Schedule | Purpose |
|---|---|---|
| `daily.yml` | 6 AM Israel time | Daily halachot broadcast + voice to channel and subscribers |
| `poll-commands.yml` | Every 5 minutes | Responds to user commands with text + voice |
| `ci.yml` | On push/PR to main | Linting, type checking, and 149 tests |

### Voice Pipeline

1. Hebrew text is split into chunks (max 1200 chars — nikud Hebrew is ~4 bytes/char, staying under Google's 5000-byte limit)
2. Each chunk is synthesized via Google Cloud TTS WaveNet (`he-IL-Wavenet-D` — native Hebrew male voice)
3. Multi-chunk audio is concatenated with 300ms silence gaps using pydub
4. Output: OGG Opus (Telegram's native voice message format)
5. Audio is cached in `data/cache/audio/` to avoid redundant API calls
6. TTS failure at any step is caught — text delivery is never blocked

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in your environment variables
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

# Preview today's message (no Telegram needed)
python main.py --preview

# Run the bot locally with live command polling
python scripts/run_polling.py

# Test the TTS pipeline
python scripts/test_tts.py

# Run the test suite
pytest
```

### Testing

The project has 149 tests covering:
- Unit tests for every module (models, formatter, selector, sefaria, commands, subscribers, TTS)
- End-to-end tests for subscriber lifecycle, broadcast delivery, command polling, API failure recovery, partial failures, and unified channel publishing
- CI runs black, ruff, mypy, and pytest on every push

</details>

---

## About Likutei Halachot

**Likutei Halachot** was written by Rebbe Natan of Breslov (1780-1844), the primary student of Rebbe Nachman of Breslov. It uniquely connects practical Jewish law (halacha) to deep spiritual insight across four volumes: Orach Chaim, Yoreh Deah, Even HaEzer, and Choshen Mishpat.

Texts sourced from [Sefaria.org](https://www.sefaria.org/Likutei_Halakhot).

## License

MIT

---

<div align="center">

**נ נח נחמ נחמן מאומן**

</div>
