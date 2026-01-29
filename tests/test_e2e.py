"""End-to-end tests for the bot.

These tests verify the complete flow from receiving a command to sending a response.
"""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestE2EPollCommands:
    """End-to-end tests for poll_commands.py."""

    @pytest.fixture
    def mock_env(self, tmp_path, monkeypatch):
        """Set up environment variables for testing."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")
        return tmp_path

    @pytest.fixture
    def state_dir(self, tmp_path):
        """Create a temporary state directory."""
        state_dir = tmp_path / ".github" / "state"
        state_dir.mkdir(parents=True)
        return state_dir

    @pytest.mark.asyncio
    async def test_e2e_start_command_flow(self, mock_env, state_dir, sample_daily_pair):
        """Test complete flow: receive /start -> send welcome message."""
        # Skip if telegram not available
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import handle_command

        # Mock the bot
        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        # Simulate /start command
        await handle_command(mock_bot, 12345, "/start", mock_client, mock_selector)

        # Verify welcome message was sent
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 12345
        assert "ברוכים הבאים" in call_kwargs["text"]
        assert call_kwargs["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_e2e_today_command_flow(self, mock_env, state_dir, sample_daily_pair):
        """Test complete flow: receive /today -> fetch halacha -> send response."""
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import handle_command

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        # Simulate /today command
        await handle_command(mock_bot, 12345, "/today", mock_client, mock_selector)

        # Verify selector was called with today's date
        mock_selector.get_daily_pair.assert_called_once_with(date.today())

        # Verify messages were sent (at least 1 for the halacha)
        assert mock_bot.send_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_e2e_state_persistence(self, mock_env, state_dir):
        """Test that state is properly persisted between runs."""
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        # Patch the state file location
        with patch("scripts.poll_commands.STATE_DIR", state_dir):
            with patch(
                "scripts.poll_commands.STATE_FILE", state_dir / "last_update_id.json"
            ):
                from scripts.poll_commands import load_state, save_state

                # Initial state should be 0
                assert load_state() == 0

                # Save a new state
                save_state(12345)

                # Verify state was persisted
                assert load_state() == 12345

                # Verify file contents
                state_file = state_dir / "last_update_id.json"
                data = json.loads(state_file.read_text())
                assert data["last_update_id"] == 12345

    @pytest.mark.asyncio
    async def test_e2e_unknown_command_flow(self, mock_env, state_dir):
        """Test that unknown commands get a helpful response."""
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import handle_command

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        # Simulate unknown command
        await handle_command(mock_bot, 12345, "/unknown", mock_client, mock_selector)

        # Verify error message was sent
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "/help" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_e2e_error_handling(self, mock_env, state_dir, sample_daily_pair):
        """Test that errors are handled gracefully."""
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import handle_command

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.side_effect = Exception("API Error")

        # Simulate /today command that will fail
        await handle_command(mock_bot, 12345, "/today", mock_client, mock_selector)

        # Verify error message was sent
        mock_bot.send_message.assert_called()
        # Last call should be error message
        last_call_kwargs = mock_bot.send_message.call_args[1]
        assert "שגיאה" in last_call_kwargs["text"]


class TestE2EBroadcast:
    """End-to-end tests for daily broadcast."""

    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Set up environment variables for testing."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "123456789")

    @pytest.mark.asyncio
    async def test_e2e_broadcast_flow(self, mock_env, sample_daily_pair):
        """Test complete broadcast flow."""
        try:
            import telegram  # noqa: F401
        except ImportError:
            pytest.skip("telegram not available")

        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="test_token_123",
            telegram_chat_id="123456789",
        )
        bot = LikuteiHalachotBot(config)

        # Mock the selector and Bot
        with patch.object(
            bot.selector, "get_daily_pair", return_value=sample_daily_pair
        ):
            with patch("src.bot.Bot") as mock_bot_class:
                mock_bot_instance = AsyncMock()
                mock_bot_class.return_value = mock_bot_instance
                mock_bot_instance.__aenter__ = AsyncMock(return_value=mock_bot_instance)
                mock_bot_instance.__aexit__ = AsyncMock(return_value=None)

                result = await bot.send_daily_broadcast()

        assert result is True
        # Verify messages were sent
        assert mock_bot_instance.send_message.call_count >= 1


class TestE2EMessageFormatting:
    """End-to-end tests for message formatting."""

    def test_e2e_no_duplicate_halachot(self, sample_daily_pair):
        """Verify the הלכות duplication bug is fixed."""
        from src.formatter import format_daily_message

        messages = format_daily_message(sample_daily_pair, date(2024, 1, 27))
        combined = "".join(messages)

        # This was the original bug - הלכות appearing twice
        assert "הלכות הלכות" not in combined

        # Section name should appear correctly
        assert "הלכות השכמת הבוקר" in combined or "הלכות שחיטה" in combined

    def test_e2e_message_contains_required_elements(self, sample_daily_pair):
        """Verify messages contain all required elements."""
        from src.formatter import format_daily_message

        messages = format_daily_message(sample_daily_pair, date(2024, 1, 27))
        combined = "".join(messages)

        # Should have date
        assert "27/01/2024" in combined

        # Should have signature
        assert "נ נח נחמ נחמן מאומן" in combined

        # Should have Sefaria links
        assert "sefaria.org" in combined

        # Should have title
        assert "ליקוטי הלכות יומי" in combined
