"""Telegram bot implementation."""

import logging
from datetime import date, time
from zoneinfo import ZoneInfo

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
    format_help_message,
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
        """Set up bot commands menu."""
        commands = [
            BotCommand("start", "התחל לקבל ליקוטי הלכות יומי"),
            BotCommand("today", "קבל את ההלכה של היום"),
            BotCommand("about", "אודות הבוט"),
            BotCommand("help", "עזרה"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands configured")

    async def _set_bot_description(self, app: Application) -> None:
        """Set bot description."""
        await app.bot.set_my_short_description("📚 שתי הלכות יומיות מליקוטי הלכות")
        await app.bot.set_my_description(
            "📚 ליקוטי הלכות יומי\n\n"
            "שתי הלכות יומיות מספר ליקוטי הלכות של רבי נתן מברסלב.\n\n"
            "נ נח נחמ נחמן מאומן"
        )
        logger.info("Bot description configured")

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        if not update.message:
            return
        logger.info(
            f"Start from user {update.effective_user.id if update.effective_user else 'unknown'}"
        )
        await update.message.reply_text(
            format_welcome_message(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def today_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /today command."""
        if not update.message:
            return
        logger.info(
            f"Today from user {update.effective_user.id if update.effective_user else 'unknown'}"
        )

        try:
            pair = self.selector.get_daily_pair(date.today())
            messages = (
                format_daily_message(pair, date.today())
                if pair
                else [format_error_message()]
            )
        except Exception as e:
            logger.exception(f"Error: {e}")
            messages = [format_error_message()]

        for msg in messages:
            await update.message.reply_text(
                msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )

    async def about_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /about command."""
        if not update.message:
            return
        logger.info(
            f"About from user {update.effective_user.id if update.effective_user else 'unknown'}"
        )
        await update.message.reply_text(
            format_about_message(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        if not update.message:
            return
        logger.info(
            f"Help from user {update.effective_user.id if update.effective_user else 'unknown'}"
        )
        await update.message.reply_text(
            format_help_message(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    async def unknown_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle unknown commands."""
        if not update.message:
            return
        await update.message.reply_text(
            "לא הבנתי. נסה /help לרשימת הפקודות.",
            parse_mode=ParseMode.HTML,
        )

    async def _error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Log errors caused by updates."""
        logger.exception(f"Exception while handling an update: {context.error}")

    def build_app(self) -> Application:
        """Build the Telegram application."""
        app = (
            Application.builder()
            .token(self.config.telegram_bot_token)
            .post_init(self._setup_commands)
            .post_init(self._set_bot_description)
            .build()
        )

        # Add command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("today", self.today_command))
        app.add_handler(CommandHandler("about", self.about_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(MessageHandler(filters.COMMAND, self.unknown_command))

        # Add error handler
        app.add_error_handler(self._error_handler)

        self._app = app
        return app

    async def send_daily_broadcast(self) -> bool:
        """Send daily halachot to configured chat."""
        logger.info(f"Broadcasting to {self.config.telegram_chat_id}")

        try:
            pair = self.selector.get_daily_pair(date.today())
            if not pair:
                logger.error("Failed to get daily pair")
                return False

            messages = format_daily_message(pair, date.today())
            app = self.build_app()
            async with app:
                for msg in messages:
                    await app.bot.send_message(
                        chat_id=self.config.telegram_chat_id,
                        text=msg,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )

            logger.info("Broadcast sent")
            return True

        except Exception as e:
            logger.exception(f"Broadcast failed: {e}")
            return False

    async def _scheduled_broadcast(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send daily broadcast via scheduled job."""
        logger.info("Running scheduled daily broadcast...")
        try:
            pair = self.selector.get_daily_pair(date.today())
            if not pair:
                logger.error("Failed to get daily pair for scheduled broadcast")
                return

            messages = format_daily_message(pair, date.today())
            for msg in messages:
                await context.bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text=msg,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
            logger.info("Scheduled broadcast sent successfully")
        except Exception as e:
            logger.exception(f"Scheduled broadcast failed: {e}")

    async def _notify_startup(self) -> None:
        """Send startup notification directly (not via post_init)."""
        if not self.config.telegram_chat_id:
            return
        try:
            app = Application.builder().token(self.config.telegram_bot_token).build()
            async with app:
                await app.bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text="🤖 Bot started and listening for commands.\n\n"
                    "If you don't get responses to /start or /today, "
                    "check that no other bot instance is running.",
                )
            logger.info("Startup notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")

    def run_polling(self, schedule_daily: bool = True) -> None:
        """Run bot in polling mode with optional daily scheduling."""
        import asyncio

        logger.info("Starting polling...")

        # Send startup notification before starting polling
        asyncio.get_event_loop().run_until_complete(self._notify_startup())

        app = self.build_app()

        if schedule_daily and self.config.telegram_chat_id and app.job_queue:
            # Schedule daily broadcast at 6:00 AM Israel time
            israel_tz = ZoneInfo("Asia/Jerusalem")
            broadcast_time = time(hour=6, minute=0, second=0, tzinfo=israel_tz)
            app.job_queue.run_daily(
                self._scheduled_broadcast,
                time=broadcast_time,
                name="daily_broadcast",
            )
            logger.info(f"Daily broadcast scheduled for {broadcast_time} Israel time")

        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
