# Likutei Halachot Yomi

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot delivering two daily halachot from **Likutei Halachot** by Rebbe Natan of Breslov, with optional Hebrew voice audio readings. Runs entirely on GitHub Actions — no server required.

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + today's halachot + voice audio (auto-subscribes) |
| `/today` | Today's two halachot + voice audio |
| `/info` | About the bot, sources, and usage |
| `/subscribe` | Subscribe to daily broadcasts |
| `/unsubscribe` | Unsubscribe from daily broadcasts |

Commands have up to 5-minute response latency due to GitHub Actions polling.

## Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Add GitHub Secrets: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

The bot will automatically send daily broadcasts at 6 AM Israel time and respond to commands every 5 minutes.

### Voice Audio (Optional)

Hebrew voice readings use Google Cloud Text-to-Speech (WaveNet). To enable:

1. Enable the [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com) in a GCP project
2. Create a service account and download the JSON key
3. Add GitHub Secrets:
   - `GOOGLE_TTS_ENABLED` = `true`
   - `GOOGLE_TTS_CREDENTIALS_JSON` = full JSON key content (single line)

Voice messages are sent as Telegram voice notes with built-in 1x/1.5x/2x speed controls. Audio is cached to avoid redundant API calls. TTS failure never blocks text delivery.

## Architecture

```
src/
├── models.py         # Data classes
├── sefaria.py        # Sefaria API client
├── selector.py       # Deterministic halacha selection
├── formatter.py      # HTML message formatting
├── commands.py       # Command message generation
├── tts.py            # Hebrew text-to-speech (Google Cloud TTS)
├── subscribers.py    # Subscriber management
├── config.py         # Environment config
└── unified/
    └── publisher.py  # Multi-channel publishing
scripts/
├── poll_commands.py  # Command polling (GitHub Actions)
├── test_tts.py       # Manual TTS test script
└── run_polling.py    # Local development
main.py               # Daily broadcast entry point
```

### Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `ci.yml` | Push/PR to main | Lint, type check, and test |
| `daily.yml` | 6 AM Israel time | Send daily halachot broadcast + voice |
| `poll-commands.yml` | Every 5 minutes | Respond to user commands + voice |

## Development

```bash
pip install -r requirements.txt
pytest                           # Run tests
python main.py --preview         # Preview today's message
python scripts/run_polling.py    # Local command polling
python scripts/test_tts.py       # Test TTS pipeline
```

## About Likutei Halachot

**Likutei Halachot** was written by Rebbe Natan of Breslov (1780-1844), the primary student of Rebbe Nachman. It connects practical Jewish law to spiritual insight across four sections: Orach Chaim, Yoreh Deah, Even HaEzer, and Choshen Mishpat.

Texts sourced from [Sefaria.org](https://www.sefaria.org/Likutei_Halakhot).

## License

MIT

---

<div align="center">

**נ נח נחמ נחמן מאומן**

</div>
