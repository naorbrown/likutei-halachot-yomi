"""Telegram bot implementation."""

import logging
from datetime import date

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import Config
from .formatter import (
    format_about_message,
    format_daily_message,
    format_error_message,
    format_welcome_message,
)
from .sefaria import SefariaClient
from .selector import HalachaSelector

logger = logging.getLogger(__name__)


class LikuteiHalachotBot:
    """Telegram bot for daily Likutei Halachot."""

    def __init__(self, config: Config):
        self.config = config
        self.client = SefariaClient()
        self.selector = HalachaSelector(self.client)
        self._app: Application | None = None

    async def _setup_commands(self, app: Application) -> None:
        """Set up bot commands for the menu."""
        commands = [
            BotCommand("start", "התחל - הודעת פתיחה"),
            BotCommand("today", "הלכות היום"),
            BotCommand("about", "אודות הבוט"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands configured")

    async def _set_bot_description(self, app: Application) -> None:
        """Set bot description and about text."""
        # Short description (shown in search results)
        await app.bot.set_my_short_description("שתי הלכות יומיות מליקוטי הלכות 📚")

        # Full description (shown on bot profile)
        await app.bot.set_my_description(
            "📚 ליקוטי הלכות יומי\n\n"
            "קבלו כל יום שתי הלכות אקראיות מספר ליקוטי הלכות "
            "של רבי נתן מברסלב.\n\n"
            "• טקסט בעברית ואנגלית\n"
            "• קישור לספריא\n"
            "• משני חלקים שונים כל יום\n\n"
            "נ נח נחמ נחמן מאומן"
        )
        logger.info("Bot description configured")

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        logger.info(f"Start command from user {update.effective_user.id}")
        await update.message.reply_text(
            format_welcome_message(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def today_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /today command."""
        user_id = update.effective_user.id
        logger.info(f"Today command from user {user_id}")

        try:
            pair = self.selector.get_daily_pair(date.today())
            if pair:
                message = format_daily_message(pair, date.today())
            else:
                message = format_error_message()
        except Exception as e:
            logger.exception(f"Error getting daily halachot: {e}")
            message = format_error_message()

        await update.message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=False,
        )

    async def about_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /about command."""
        logger.info(f"About command from user {update.effective_user.id}")
        await update.message.reply_text(
            format_about_message(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def unknown_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle unknown commands."""
        await update.message.reply_text(
            "לא הבנתי את הפקודה. נסה /start או /today",
            parse_mode=ParseMode.HTML,
        )

    def build_app(self) -> Application:
        """Build and configure the Telegram application."""
        app = (
            Application.builder()
            .token(self.config.telegram_bot_token)
            .post_init(self._setup_commands)
            .post_init(self._set_bot_description)
            .build()
        )

        # Register handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("today", self.today_command))
        app.add_handler(CommandHandler("about", self.about_command))
        app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))

        self._app = app
        return app

    async def send_daily_broadcast(self) -> bool:
        """Send daily halachot to the configured chat."""
        logger.info(f"Sending daily broadcast to {self.config.telegram_chat_id}")

        try:
            pair = self.selector.get_daily_pair(date.today())
            if not pair:
                logger.error("Failed to get daily pair")
                return False

            message = format_daily_message(pair, date.today())

            app = self.build_app()
            async with app:
                await app.bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=False,
                )

            logger.info("Daily broadcast sent successfully")
            return True

        except Exception as e:
            logger.exception(f"Failed to send daily broadcast: {e}")
            return False

    def run_polling(self) -> None:
        """Run the bot in polling mode (for interactive use)."""
        logger.info("Starting bot in polling mode...")
        app = self.build_app()
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Clear any pending updates/conflicts
        )
