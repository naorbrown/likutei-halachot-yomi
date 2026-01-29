"""Torah Yomi Unified Channel Publisher for Likutei Halachot Bot.

Publishes content to the unified Torah Yomi channel.
Handles rate limiting, retries, and proper message formatting.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# Configuration from environment
UNIFIED_CHANNEL_ID = os.getenv("TORAH_YOMI_CHANNEL_ID")
UNIFIED_BOT_TOKEN = os.getenv("TORAH_YOMI_CHANNEL_BOT_TOKEN")
PUBLISH_ENABLED = os.getenv("TORAH_YOMI_PUBLISH_ENABLED", "true").lower() == "true"

# Source configuration
SOURCE = "likutei_halachot"
BADGE = "📜 Likutei Halachot | ליקוטי הלכות"
BOT_USERNAME = "LikuteiHalachotBot"

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


def format_for_unified_channel(content: str) -> str:
    """Format message with unified channel header/footer.

    Args:
        content: Original message content

    Returns:
        Formatted message with header and footer
    """
    header = f"{BADGE}\n{'─' * 30}\n\n"
    footer = f"\n\n{'━' * 30}\n🔗 @{BOT_USERNAME}"
    return f"{header}{content}{footer}"


def is_unified_channel_enabled() -> bool:
    """Check if unified channel publishing is enabled."""
    return PUBLISH_ENABLED and bool(UNIFIED_CHANNEL_ID) and bool(UNIFIED_BOT_TOKEN)


class TorahYomiPublisher:
    """Publisher for the unified Torah Yomi channel."""

    def __init__(self) -> None:
        """Initialize publisher."""
        self._bot: Bot | None = None

    def _get_bot(self) -> Bot | None:
        """Get or create the bot instance."""
        if self._bot is None and UNIFIED_BOT_TOKEN:
            self._bot = Bot(token=UNIFIED_BOT_TOKEN)
        return self._bot

    async def publish_text(
        self,
        text: str,
        *,
        parse_mode: str = ParseMode.HTML,
        disable_web_page_preview: bool = True,
        **kwargs: Any,
    ) -> bool:
        """Publish a text message to the unified channel.

        Args:
            text: Message text
            parse_mode: Telegram parse mode
            disable_web_page_preview: Whether to disable link previews
            **kwargs: Additional options for send_message

        Returns:
            True if successful, False otherwise
        """
        if not is_unified_channel_enabled():
            logger.debug("Unified channel publish disabled or not configured")
            return False

        bot = self._get_bot()
        if not bot:
            logger.error("No bot token configured")
            return False

        formatted_text = format_for_unified_channel(text)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await bot.send_message(
                    chat_id=UNIFIED_CHANNEL_ID,
                    text=formatted_text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    **kwargs,
                )
                logger.info(f"Published text to unified channel ({SOURCE})")
                return True
            except TelegramError as e:
                logger.error(f"Publish attempt {attempt} failed: {e}")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY * attempt)

        logger.error("All publish attempts failed")
        return False

    async def publish_batch(self, messages: list[str]) -> dict[str, int]:
        """Publish multiple text messages with rate limiting.

        Args:
            messages: List of message texts

        Returns:
            Dictionary with success and failed counts
        """
        if not is_unified_channel_enabled():
            return {"success": 0, "failed": 0}

        success = 0
        failed = 0

        for msg in messages:
            if await self.publish_text(msg):
                success += 1
            else:
                failed += 1
            # Rate limiting between messages
            await asyncio.sleep(0.1)

        return {"success": success, "failed": failed}


# Convenience function
async def publish_text_to_unified_channel(text: str, **kwargs: Any) -> bool:
    """Convenience function to publish text."""
    publisher = TorahYomiPublisher()
    return await publisher.publish_text(text, **kwargs)
