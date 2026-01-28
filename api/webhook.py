"""
Vercel Serverless Function for Telegram Bot Webhook.

Handles /start, /today, /about commands with rate limiting.
"""

import asyncio
import hashlib
import logging
import os
import time
from datetime import date
from http.server import BaseHTTPRequestHandler
import json

from telegram import Bot, Update
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory rate limiter (resets on cold start, which is fine)
# Format: {user_id: [timestamp1, timestamp2, ...]}
request_times: dict[int, list[float]] = {}
RATE_LIMIT = 10  # requests per minute per user
RATE_WINDOW = 60  # seconds


def is_rate_limited(user_id: int) -> bool:
    """Check if user has exceeded rate limit."""
    now = time.time()

    if user_id not in request_times:
        request_times[user_id] = []

    # Remove old timestamps outside the window
    request_times[user_id] = [
        t for t in request_times[user_id] if now - t < RATE_WINDOW
    ]

    if len(request_times[user_id]) >= RATE_LIMIT:
        return True

    request_times[user_id].append(now)
    return False


def get_bot() -> Bot:
    """Get Telegram bot instance."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    return Bot(token=token)


def get_daily_pair(target_date: date) -> tuple[dict, dict] | None:
    """Get two halachot for the given date."""
    import requests

    # Get index of Likutei Halachot
    try:
        response = requests.get(
            "https://www.sefaria.org/api/v2/index/Likutei_Halachot",
            timeout=10
        )
        response.raise_for_status()
        index_data = response.json()
    except Exception as e:
        logger.error(f"Failed to get index: {e}")
        return None

    # Build list of all section references
    all_refs: list[str] = []

    def extract_refs(node: dict, prefix: str = "") -> None:
        if "nodes" in node:
            for child in node["nodes"]:
                child_prefix = f"{prefix}, {child.get('heTitle', '')}" if prefix else child.get('heTitle', '')
                extract_refs(child, child_prefix)
        elif "wholeRef" in node:
            all_refs.append(node["wholeRef"])

    if "schema" in index_data and "nodes" in index_data["schema"]:
        for node in index_data["schema"]["nodes"]:
            extract_refs(node)

    if len(all_refs) < 2:
        return None

    # Use date to deterministically select 2 sections
    date_str = target_date.isoformat()
    seed = int(hashlib.sha256(date_str.encode()).hexdigest(), 16)

    idx1 = seed % len(all_refs)
    idx2 = (seed // len(all_refs)) % len(all_refs)
    if idx2 == idx1:
        idx2 = (idx2 + 1) % len(all_refs)

    # Fetch the texts
    results = []
    for ref in [all_refs[idx1], all_refs[idx2]]:
        try:
            resp = requests.get(
                f"https://www.sefaria.org/api/texts/{ref}",
                params={"context": 0},
                timeout=10
            )
            resp.raise_for_status()
            results.append(resp.json())
        except Exception as e:
            logger.error(f"Failed to fetch {ref}: {e}")
            return None

    return (results[0], results[1]) if len(results) == 2 else None


def format_halacha(data: dict) -> str:
    """Format a single halacha for display."""
    he_title = data.get("heRef", "ליקוטי הלכות")
    en_title = data.get("ref", "Likutei Halachot")

    # Get Hebrew text
    he_text = data.get("he", [])
    if isinstance(he_text, list):
        he_text = he_text[0] if he_text else ""

    # Get English text
    en_text = data.get("text", [])
    if isinstance(en_text, list):
        en_text = en_text[0] if en_text else ""

    # Clean up HTML tags
    import re
    he_text = re.sub(r'<[^>]+>', '', str(he_text))[:500]
    en_text = re.sub(r'<[^>]+>', '', str(en_text))[:500]

    # Build Sefaria link
    ref = data.get("ref", "").replace(" ", "_")
    link = f"https://www.sefaria.org/{ref}" if ref else ""

    lines = [f"<b>{he_title}</b>"]
    if he_text:
        lines.append(f"\n{he_text}...")
    if en_text:
        lines.append(f"\n\n<i>{en_text}...</i>")
    if link:
        lines.append(f'\n\n<a href="{link}">קרא עוד / Read more</a>')

    return "".join(lines)


def format_daily_message(pair: tuple[dict, dict], target_date: date) -> str:
    """Format the daily message with both halachot."""
    date_str = target_date.strftime("%d/%m/%Y")

    header = f"📖 <b>ליקוטי הלכות יומי</b> | {date_str}\n"
    header += "━━━━━━━━━━━━━━━━━━━━━\n\n"

    h1 = format_halacha(pair[0])
    h2 = format_halacha(pair[1])

    divider = "\n\n━━━━━━━━━━━━━━━━━━━━━\n\n"

    return header + h1 + divider + h2


async def handle_command(bot: Bot, chat_id: int, command: str) -> None:
    """Handle bot commands."""
    if command == "/start":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "🌟 <b>ברוכים הבאים!</b>\n\n"
                "בוט זה שולח 2 הלכות אקראיות מליקוטי הלכות מדי יום.\n\n"
                "🌟 <b>Welcome!</b>\n\n"
                "This bot sends 2 random halachot from Likutei Halachot daily.\n\n"
                "<b>פקודות / Commands:</b>\n"
                "/today - קבל את ההלכות היומיות\n"
                "/about - אודות הבוט"
            ),
            parse_mode=ParseMode.HTML,
        )

    elif command == "/today":
        pair = get_daily_pair(date.today())
        if pair:
            message = format_daily_message(pair, date.today())
        else:
            message = (
                "❌ <b>שגיאה</b>\n\n"
                "לא הצלחנו לטעון את ההלכות. נסה שוב מאוחר יותר.\n\n"
                "❌ <b>Error</b>\n\n"
                "Failed to load halachot. Please try again later."
            )
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )

    elif command == "/about":
        await bot.send_message(
            chat_id=chat_id,
            text=(
                "ℹ️ <b>אודות / About</b>\n\n"
                "בוט ליקוטי הלכות יומי שולח 2 קטעים אקראיים "
                "מספר ליקוטי הלכות של רבי נתן מברסלב.\n\n"
                "The Likutei Halachot Yomi bot sends 2 random passages "
                "from Likutei Halachot by Rabbi Natan of Breslov.\n\n"
                "📚 טקסטים מ-Sefaria.org\n"
                "💻 קוד פתוח: github.com/naorbrown/likutei-halachot-yomi"
            ),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    else:
        await bot.send_message(
            chat_id=chat_id,
            text="לא הבנתי. נסה /start או /today\nI didn't understand. Try /start or /today",
        )


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""

    def do_GET(self):
        """Health check."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok", "bot": "Likutei Halachot Yomi"}).encode())

    def do_POST(self):
        """Handle Telegram webhook."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            update_data = json.loads(body)

            bot = get_bot()
            update = Update.de_json(update_data, bot)

            if update and update.message:
                user_id = update.message.from_user.id if update.message.from_user else 0
                chat_id = update.message.chat_id
                text = update.message.text or ""

                # Rate limiting
                if is_rate_limited(user_id):
                    asyncio.run(bot.send_message(
                        chat_id=chat_id,
                        text="⏳ לאט לאט! נסה שוב בעוד דקה.\n⏳ Slow down! Try again in a minute.",
                    ))
                else:
                    # Handle command
                    command = text.split()[0].lower() if text else ""
                    if command.startswith("/"):
                        asyncio.run(handle_command(bot, chat_id, command))

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

        except Exception as e:
            logger.exception(f"Error: {e}")
            self.send_response(200)  # Return 200 to avoid Telegram retries
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error"}).encode())
