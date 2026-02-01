"""Broadcast state management to prevent duplicate daily broadcasts.

This module tracks the last broadcast date to ensure we only send
one broadcast per day, even if the workflow is triggered multiple times
(e.g., due to dual DST cron schedules or manual reruns).
"""

import json
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# State file path (same directory as subscribers.json)
STATE_DIR = Path(__file__).parent.parent / ".github" / "state"
BROADCAST_STATE_FILE = STATE_DIR / "broadcast_state.json"


def get_last_broadcast_date() -> date | None:
    """Get the date of the last successful broadcast."""
    if BROADCAST_STATE_FILE.exists():
        try:
            data = json.loads(BROADCAST_STATE_FILE.read_text())
            last_date_str = data.get("last_broadcast_date")
            if last_date_str:
                return date.fromisoformat(last_date_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to load broadcast state: {e}")
    return None


def set_last_broadcast_date(broadcast_date: date) -> None:
    """Record the date of a successful broadcast."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    BROADCAST_STATE_FILE.write_text(
        json.dumps({"last_broadcast_date": broadcast_date.isoformat()}, indent=2)
    )
    logger.info(f"Recorded broadcast date: {broadcast_date.isoformat()}")


def has_broadcast_today(target_date: date | None = None) -> bool:
    """Check if we've already broadcast for the given date (defaults to today).

    This is used to prevent duplicate broadcasts when multiple cron jobs
    trigger on the same day (e.g., dual DST schedules at 3am and 4am UTC).
    """
    if target_date is None:
        target_date = date.today()

    last_broadcast = get_last_broadcast_date()
    if last_broadcast and last_broadcast >= target_date:
        logger.info(
            f"Already broadcast on {last_broadcast.isoformat()}, "
            f"skipping for {target_date.isoformat()}"
        )
        return True
    return False


def mark_broadcast_complete(target_date: date | None = None) -> None:
    """Mark the broadcast as complete for the given date (defaults to today)."""
    if target_date is None:
        target_date = date.today()
    set_last_broadcast_date(target_date)
