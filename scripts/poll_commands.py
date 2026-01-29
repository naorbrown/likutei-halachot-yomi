#!/usr/bin/env python3
"""Poll Telegram for commands and respond.

This script is designed to run via GitHub Actions every 5 minutes.
It polls for new updates, handles commands, and persists state.

Simplified commands:
- /start: Welcome + today's content (entry point)
- /today: Just today's content (no welcome)
- /info: Combined about + help
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.commands import (
    get_error_message,
    get_info_message,
    get_start_messages,
    get_today_messages,
)
from src.config import Config
from src.sefaria import SefariaClient
from src.selector import HalachaSelector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# State file path
STATE_DIR = Path(__file__).parent.parent / ".github" / "state"
STATE_FILE = STATE_DIR / "last_update_id.json"


def load_state() -> int:
    """Load last processed update ID from state file."""
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            return int(data.get("last_update_id", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            return 0
    return 0


def save_state(last_update_id: int) -> None:
    """Save last processed update ID to state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"last_update_id": last_update_id}, indent=2))
    logger.info(f"Saved state: last_update_id={last_update_id}")


async def handle_command(
    bot, chat_id: int, command: str, selector: HalachaSelector
) -> None:
    """Handle a single command.

    Args:
        bot: Telegram Bot instance (must be initialized)
        chat_id: Chat ID to send response to
        command: Command string (e.g., "/start", "/today")
        selector: HalachaSelector for getting daily content
    """
    try:
        if command == "/start":
            # Welcome + today's content for new users
            messages = get_start_messages(selector)
            for msg in messages:
                await bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            logger.info(f"Sent start messages to {chat_id}")

        elif command == "/today":
            # Just today's content for returning users
            messages = get_today_messages(selector)
            for msg in messages:
                await bot.send_message(
                    chat_id=chat_id,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True,
                )
            logger.info(f"Sent today's halachot to {chat_id}")

        elif command in ("/info", "/about", "/help"):
            # Combined info message
            await bot.send_message(
                chat_id=chat_id,
                text=get_info_message(),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"Sent info message to {chat_id}")

        else:
            # Unknown command - ignore silently
            logger.debug(f"Unknown command '{command}' from {chat_id} - ignoring")

    except Exception as e:
        logger.error(f"Error handling command {command} for {chat_id}: {e}")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=get_error_message(),
                parse_mode="HTML",
            )
        except Exception:
            pass


async def poll_and_respond() -> bool:
    """Poll for updates and respond to commands.

    Returns True if successful, False otherwise.
    """
    # Import telegram here to allow graceful failure
    try:
        from telegram import Bot
    except ImportError as e:
        logger.error(f"telegram module not available: {e}")
        return False

    # Load config
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return False

    # Initialize components
    client = SefariaClient()
    selector = HalachaSelector(client)

    # Pre-warm cache for instant responses
    # This loads today's cached messages into memory before processing any commands
    cached = selector.get_cached_messages()
    if cached:
        logger.info(
            f"Cache pre-warmed: {len(cached)} messages ready for instant response"
        )
    else:
        logger.warning("No cached messages available - responses may be slower")

    # Load state
    last_update_id = load_state()
    logger.info(f"Starting poll with offset {last_update_id + 1}")

    # Use Bot as async context manager (required in python-telegram-bot v20+)
    async with Bot(token=config.telegram_bot_token) as bot:
        try:
            # Delete any existing webhook to ensure getUpdates works
            # (Telegram won't send updates via getUpdates if a webhook is set)
            webhook_deleted = await bot.delete_webhook(drop_pending_updates=False)
            if webhook_deleted:
                logger.info("Webhook cleared, ready for polling")

            # Get updates (use shorter timeout to avoid workflow hanging)
            updates = await bot.get_updates(
                offset=last_update_id + 1,
                timeout=10,  # Reduced from 30s to prevent workflow timeouts
                allowed_updates=["message"],
            )

            if not updates:
                logger.info("No new updates")
                return True

            logger.info(f"Processing {len(updates)} update(s)")

            # Process each update
            new_last_update_id = last_update_id
            for update in updates:
                new_last_update_id = max(new_last_update_id, update.update_id)

                # Only process messages with text
                if not update.message or not update.message.text:
                    continue

                text = update.message.text.strip()
                chat_id = update.message.chat_id

                # Only process commands (starting with /)
                if text.startswith("/"):
                    command = (
                        text.split()[0].split("@")[0].lower()
                    )  # Handle /cmd@botname
                    logger.info(f"Processing command '{command}' from chat {chat_id}")
                    await handle_command(bot, chat_id, command, selector)

            # Save state
            if new_last_update_id > last_update_id:
                save_state(new_last_update_id)

            return True

        except Exception as e:
            logger.error(f"Error polling updates: {e}")
            import traceback

            traceback.print_exc()
            return False


def main() -> None:
    """Main entry point."""
    logger.info("=== Poll Commands Script Started ===")

    success = asyncio.run(poll_and_respond())

    if success:
        logger.info("=== Poll completed successfully ===")
        sys.exit(0)
    else:
        logger.error("=== Poll failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
