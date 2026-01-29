"""Command logic for Telegram bot.

This module provides the core command logic that can be used by both:
- bot.py (Application framework handlers)
- poll_commands.py (Stateless GitHub Actions polling)

Simplified commands:
- /start: Welcome + today's content (entry point for new users)
- /today: Just today's content (for returning users)
- /info: Combined about + help information
"""

from __future__ import annotations

import logging
from datetime import date

from .formatter import (
    format_daily_message,
    format_error_message,
    format_info_message,
    format_welcome_message,
)
from .selector import HalachaSelector

logger = logging.getLogger(__name__)


def get_start_messages(
    selector: HalachaSelector, for_date: date | None = None
) -> list[str]:
    """Get messages for /start command (welcome + daily content).

    Used for new users or first interaction.

    Args:
        selector: HalachaSelector instance for fetching daily pair
        for_date: Optional date override, defaults to today

    Returns:
        List of formatted messages: [welcome, content...]
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


def get_today_messages(
    selector: HalachaSelector, for_date: date | None = None
) -> list[str]:
    """Get messages for /today command (just daily content, no welcome).

    Used for returning users who just want today's halachot.

    Args:
        selector: HalachaSelector instance for fetching daily pair
        for_date: Optional date override, defaults to today

    Returns:
        List of formatted content messages (no welcome)
    """
    if for_date is None:
        for_date = date.today()

    try:
        # Try cached messages first, skip welcome (first message)
        cached_messages = selector.get_cached_messages(for_date)
        if cached_messages and len(cached_messages) > 1:
            logger.debug(f"Using cached content for {for_date}")
            return cached_messages[1:]  # Skip welcome message

        # Fall back to fetching and formatting
        pair = selector.get_daily_pair(for_date)
        if pair:
            return format_daily_message(pair, for_date)
        else:
            logger.warning(f"No daily pair available for {for_date}")
            return [format_error_message()]
    except Exception as e:
        logger.exception(f"Error getting daily pair: {e}")
        return [format_error_message()]


def get_info_message() -> str:
    """Get message for /info command (combined about + help)."""
    return format_info_message()


def get_error_message() -> str:
    """Get generic error message."""
    return format_error_message()


# Backwards compatibility aliases
def get_daily_messages(
    selector: HalachaSelector, for_date: date | None = None
) -> list[str]:
    """Deprecated: Use get_start_messages instead."""
    return get_start_messages(selector, for_date)


def get_about_message() -> str:
    """Deprecated: Use get_info_message instead."""
    return get_info_message()


def get_help_message() -> str:
    """Deprecated: Use get_info_message instead."""
    return get_info_message()
