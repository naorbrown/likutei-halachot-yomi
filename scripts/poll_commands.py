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
from src.subscribers import add_subscriber, is_subscribed, remove_subscriber
from src.tts import send_voice_for_pair

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
    bot,
    chat_id: int,
    command: str,
    selector: HalachaSelector,
    config: Config | None = None,
) -> None:
    """Handle a single command.

    Args:
        bot: Telegram Bot instance (must be initialized)
        chat_id: Chat ID to send response to
        command: Command string (e.g., "/start", "/today")
        selector: HalachaSelector for getting daily content
        config: Optional Config for TTS support. If None, voice is skipped.
    """
    try:
        if command == "/start":
            # Auto-subscribe user for daily broadcasts
            was_new = add_subscriber(chat_id)
            if was_new:
                logger.info(f"Auto-subscribed new user {chat_id}")

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

            # Send voice messages if TTS enabled
            if config and config.google_tts_enabled:
                pair = selector.get_daily_pair()
                if pair:
                    await send_voice_for_pair(
                        bot, pair, chat_id, config.google_tts_credentials_json
                    )

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

            # Send voice messages if TTS enabled
            if config and config.google_tts_enabled:
                pair = selector.get_daily_pair()
                if pair:
                    await send_voice_for_pair(
                        bot, pair, chat_id, config.google_tts_credentials_json
                    )

        elif command in ("/info", "/about", "/help"):
            # Combined info message
            await bot.send_message(
                chat_id=chat_id,
                text=get_info_message(),
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            logger.info(f"Sent info message to {chat_id}")

        elif command == "/subscribe":
            # Explicit subscribe to daily broadcasts
            if is_subscribed(chat_id):
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ אתה כבר רשום לקבלת הלכות יומיות.",
                    parse_mode="HTML",
                )
            else:
                add_subscriber(chat_id)
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ נרשמת בהצלחה! תקבל הלכות יומיות בשעה 6 בבוקר.",
                    parse_mode="HTML",
                )
            logger.info(f"Subscribe command from {chat_id}")

        elif command == "/unsubscribe":
            # Unsubscribe from daily broadcasts
            if remove_subscriber(chat_id):
                await bot.send_message(
                    chat_id=chat_id,
                    text="✅ הסרת את הרישום. לא תקבל עוד הלכות יומיות.\nאפשר להירשם מחדש עם /subscribe",
                    parse_mode="HTML",
                )
            else:
                await bot.send_message(
                    chat_id=chat_id,
                    text="אתה לא רשום כרגע. להרשמה שלח /subscribe",
                    parse_mode="HTML",
                )
            logger.info(f"Unsubscribe command from {chat_id}")

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
        from telegram.error import NetworkError, TimedOut
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
    max_retries = 3
    async with Bot(token=config.telegram_bot_token) as bot:
        try:
            # Delete any existing webhook to ensure getUpdates works
            # (Telegram won't send updates via getUpdates if a webhook is set)
            webhook_deleted = await bot.delete_webhook(drop_pending_updates=False)
            if webhook_deleted:
                logger.info("Webhook cleared, ready for polling")
        except (TimedOut, NetworkError) as e:
            logger.warning(f"Could not clear webhook (will retry on next run): {e}")

        # Retry get_updates on transient network errors
        updates = None
        for attempt in range(1, max_retries + 1):
            try:
                updates = await bot.get_updates(
                    offset=last_update_id + 1,
                    timeout=10,
                    allowed_updates=["message"],
                )
                break  # Success
            except (TimedOut, NetworkError) as e:
                if attempt < max_retries:
                    wait = attempt * 2
                    logger.warning(
                        f"get_updates attempt {attempt}/{max_retries} failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                else:
                    # All retries exhausted - treat as non-fatal since next
                    # scheduled run (in 5 min) will pick up any pending updates
                    logger.warning(
                        f"get_updates failed after {max_retries} attempts: {e}. "
                        "Will retry on next scheduled run."
                    )
                    return True

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
                command = text.split()[0].split("@")[0].lower()  # Handle /cmd@botname
                logger.info(f"Processing command '{command}' from chat {chat_id}")
                await handle_command(bot, chat_id, command, selector, config)

        # Save state
        if new_last_update_id > last_update_id:
            save_state(new_last_update_id)

        return True


def main() -> None:
    """Main entry point.

    Always exits 0 — transient network errors are non-fatal since the
    next scheduled run (in 5 min) will pick up any pending updates.
    Exiting non-zero would trigger unnecessary failure notifications.
    """
    logger.info("=== Poll Commands Script Started ===")

    try:
        success = asyncio.run(poll_and_respond())
    except Exception as e:
        logger.warning(f"Poll encountered error (non-fatal): {e}")
        success = True  # Treat as non-fatal

    if success:
        logger.info("=== Poll completed successfully ===")
    else:
        logger.warning("=== Poll completed with issues (non-fatal) ===")

    sys.exit(0)


if __name__ == "__main__":
    main()
