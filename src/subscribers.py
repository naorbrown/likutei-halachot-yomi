"""Subscriber management for individual broadcasts.

This module tracks users who want to receive daily broadcasts directly
through the bot (in addition to or instead of the channel).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Subscribers file path
STATE_DIR = Path(__file__).parent.parent / ".github" / "state"
SUBSCRIBERS_FILE = STATE_DIR / "subscribers.json"


def load_subscribers() -> set[int]:
    """Load subscriber chat IDs from state file."""
    if SUBSCRIBERS_FILE.exists():
        try:
            data = json.loads(SUBSCRIBERS_FILE.read_text())
            return set(data.get("subscribers", []))
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning("Failed to load subscribers, starting fresh")
            return set()
    return set()


def save_subscribers(subscribers: set[int]) -> None:
    """Save subscriber chat IDs to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SUBSCRIBERS_FILE.write_text(
        json.dumps({"subscribers": sorted(subscribers)}, indent=2)
    )
    logger.info(f"Saved {len(subscribers)} subscribers")


def add_subscriber(chat_id: int) -> bool:
    """Add a subscriber. Returns True if newly added, False if already subscribed."""
    subscribers = load_subscribers()
    if chat_id in subscribers:
        return False
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    logger.info(f"Added subscriber: {chat_id}")
    return True


def remove_subscriber(chat_id: int) -> bool:
    """Remove a subscriber. Returns True if removed, False if wasn't subscribed."""
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        return False
    subscribers.discard(chat_id)
    save_subscribers(subscribers)
    logger.info(f"Removed subscriber: {chat_id}")
    return True


def is_subscribed(chat_id: int) -> bool:
    """Check if a chat ID is subscribed."""
    return chat_id in load_subscribers()


def get_subscriber_count() -> int:
    """Get the number of subscribers."""
    return len(load_subscribers())
