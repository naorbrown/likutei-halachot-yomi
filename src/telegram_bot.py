"""
Telegram bot for sending Likutei Halachot Yomi.

Supports two modes:
1. One-shot mode: Send daily portion via cron/GitHub Actions
2. Interactive mode: Long-polling bot that responds to commands
"""

import asyncio
import logging
import re
from typing import List, Optional, TYPE_CHECKING

from telegram import Bot, Update, BotCommand
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler, ContextTypes

from .config import Config
from .message_formatter import FormattedMessage

if TYPE_CHECKING:
    from .app import LikuteiHalachotYomiApp

logger = logging.getLogger(__name__)


class TelegramBot:
    """Handles sending messages to Telegram."""

    def __init__(self, config: Config):
        self.config = config
        self.bot = Bot(token=config.telegram_bot_token)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = ParseMode.HTML,
    ) -> bool:
        """
        Send a message to Telegram.

        Args:
            text: Message text
            chat_id: Target chat ID (defaults to config)
            parse_mode: Message parse mode

        Returns:
            True if sent successfully
        """
        target_chat = chat_id or self.config.telegram_chat_id

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=False,
            )
            logger.info(f"Message sent successfully to {target_chat}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram error sending message: {e}")

            # Try sending without formatting if parsing failed
            if "can't parse" in str(e).lower():
                try:
                    await self.bot.send_message(
                        chat_id=target_chat,
                        text=self._strip_html(text),
                    )
                    logger.info("Message sent without formatting")
                    return True
                except TelegramError as e2:
                    logger.error(f"Failed to send plain text: {e2}")

            return False

    async def send_formatted_messages(
        self,
        messages: List[FormattedMessage],
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Send multiple formatted messages.

        Args:
            messages: List of FormattedMessage objects
            chat_id: Target chat ID

        Returns:
            True if all messages sent successfully
        """
        success = True

        for i, message in enumerate(messages):
            result = await self.send_message(
                text=message.text,
                chat_id=chat_id,
                parse_mode=message.parse_mode,
            )

            if not result:
                success = False

            # Small delay between messages to avoid rate limiting
            if i < len(messages) - 1:
                await asyncio.sleep(0.5)

        return success

    async def setup_commands(self) -> bool:
        """Set up bot commands for the menu."""
        commands = [
            BotCommand("start", "התחל לקבל ליקוטי הלכות יומי"),
            BotCommand("today", "קבל את ההלכה של היום"),
            BotCommand("about", "אודות הבוט"),
            BotCommand("help", "עזרה"),
        ]
        try:
            await self.bot.set_my_commands(commands)
            logger.info("Bot commands set successfully")
            return True
        except TelegramError as e:
            logger.error(f"Failed to set commands: {e}")
            return False

    def _strip_html(self, text: str) -> str:
        """Remove HTML formatting from text."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        return text

    async def test_connection(self) -> bool:
        """
        Test the Telegram bot connection.

        Returns:
            True if connection is working
        """
        try:
            me = await self.bot.get_me()
            logger.info(f"Connected to Telegram as @{me.username}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False

    async def set_bot_description(
        self,
        description: str,
        short_description: str,
    ) -> bool:
        """
        Set the bot's description and short description.

        Args:
            description: Full description shown in bot profile (up to 512 chars)
            short_description: Short description shown in empty chat (up to 120 chars)

        Returns:
            True if both set successfully
        """
        try:
            await self.bot.set_my_description(description=description)
            logger.info("Bot description set successfully")

            await self.bot.set_my_short_description(short_description=short_description)
            logger.info("Bot short description set successfully")

            return True
        except TelegramError as e:
            logger.error(f"Failed to set bot description: {e}")
            return False


class InteractiveTelegramBot:
    """
    Interactive Telegram bot that responds to commands.

    This runs as a long-polling bot, listening for and responding to user commands.
    """

    def __init__(self, config: Config, app: "LikuteiHalachotYomiApp"):
        self.config = config
        self.app = app
        self.application: Optional[Application] = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """ברוכים הבאים לליקוטי הלכות יומי! 📖

הבוט שולח כל יום את הדף היומי בליקוטי הלכות לפי לוח אשרינו הרשמי.

פקודות זמינות:
/today - קבל את ההלכה של היום
/about - אודות הבוט
/help - עזרה

נ נח נחמ נחמן מאומן! 🙏"""

        await update.message.reply_text(welcome_message)
        logger.info(f"Start command from user {update.effective_user.id}")

    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /today command - send today's portion."""
        logger.info(f"Today command from user {update.effective_user.id}")

        try:
            # Get today's Hebrew date
            from .hebrew_calendar import get_hebrew_date
            hebrew_date = get_hebrew_date()

            # Get daily portions
            portions = self.app.schedule_manager.get_daily_portions(hebrew_date)

            if not portions:
                await update.message.reply_text(
                    "לא נמצא לימוד להיום. נסה שוב מאוחר יותר."
                )
                return

            # Fetch texts from Sefaria
            sefaria_texts = []
            for portion in portions:
                logger.info(f"Fetching: {portion.ref}")
                text = self.app.sefaria_client.get_text(portion.ref)
                sefaria_texts.append(text)

            # Format messages
            messages = self.app.formatter.format_daily_message(
                hebrew_date=hebrew_date,
                portions=portions,
                sefaria_texts=sefaria_texts,
            )

            # Send messages
            for message in messages:
                try:
                    await update.message.reply_text(
                        text=message.text,
                        parse_mode=message.parse_mode,
                        disable_web_page_preview=False,
                    )
                except TelegramError as e:
                    logger.error(f"Error sending message: {e}")
                    # Try without formatting
                    plain_text = re.sub(r'<[^>]+>', '', message.text)
                    await update.message.reply_text(text=plain_text)

        except Exception as e:
            logger.error(f"Error in today_command: {e}", exc_info=True)
            await update.message.reply_text(
                "אירעה שגיאה. נסה שוב מאוחר יותר."
            )

    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command."""
        about_message = """📖 ליקוטי הלכות יומי

ליקוטי הלכות הוא ספרו המרכזי של רבי נתן מברסלב, תלמידו הגדול של רבי נחמן מברסלב.

הספר מיישם את תורות רבי נחמן על ארבעת חלקי השולחן ערוך:
• אורח חיים
• יורה דעה
• אבן העזר
• חושן משפט

🔄 מחזור הלימוד: 4 שנים
📅 שנה נוכחית: תשפ״ו (מחזור ה׳)
📚 מקור הלוח: אשרינו - קהילת ברסלב העולמית

🔗 טקסט מספריא
💻 קוד פתוח: github.com/naorbrown/likutei-halachot-yomi

נ נח נחמ נחמן מאומן! 🙏"""

        await update.message.reply_text(about_message)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """עזרה - ליקוטי הלכות יומי 📖

פקודות זמינות:

/start - התחל לקבל ליקוטי הלכות יומי
/today - קבל את ההלכה של היום
/about - אודות הבוט והלימוד
/help - הצג הודעה זו

הבוט שולח אוטומטית את הדף היומי בכל יום.
ניתן גם לבקש את הדף באופן ידני עם /today.

לשאלות ובעיות: github.com/naorbrown/likutei-halachot-yomi/issues"""

        await update.message.reply_text(help_message)

    async def run_polling(self):
        """Run the bot in long-polling mode."""
        logger.info("Starting interactive bot in polling mode...")

        # Build application
        self.application = (
            Application.builder()
            .token(self.config.telegram_bot_token)
            .build()
        )

        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("today", self.today_command))
        self.application.add_handler(CommandHandler("about", self.about_command))
        self.application.add_handler(CommandHandler("help", self.help_command))

        # Set up bot commands menu
        bot = TelegramBot(self.config)
        await bot.setup_commands()

        # Start polling
        logger.info("Bot is now polling for updates...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(drop_pending_updates=False)

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Stopping bot...")
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
