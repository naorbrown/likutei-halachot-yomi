#!/usr/bin/env python3
"""
Likutei Halachot Yomi - Daily Learning Bot

Usage:
    python run.py              # Send daily portion
    python run.py --preview    # Preview without sending
    python run.py --test       # Test mode with sample data
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config, get_config
from src.app import LikuteiHalachotYomiApp, setup_logging


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Likutei Halachot Yomi - Daily Learning Bot"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview today's portion without sending",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (don't send to Telegram)",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Override date (YYYY-MM-DD format)",
    )
    parser.add_argument(
        "--generate-schedule",
        action="store_true",
        help="Regenerate the yearly schedule",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


async def async_main():
    """Async main function."""
    args = parse_args()

    # Get config
    if args.test:
        config = Config.for_testing()
    else:
        try:
            config = Config.from_env()
        except ValueError as e:
            print(f"Configuration error: {e}")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            print("Or use --test mode for testing without Telegram")
            return 1

    if args.verbose:
        config.log_level = "DEBUG"

    setup_logging(config)

    # Create app
    app = LikuteiHalachotYomiApp(config)

    # Parse date if provided
    gregorian_date = None
    if args.date:
        from datetime import datetime
        try:
            gregorian_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            return 1

    # Handle commands
    if args.generate_schedule:
        print("Regenerating schedule...")
        app.schedule_manager._schedule = None
        app.schedule_manager._generate_default_schedule()
        app.schedule_manager.save_schedule()
        print(f"Schedule saved to {app.schedule_manager.schedule_file}")
        return 0

    if args.preview:
        print("\n" + "=" * 60)
        print("PREVIEW - Today's Likutei Halachot Yomi")
        print("=" * 60 + "\n")
        preview = app.preview(gregorian_date)
        print(preview)
        return 0

    # Run the bot
    success = await app.run(gregorian_date)
    return 0 if success else 1


def main():
    """Main entry point."""
    exit_code = asyncio.run(async_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
