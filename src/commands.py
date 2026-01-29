"""Command logic for Telegram bot.

This module provides the core command logic that can be used by both:
- bot.py (Application framework handlers)
- poll_commands.py (Stateless GitHub Actions polling)

By centralizing the logic here, we ensure consistent behavior and avoid duplication.
"""

from __future__ import annotations

import logging
from datetime import date

from .formatter import (
    format_about_message,
    format_daily_message,
    format_error_message,
    format_help_message,
    format_welcome_message,
)
from .selector import HalachaSelector

logger = logging.getLogger(__name__)


def get_daily_messages(
    selector: HalachaSelector, for_date: date | None = None
) -> list[str]:
    """Get messages for /start and /today commands.

    Returns a list of formatted messages including welcome message
    followed by daily content (or error message if unavailable).

    Uses pre-cached formatted messages when available for instant response.

    Args:
        selector: HalachaSelector instance for fetching daily pair
        for_date: Optional date override, defaults to today

    Returns:
        List of formatted messages to send
    """
    if for_date is None:
        for_date = date.today()

    try:
        # Try cached messages first for instant response
        cached_messages = selector.get_cached_messages(for_date)
        if cached_messages:
            logger.debug(f"Using cached messages for {for_date}")
            return cached_messages

        # Fall back to fetching and formatting
        messages = [format_welcome_message()]
        pair = selector.get_daily_pair(for_date)
        if pair:
            messages.extend(format_daily_message(pair, for_date))
        else:
            logger.warning(f"No daily pair available for {for_date}")
            messages.append(format_error_message())
        return messages
    except Exception as e:
        logger.exception(f"Error getting daily pair: {e}")
        return [format_welcome_message(), format_error_message()]


def get_about_message() -> str:
    """Get message for /about command."""
    return format_about_message()


def get_help_message() -> str:
    """Get message for /help command."""
    return format_help_message()


def get_error_message() -> str:
    """Get generic error message."""
    return format_error_message()
