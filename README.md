# Likutei Halachot Yomi

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot delivering two daily halachot from **Likutei Halachot** by Rebbe Natan of Breslov. Runs entirely on GitHub Actions — no server required.

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + today's halachot (auto-subscribes) |
| `/today` | Today's two halachot |
| `/info` | About the bot, sources, and usage |
| `/subscribe` | Subscribe to daily broadcasts |
| `/unsubscribe` | Unsubscribe from daily broadcasts |

Commands have up to 5-minute response latency due to GitHub Actions polling.

## Setup

1. Create a bot via [@BotFather](https://t.me/botfather) on Telegram
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Add GitHub Secrets: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

The bot will automatically send daily broadcasts at 6 AM Israel time and respond to commands every 5 minutes.

## Architecture

```
src/
├── models.py         # Data classes
├── sefaria.py        # Sefaria API client
├── selector.py       # Deterministic halacha selection
├── formatter.py      # HTML message formatting
├── commands.py       # Command message generation
├── subscribers.py    # Subscriber management
├── config.py         # Environment config
└── unified/
    └── publisher.py  # Multi-channel publishing
scripts/
├── poll_commands.py  # Command polling (GitHub Actions)
└── run_polling.py    # Local development
main.py               # Daily broadcast entry point
```

### Workflows

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| `ci.yml` | Push/PR to main | Lint, type check, and test |
| `daily.yml` | 6 AM Israel time | Send daily halachot broadcast |
| `poll-commands.yml` | Every 5 minutes | Respond to user commands |

## Development

```bash
pip install -r requirements.txt
pytest                           # Run tests
python main.py --preview         # Preview today's message
python scripts/run_polling.py    # Local command polling
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
