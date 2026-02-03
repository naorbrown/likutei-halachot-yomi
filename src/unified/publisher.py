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

# Rate limiting
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


def format_for_unified_channel(content: str) -> str:
    """Format message with unified channel header.

    Args:
        content: Original message content

    Returns:
        Formatted message with header
    """
    header = f"{BADGE}\n{'─' * 30}\n\n"
    return f"{header}{content}"


def is_unified_channel_enabled() -> bool:
    """Check if unified channel publishing is enabled."""
    return PUBLISH_ENABLED and bool(UNIFIED_CHANNEL_ID) and bool(UNIFIED_BOT_TOKEN)


class TorahYomiPublisher:
    """Publisher for the unified Torah Yomi channel."""

    def __init__(self) -> None:
        """Initialize publisher."""
        pass  # Stateless - Bot created fresh each call with proper lifecycle

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

        if not UNIFIED_BOT_TOKEN:
            logger.error("No bot token configured")
            return False

        formatted_text = format_for_unified_channel(text)

        # Use async context manager for proper Bot lifecycle (required in v20+)
        bot = Bot(token=UNIFIED_BOT_TOKEN)
        async with bot:
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

        if not UNIFIED_BOT_TOKEN:
            return {"success": 0, "failed": len(messages)}

        success = 0
        failed = 0

        # Use single Bot context for all messages (more efficient)
        bot = Bot(token=UNIFIED_BOT_TOKEN)
        async with bot:
            for msg in messages:
                formatted_text = format_for_unified_channel(msg)
                try:
                    await bot.send_message(
                        chat_id=UNIFIED_CHANNEL_ID,
                        text=formatted_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )
                    success += 1
                except TelegramError as e:
                    logger.error(f"Batch publish failed for message: {e}")
                    failed += 1
                # Rate limiting between messages
                await asyncio.sleep(0.1)

        return {"success": success, "failed": failed}


# Convenience function
async def publish_text_to_unified_channel(text: str, **kwargs: Any) -> bool:
    """Convenience function to publish text."""
    publisher = TorahYomiPublisher()
    return await publisher.publish_text(text, **kwargs)
