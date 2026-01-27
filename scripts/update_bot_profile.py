#!/usr/bin/env python3
"""
Update Telegram Bot Profile

This script updates the bot's description, short description, and commands.
Run this when you need to update the bot's public-facing profile.

Usage:
    python scripts/update_bot_profile.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.telegram_bot import TelegramBot


# Bot descriptions - edit these when needed
BOT_DESCRIPTION = """ליקוטי הלכות יומי - דף היומי בליקוטי הלכות

📖 קבל כל יום את הדף היומי בליקוטי הלכות לפי לוח אשרינו הרשמי של קהילת ברסלב העולמית.

✨ מה הבוט מציע:
• הדף היומי נשלח אוטומטית כל יום
• טקסט מלא מספריא
• קישור ישיר ללימוד באתר
• לוח שנה מדויק לשנת תשפ״ו (מחזור ה׳)

📚 ליקוטי הלכות הוא ספרו המרכזי של רבי נתן מברסלב, המיישם את תורות רבי נחמן על ארבעת חלקי השולחן ערוך.

🔗 מבוסס על לוח אשרינו הרשמי
💡 קוד פתוח: github.com/naorbrown/likutei-halachot-yomi"""

BOT_SHORT_DESCRIPTION = """📖 דף היומי בליקוטי הלכות לפי לוח אשרינו • טקסט מלא • קישור לספריא • אוטומטי כל יום"""


async def main():
    """Update bot profile."""
    print("Likutei Halachot Yomi - Bot Profile Updater")
    print("=" * 50)

    try:
        config = Config.from_env()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure TELEGRAM_BOT_TOKEN is set in your environment or .env file")
        return 1

    bot = TelegramBot(config)

    # Test connection
    print("\n1. Testing connection...")
    if not await bot.test_connection():
        print("Failed to connect to Telegram")
        return 1
    print("   Connected successfully!")

    # Set commands
    print("\n2. Setting bot commands...")
    if await bot.setup_commands():
        print("   Commands updated!")
    else:
        print("   Failed to set commands")

    # Set descriptions
    print("\n3. Setting bot descriptions...")
    print(f"   Description length: {len(BOT_DESCRIPTION)} chars (max 512)")
    print(f"   Short description length: {len(BOT_SHORT_DESCRIPTION)} chars (max 120)")

    if len(BOT_DESCRIPTION) > 512:
        print("   ERROR: Description too long!")
        return 1
    if len(BOT_SHORT_DESCRIPTION) > 120:
        print("   ERROR: Short description too long!")
        return 1

    if await bot.set_bot_description(BOT_DESCRIPTION, BOT_SHORT_DESCRIPTION):
        print("   Descriptions updated!")
    else:
        print("   Failed to set descriptions")
        return 1

    print("\n" + "=" * 50)
    print("Bot profile updated successfully!")
    print("\nDescriptions set:")
    print("-" * 50)
    print("SHORT DESCRIPTION:")
    print(BOT_SHORT_DESCRIPTION)
    print("-" * 50)
    print("FULL DESCRIPTION:")
    print(BOT_DESCRIPTION)

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
