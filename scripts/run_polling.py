#!/usr/bin/env python3
"""Run the bot in polling mode for interactive commands."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot import LikuteiHalachotBot
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main() -> None:
    """Run the bot in polling mode."""
    config = Config.from_env()
    bot = LikuteiHalachotBot(config)
    bot.run_polling()


if __name__ == "__main__":
    main()
