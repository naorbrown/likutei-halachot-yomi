#!/usr/bin/env python3
"""
Webhook-based web server for Telegram bot.

This runs on Render (or similar) and handles incoming webhook requests.
Render's free tier sleeps when inactive but wakes on incoming requests.
"""

import asyncio
import logging
import os
from datetime import date

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from telegram import Bot, Update
from telegram.constants import ParseMode

from src.config import Config
from src.formatter import (
    format_about_message,
    format_daily_message,
    format_error_message,
    format_welcome_message,
)
from src.sefaria import SefariaClient
from src.selector import HalachaSelector

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot components
config = Config.from_env()
bot = Bot(token=config.telegram_bot_token)
client = SefariaClient()
selector = HalachaSelector(client)


async def handle_start(chat_id: int) -> None:
    """Handle /start command."""
    await bot.send_message(
        chat_id=chat_id,
        text=format_welcome_message(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def handle_today(chat_id: int) -> None:
    """Handle /today command."""
    try:
        pair = selector.get_daily_pair(date.today())
        if pair:
            message = format_daily_message(pair, date.today())
        else:
            message = format_error_message()
    except Exception as e:
        logger.exception(f"Error getting daily halachot: {e}")
        message = format_error_message()

    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=False,
    )


async def handle_about(chat_id: int) -> None:
    """Handle /about command."""
    await bot.send_message(
        chat_id=chat_id,
        text=format_about_message(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def handle_unknown(chat_id: int) -> None:
    """Handle unknown commands."""
    await bot.send_message(
        chat_id=chat_id,
        text="לא הבנתי את הפקודה. נסה /start או /today",
        parse_mode=ParseMode.HTML,
    )


async def process_update(update_data: dict) -> None:
    """Process incoming Telegram update."""
    update = Update.de_json(update_data, bot)

    if not update or not update.message:
        return

    message = update.message
    chat_id = message.chat_id
    text = message.text or ""

    logger.info(f"Received message from {chat_id}: {text[:50]}")

    # Route commands
    if text.startswith("/start"):
        await handle_start(chat_id)
    elif text.startswith("/today"):
        await handle_today(chat_id)
    elif text.startswith("/about"):
        await handle_about(chat_id)
    elif text.startswith("/"):
        await handle_unknown(chat_id)


@app.route("/", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "bot": "Likutei Halachot Yomi"})


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming Telegram webhook."""
    try:
        update_data = request.get_json()
        if update_data:
            # Run async handler in sync context
            asyncio.run(process_update(update_data))
        return jsonify({"status": "ok"})
    except Exception as e:
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/set-webhook", methods=["POST"])
def set_webhook():
    """Set the Telegram webhook URL."""
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        return jsonify({"error": "WEBHOOK_URL not configured"}), 400

    full_url = f"{webhook_url}/webhook"

    async def _set():
        await bot.set_webhook(url=full_url)
        return await bot.get_webhook_info()

    info = asyncio.run(_set())
    return jsonify(
        {
            "status": "ok",
            "webhook_url": info.url,
            "pending_update_count": info.pending_update_count,
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
