"""
Telegram bot for sending Likutei Halachot Yomi.
"""

import asyncio
import logging
import re
from typing import List, Optional

from telegram import Bot, Update, BotCommand
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import Config
from .message_formatter import FormattedMessage

logger = logging.getLogger(__name__)


class TelegramBot:
    """Handles sending messages to Telegram."""

    def __init__(self, config: Config):
        self.config = config
        self.bot = Bot(token=config.telegram_bot_token)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = ParseMode.HTML,
    ) -> bool:
        """
        Send a message to Telegram.

        Args:
            text: Message text
            chat_id: Target chat ID (defaults to config)
            parse_mode: Message parse mode

        Returns:
            True if sent successfully
        """
        target_chat = chat_id or self.config.telegram_chat_id

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=False,
            )
            logger.info(f"Message sent successfully to {target_chat}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram error sending message: {e}")

            # Try sending without formatting if parsing failed
            if "can't parse" in str(e).lower():
                try:
                    await self.bot.send_message(
                        chat_id=target_chat,
                        text=self._strip_html(text),
                    )
                    logger.info("Message sent without formatting")
                    return True
                except TelegramError as e2:
                    logger.error(f"Failed to send plain text: {e2}")

            return False

    async def send_formatted_messages(
        self,
        messages: List[FormattedMessage],
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send multiple formatted messages.

        Args:
            messages: List of FormattedMessage objects
            chat_id: Target chat ID

        Returns:
            True if all messages sent successfully
        """
        success = True

        for i, message in enumerate(messages):
            result = await self.send_message(
                text=message.text,
                chat_id=chat_id,
                parse_mode=message.parse_mode,
            )

            if not result:
                success = False

            # Small delay between messages to avoid rate limiting
            if i < len(messages) - 1:
                await asyncio.sleep(0.5)

        return success

    async def setup_commands(self) -> bool:
        """Set up bot commands for the menu."""
        commands = [
            BotCommand("start", "התחל לקבל ליקוטי הלכות יומי"),
            BotCommand("today", "קבל את ההלכה של היום"),
            BotCommand("about", "אודות הבוט"),
            BotCommand("help", "עזרה"),
        ]
        try:
            await self.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
            return True
        except TelegramError as e:
            logger.error(f"Failed to set commands: {e}")
            return False

    def _strip_html(self, text: str) -> str:
        """Remove HTML formatting from text."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text

    async def test_connection(self) -> bool:
        """
        Test the Telegram bot connection.

        Returns:
            True if connection is working
        """
        try:
            me = await self.bot.get_me()
            logger.info(f"Connected to Telegram as @{me.username}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False
