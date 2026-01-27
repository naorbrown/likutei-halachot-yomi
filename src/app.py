"""
Main application for Likutei Halachot Yomi bot.
"""

import asyncio
import logging
import sys
from datetime import date
from typing import Optional

from .config import Config, get_config
from .hebrew_calendar import get_hebrew_date, HebrewDate
from .schedule import ScheduleManager, DailyPortion
from .sefaria_client import get_sefaria_client, SefariaText
from .message_formatter import MessageFormatter
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)


def setup_logging(config: Config):
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format=config.log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.logs_dir / "bot.log", encoding="utf-8"),
        ],
    )


class LikuteiHalachotYomiApp:
    """Main application class."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.schedule_manager = ScheduleManager(self.config.data_dir)
        self.sefaria_client = get_sefaria_client()
        self.formatter = MessageFormatter(
            max_length=self.config.max_message_length,
            include_footer=True,
        )
        self.telegram_bot = TelegramBot(self.config)

    async def run(self, gregorian_date: Optional[date] = None) -> bool:
        """
        Run the daily bot - fetch portions and send to Telegram.

        Args:
            gregorian_date: Override date (for testing)

        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("Likutei Halachot Yomi Bot Starting")
        logger.info("=" * 60)

        # Get Hebrew date
        hebrew_date = get_hebrew_date(gregorian_date)
        logger.info(f"Hebrew Date: {hebrew_date}")

        # Get daily portions
        portions = self.schedule_manager.get_daily_portions(hebrew_date)
        logger.info(f"Found {len(portions)} portions for today")

        if not portions:
            logger.warning("No portions found for today")

        # Fetch texts from Sefaria
        sefaria_texts = []
        for portion in portions:
            logger.info(f"Fetching: {portion.ref}")
            text = self.sefaria_client.get_text(portion.ref)
            if text:
                logger.info(f"  Got: {text.he_ref}")
            else:
                logger.warning(f"  Failed to fetch: {portion.ref}")
            sefaria_texts.append(text)

        # Format messages
        messages = self.formatter.format_daily_message(
            hebrew_date=hebrew_date,
            portions=portions,
            sefaria_texts=sefaria_texts,
        )

        logger.info(f"Formatted {len(messages)} message(s)")

        # Send to Telegram
        if self.config.telegram_bot_token == "test_token":
            logger.info("Test mode - not sending to Telegram")
            logger.info("Message preview:")
            for msg in messages:
                logger.info(f"\n{msg.text[:500]}...")
            return True

        success = await self.telegram_bot.send_formatted_messages(messages)

        if success:
            logger.info("Daily Likutei Halachot sent successfully!")
        else:
            logger.error("Failed to send daily Likutei Halachot")

        return success

    def preview(self, gregorian_date: Optional[date] = None) -> str:
        """
        Generate a preview of today's portion without sending.

        Args:
            gregorian_date: Override date (for testing)

        Returns:
            Preview text
        """
        hebrew_date = get_hebrew_date(gregorian_date)
        portions = self.schedule_manager.get_daily_portions(hebrew_date)

        return self.formatter.format_test_message(hebrew_date, portions)


async def main():
    """Main entry point."""
    config = get_config()
    setup_logging(config)

    app = LikuteiHalachotYomiApp(config)
    success = await app.run()

    return 0 if success else 1


def run():
    """Synchronous entry point for command line."""
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
