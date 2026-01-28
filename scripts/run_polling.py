#!/usr/bin/env python3
"""Run the bot in polling mode for interactive commands."""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

from src.bot import LikuteiHalachotBot
from src.config import Config

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the bot in polling mode."""
    try:
        logger.info("Loading configuration...")
        config = Config.from_env()
        logger.info("Configuration loaded successfully")

        logger.info("Initializing bot...")
        bot = LikuteiHalachotBot(config)
        logger.info("Bot initialized, starting polling...")

        bot.run_polling()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
