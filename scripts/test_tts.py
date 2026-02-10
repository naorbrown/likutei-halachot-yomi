#!/usr/bin/env python3
"""Test TTS pipeline: generate audio and send to Telegram.

Usage:
    python scripts/test_tts.py                     # Use sample text
    python scripts/test_tts.py --date 2026-02-10   # Use cached halacha for date
    python scripts/test_tts.py --text "custom"     # Custom Hebrew text
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from telegram import Bot

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config, get_data_dir
from src.tts import HebrewTTSClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

SAMPLE_TEXT = (
    "יִתְגַּבֵּר כַּאֲרִי לַעֲמֹד בַּבֹּקֶר לַעֲבוֹדַת בּוֹרְאוֹ. "
    "שֶׁיְּהֵא הוּא מְעוֹרֵר הַשַּׁחַר וְלֹא שֶׁהַשַּׁחַר יְעוֹרְרֵנוּ. "
    "כִּי צָרִיךְ הָאָדָם לְהִתְגַּבֵּר תָּמִיד לַעֲבוֹדַת הַבּוֹרֵא יִתְבָּרַךְ."
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test TTS pipeline")
    parser.add_argument("--date", type=str, help="Load halacha from cache (YYYY-MM-DD)")
    parser.add_argument("--text", type=str, help="Custom Hebrew text to synthesize")
    return parser.parse_args()


def load_cached_text(date_str: str) -> str | None:
    """Load Hebrew text from a cached daily pair."""
    cache_file = get_data_dir() / "cache" / f"pair_{date_str}.json"
    if not cache_file.exists():
        logger.error(f"No cache file for {date_str}: {cache_file}")
        return None

    data = json.loads(cache_file.read_text())
    text: str = data.get("first", {}).get("hebrew_text", "")
    if not text:
        logger.error(f"No Hebrew text in cache for {date_str}")
        return None
    return text


async def send_test_voice(config: Config, audio: bytes, caption: str) -> None:
    """Send a voice message to the configured Telegram chat."""
    bot = Bot(token=config.telegram_bot_token)
    async with bot:
        result = await bot.send_voice(
            chat_id=config.telegram_chat_id,
            voice=audio,
            caption=caption,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
        )
        logger.info(
            f"Voice message sent (message_id={result.message_id}, "
            f"duration={result.voice.duration if result.voice else '?'}s)"
        )


def main() -> int:
    load_dotenv()
    args = parse_args()

    # Determine text to synthesize
    if args.text:
        text = args.text
        caption = "\U0001f509 TTS Test (custom text)"
    elif args.date:
        text = load_cached_text(args.date)
        if not text:
            return 1
        caption = f"\U0001f509 TTS Test ({args.date})"
    else:
        text = SAMPLE_TEXT
        caption = "\U0001f509 TTS Test (sample)"

    logger.info(f"Text length: {len(text)} chars")
    logger.info(f"Text preview: {text[:100]}...")

    # Load config
    try:
        config = Config.from_env()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        return 1

    # Generate audio
    tts = HebrewTTSClient(config.google_tts_credentials_json)
    audio = tts.synthesize_text(text)
    if not audio:
        logger.error("TTS synthesis failed")
        return 1

    logger.info(f"Audio generated: {len(audio)} bytes ({len(audio) / 1024:.1f} KB)")

    # Send to Telegram
    asyncio.run(send_test_voice(config, audio, caption))
    logger.info("Test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
