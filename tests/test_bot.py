"""Tests for the Telegram bot."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip all tests in this module if telegram is not available
pytest.importorskip("telegram")

from src.bot import LikuteiHalachotBot
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock config."""
    return Config(
        telegram_bot_token="test_token_12345",
        telegram_chat_id="123456789",
    )


@pytest.fixture
def bot(mock_config):
    """Create a bot instance with mock config."""
    return LikuteiHalachotBot(mock_config)


class TestBotInitialization:
    """Tests for bot initialization."""

    def test_bot_creates_with_config(self, mock_config):
        """Bot should initialize with config."""
        bot = LikuteiHalachotBot(mock_config)
        assert bot.config == mock_config
        assert bot.client is not None
        assert bot.selector is not None

    def test_bot_has_required_methods(self, bot):
        """Bot should have all required command handlers."""
        assert hasattr(bot, "start_command")
        assert hasattr(bot, "today_command")
        assert hasattr(bot, "about_command")
        assert hasattr(bot, "help_command")
        assert hasattr(bot, "unknown_command")
        assert hasattr(bot, "send_daily_broadcast")
        assert hasattr(bot, "run_polling")


class TestCommandHandlers:
    """Tests for command handlers."""

    @pytest.mark.asyncio
    async def test_start_command_sends_welcome(self, bot):
        """Start command should send welcome message."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        await bot.start_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "ברוכים הבאים" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_start_command_handles_no_message(self, bot):
        """Start command should handle missing message gracefully."""
        update = MagicMock()
        update.message = None
        context = MagicMock()

        # Should not raise
        await bot.start_command(update, context)

    @pytest.mark.asyncio
    async def test_about_command_sends_about(self, bot):
        """About command should send about message."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        await bot.about_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "ליקוטי הלכות" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_help_command_sends_help(self, bot):
        """Help command should send help message."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        await bot.help_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "/start" in call_args[0][0]
        assert "/today" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_unknown_command_sends_error(self, bot):
        """Unknown command should send error message."""
        update = MagicMock()
        update.message = AsyncMock()
        context = MagicMock()

        await bot.unknown_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "/help" in call_args[0][0]


class TestTodayCommand:
    """Tests for /today command."""

    @pytest.mark.asyncio
    async def test_today_command_with_valid_pair(self, bot, sample_daily_pair):
        """Today command should send halachot when pair is available."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        with patch.object(
            bot.selector, "get_daily_pair", return_value=sample_daily_pair
        ):
            await bot.today_command(update, context)

        # Should have called reply_text at least once
        assert update.message.reply_text.call_count >= 1

    @pytest.mark.asyncio
    async def test_today_command_with_no_pair(self, bot):
        """Today command should send error when no pair available."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        with patch.object(bot.selector, "get_daily_pair", return_value=None):
            await bot.today_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "שגיאה" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_today_command_handles_exception(self, bot):
        """Today command should handle exceptions gracefully."""
        update = MagicMock()
        update.message = AsyncMock()
        update.effective_user.id = 12345
        context = MagicMock()

        with patch.object(
            bot.selector, "get_daily_pair", side_effect=Exception("Test error")
        ):
            await bot.today_command(update, context)

        update.message.reply_text.assert_called_once()
        call_args = update.message.reply_text.call_args
        assert "שגיאה" in call_args[0][0]


class TestBroadcast:
    """Tests for broadcast functionality."""

    @pytest.mark.asyncio
    async def test_send_daily_broadcast_success(self, bot, sample_daily_pair):
        """Broadcast should succeed with valid pair."""
        mock_bot = AsyncMock()

        with patch.object(
            bot.selector, "get_daily_pair", return_value=sample_daily_pair
        ):
            with patch("src.bot.Bot", return_value=mock_bot):
                mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
                mock_bot.__aexit__ = AsyncMock(return_value=None)

                result = await bot.send_daily_broadcast()

        assert result is True

    @pytest.mark.asyncio
    async def test_send_daily_broadcast_no_pair(self, bot):
        """Broadcast should fail when no pair available."""
        with patch.object(bot.selector, "get_daily_pair", return_value=None):
            result = await bot.send_daily_broadcast()

        assert result is False


class TestBuildApp:
    """Tests for application building."""

    def test_build_app_returns_application(self, bot):
        """Build app should return an Application instance."""
        with patch("src.bot.Application") as mock_app_class:
            mock_builder = MagicMock()
            mock_app_class.builder.return_value = mock_builder
            mock_builder.token.return_value = mock_builder
            mock_builder.post_init.return_value = mock_builder
            mock_builder.build.return_value = MagicMock()

            app = bot.build_app()

            assert app is not None
            mock_app_class.builder.assert_called_once()
