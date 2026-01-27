# Likutei Halachot Yomi 📚

[![CI](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/ci.yml)
[![Daily](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml/badge.svg)](https://github.com/naorbrown/likutei-halachot-yomi/actions/workflows/daily.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Telegram bot that sends two random halachot from **Likutei Halachot** every day, featuring texts from Rebbe Nachman's teachings as compiled by Rebbe Natan of Breslov.

## ✨ Features

- **Daily Inspiration**: Two halachot delivered every day at 6 AM Israel time
- **Two Different Volumes**: Each day's halachot come from two different sections (Orach Chaim, Yoreh Deah, Even HaEzer, or Choshen Mishpat)
- **Hebrew + English**: Original Hebrew text with English translation when available
- **Sefaria Links**: Direct links to continue learning on Sefaria
- **Deterministic Selection**: Same date always produces the same halachot (reproducible)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Chat ID where messages should be sent

### Installation

```bash
# Clone the repository
git clone https://github.com/naorbrown/likutei-halachot-yomi.git
cd likutei-halachot-yomi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your bot token and chat ID
```

### Usage

```bash
# Preview today's message (no Telegram required)
python main.py --preview

# Send daily message to configured chat
python main.py

# Run interactive bot (responds to commands)
python main.py --serve
```

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message and introduction |
| `/today` | Get today's two halachot |
| `/about` | Information about the bot and Likutei Halachot |

## 🏗️ Architecture

```
likutei-halachot-yomi/
├── main.py              # Entry point
├── src/
│   ├── bot.py           # Telegram bot implementation
│   ├── config.py        # Configuration management
│   ├── formatter.py     # Message formatting
│   ├── models.py        # Data models
│   ├── selector.py      # Halacha selection logic
│   └── sefaria.py       # Sefaria API client
├── data/
│   └── sections.json    # Catalog of available sections
├── tests/               # Test suite
└── .github/workflows/   # CI/CD pipelines
```

## 📖 About Likutei Halachot

**Likutei Halachot** (ליקוטי הלכות) is a foundational text of Breslov Chassidut written by Rebbe Natan of Breslov (1780-1844), the foremost disciple of Rebbe Nachman of Uman. The work provides deep mystical insights on the Shulchan Aruch (Code of Jewish Law) through the lens of Rebbe Nachman's teachings.

The work is divided into four sections following the structure of the Shulchan Aruch:

- **Orach Chaim** (אורח חיים) - Daily conduct, prayer, Shabbat, holidays
- **Yoreh Deah** (יורה דעה) - Dietary laws, vows, charity, Torah study
- **Even HaEzer** (אבן העזר) - Marriage and family law
- **Choshen Mishpat** (חושן משפט) - Civil and monetary law

## 🔧 Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run linter
ruff check src/ tests/

# Format code
black src/ tests/

# Type check
mypy src/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Sefaria](https://www.sefaria.org/) for providing free access to Jewish texts
- The Breslov community for preserving and spreading these teachings

---

<div align="center">

**נ נח נחמ נחמן מאומן**

*Spreading the light of Rebbe Nachman's teachings*

</div>
