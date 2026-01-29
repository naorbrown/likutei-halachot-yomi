"""Telegram bot implementation."""

import logging
from datetime import date, time
from zoneinfo import ZoneInfo

from telegram import Bot, BotCommand, Update
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
from .unified import is_unified_channel_enabled, publish_text_to_unified_channel

logger = logging.getLogger(__name__)


class LikuteiHalachotBot:
    """Telegram bot for daily Likutei Halachot."""

    def __init__(self, config: Config):
        self.config = config
        self.client = SefariaClient()
        self.selector = HalachaSelector(self.client)

    async def _post_init(self, app: Application) -> None:
        """Post-initialization: set up commands and send startup notification."""
        # Set up bot commands menu
        commands = [
            BotCommand("start", "התחל לקבל ליקוטי הלכות יומי"),
            BotCommand("today", "קבל את ההלכה של היום"),
            BotCommand("about", "אודות הבוט"),
            BotCommand("help", "עזרה"),
        ]
        await app.bot.set_my_commands(commands)
        logger.info("Bot commands configured")

        # Set bot description
        await app.bot.set_my_short_description("📚 שתי הלכות יומיות מליקוטי הלכות")
        await app.bot.set_my_description(
            "📚 ליקוטי הלכות יומי\n\n"
            "שתי הלכות יומיות מספר ליקוטי הלכות של רבי נתן מברסלב.\n\n"
            "נ נח נחמ נחמן מאומן"
        )
        logger.info("Bot description configured")

        # Send startup notification
        if self.config.telegram_chat_id:
            try:
                await app.bot.send_message(
                    chat_id=self.config.telegram_chat_id,
                    text="🤖 Bot started and listening for commands.",
                )
                logger.info("Startup notification sent")
            except Exception as e:
                logger.warning(f"Could not send startup notification: {e}")

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        if not update.message:
            return
        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"/start from user {user_id}")
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
        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"/today from user {user_id}")

        try:
            pair = self.selector.get_daily_pair(date.today())
            messages = (
                format_daily_message(pair, date.today())
                if pair
                else [format_error_message()]
            )
        except Exception as e:
            logger.exception(f"Error getting daily pair: {e}")
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
        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"/about from user {user_id}")
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
        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"/help from user {user_id}")
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

    def build_app(self) -> Application:
        """Build the Telegram application."""
        app = (
            Application.builder()
            .token(self.config.telegram_bot_token)
            .post_init(self._post_init)
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

        return app

    async def send_daily_broadcast(self) -> bool:
        """Send daily halachot to configured chat (for GitHub Actions)."""
        logger.info(f"Broadcasting to {self.config.telegram_chat_id}")

        try:
            pair = self.selector.get_daily_pair(date.today())
            if not pair:
                logger.error("Failed to get daily pair")
                return False

            messages = format_daily_message(pair, date.today())

            # Use simple Bot class directly
            bot = Bot(token=self.config.telegram_bot_token)
            async with bot:
                for msg in messages:
                    await bot.send_message(
                        chat_id=self.config.telegram_chat_id,
                        text=msg,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                    )

            logger.info("Broadcast sent successfully")

            # Also publish to unified Torah Yomi channel
            await self._send_to_unified_channel(pair)
            return True

        except Exception as e:
            logger.exception(f"Broadcast failed: {e}")
            return False

    async def _send_to_unified_channel(self, pair: tuple) -> None:
        """Send a condensed message to the unified Torah Yomi channel."""
        if not is_unified_channel_enabled():
            logger.debug("Unified channel not configured, skipping")
            return

        try:
            # Build a condensed message for the unified channel
            halacha1, halacha2 = pair

            unified_msg = f"<b>ליקוטי הלכות יומי</b>\n"
            unified_msg += f"📅 {date.today().strftime('%d/%m/%Y')}\n\n"

            if halacha1:
                unified_msg += f"<b>א׳</b> {halacha1.title_he}\n"
                # Include first 200 chars of content as preview
                if halacha1.content_he:
                    preview = halacha1.content_he[:200]
                    if len(halacha1.content_he) > 200:
                        preview += "..."
                    unified_msg += f"{preview}\n\n"

            if halacha2:
                unified_msg += f"<b>ב׳</b> {halacha2.title_he}\n"
                if halacha2.content_he:
                    preview = halacha2.content_he[:200]
                    if len(halacha2.content_he) > 200:
                        preview += "..."
                    unified_msg += f"{preview}\n"

            unified_msg += "\n<i>נ נח נחמ נחמן מאומן</i>"

            await publish_text_to_unified_channel(unified_msg)
            logger.info("Published to unified channel successfully")

        except Exception as e:
            # Don't fail the main broadcast if unified channel fails
            logger.error(f"Failed to publish to unified channel: {e}")

    def run_polling(self) -> None:
        """Run bot in polling mode with daily scheduling."""
        logger.info("Building application...")
        app = self.build_app()

        # Schedule daily broadcast at 6:00 AM Israel time
        if self.config.telegram_chat_id and app.job_queue:
            israel_tz = ZoneInfo("Asia/Jerusalem")
            broadcast_time = time(hour=6, minute=0, second=0, tzinfo=israel_tz)
            app.job_queue.run_daily(
                self._scheduled_broadcast,
                time=broadcast_time,
                name="daily_broadcast",
            )
            logger.info(f"Daily broadcast scheduled for {broadcast_time} Israel time")

        logger.info("Starting polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
