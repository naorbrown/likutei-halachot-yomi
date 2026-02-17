#!/usr/bin/env python3
"""
Likutei Halachot Yomi - Daily wisdom from Rebbe Nachman's halachic teachings.

Usage:
    python main.py              # Send daily broadcast (for cron/CI)
    python main.py --serve      # Run interactive bot
    python main.py --preview    # Preview today's message
"""

import argparse
import asyncio
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.bot import LikuteiHalachotBot
from src.config import Config
from src.formatter import format_daily_message
from src.sefaria import SefariaClient
from src.selector import HalachaSelector

logger = logging.getLogger(__name__)

# Israel timezone for DST-aware scheduling
ISRAEL_TZ = ZoneInfo("Asia/Jerusalem")


BROADCAST_MARKER = Path(".github/state/last_broadcast_date.txt")


def is_broadcast_hour() -> bool:
    """Check if it's currently the 3am-5am window in Israel.

    The workflow runs at both 0am and 1am UTC to cover DST transitions.
    GitHub Actions cron can be delayed 30-120+ minutes, so we accept a window
    of 3am-5am Israel time. The already_sent_today() guard prevents duplicates.
    """
    israel_now = datetime.now(ISRAEL_TZ)
    return israel_now.hour in (3, 4, 5)


def already_sent_today() -> bool:
    """Check if we already sent a broadcast today (prevents double-sends)."""
    today = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d")
    if BROADCAST_MARKER.exists() and BROADCAST_MARKER.read_text().strip() == today:
        return True
    return False


def mark_sent_today() -> None:
    """Record that we sent a broadcast today."""
    today = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d")
    BROADCAST_MARKER.parent.mkdir(parents=True, exist_ok=True)
    BROADCAST_MARKER.write_text(today)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Likutei Halachot Yomi Telegram Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py              Send daily message to configured chat
    python main.py --serve      Run interactive bot with polling
    python main.py --preview    Preview today's message locally
        """,
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run bot in interactive polling mode",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview today's message without sending",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Override date for preview (YYYY-MM-DD format)",
    )
    return parser.parse_args()


def preview_message(date_override: str | None = None) -> None:
    """Preview today's message without sending."""
    import re

    client = SefariaClient()
    selector = HalachaSelector(client)

    if date_override:
        from datetime import datetime

        target_date = datetime.strptime(date_override, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    print(f"\n{'=' * 60}")
    print(f"Preview for: {target_date}")
    print("=" * 60)

    pair = selector.get_daily_pair(target_date)
    if pair:
        messages = format_daily_message(pair, target_date)
        # Convert HTML to readable text for terminal
        for i, msg in enumerate(messages, 1):
            readable = re.sub(r"<[^>]+>", "", msg)
            print(f"\n--- Message {i} ---")
            print(readable)

        print(f"\n{'=' * 60}")
        total_chars = sum(len(m) for m in messages)
        print(f"Total messages: {len(messages)}")
        print(f"Total characters: {total_chars}")
        print(f"First halacha: {pair.first.reference}")
        print(f"Second halacha: {pair.second.reference}")
    else:
        print("ERROR: Failed to get daily pair")
        sys.exit(1)


async def send_broadcast(config: Config) -> bool:
    """Send the daily broadcast."""
    bot = LikuteiHalachotBot(config)
    return await bot.send_daily_broadcast()


def run_server(config: Config) -> None:
    """Run the bot in interactive mode."""
    bot = LikuteiHalachotBot(config)
    bot.run_polling()


def main() -> int:
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    args = parse_args()

    # Preview mode doesn't need config
    if args.preview:
        preview_message(args.date)
        return 0

    # Load and validate configuration
    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    config.setup_logging()
    logger.info("Likutei Halachot Yomi starting...")
    logger.info(f"Chat ID: {config.telegram_chat_id}")
    logger.info(f"Token: {config.telegram_bot_token[:10]}...")

    if args.serve:
        # Interactive mode
        run_server(config)
        return 0
    else:
        # One-shot broadcast mode (CI/cron)
        # GitHub Actions cron can be delayed 30-120+ minutes, so we accept
        # 3am-5am Israel time. The already_sent_today guard prevents duplicates.
        if not is_broadcast_hour():
            israel_now = datetime.now(ISRAEL_TZ)
            logger.info(
                f"Skipping broadcast: Israel time is {israel_now.strftime('%H:%M')} "
                f"(not in 3-5am window). DST handling - other scheduled run will send."
            )
            return 0

        if already_sent_today():
            logger.info("Skipping broadcast: already sent today.")
            return 0

        logger.info("Sending daily broadcast...")
        success = asyncio.run(send_broadcast(config))
        if success:
            mark_sent_today()
            logger.info("Broadcast completed successfully!")
        else:
            logger.error("Broadcast failed!")
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
