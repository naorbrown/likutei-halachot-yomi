"""Tests for the poll commands script."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestStateManagement:
    """Tests for state loading and saving."""

    def test_load_state_no_file(self, tmp_path):
        """Should return 0 when state file doesn't exist."""
        with patch("scripts.poll_commands.STATE_FILE", tmp_path / "nonexistent.json"):
            from scripts.poll_commands import load_state

            assert load_state() == 0

    def test_load_state_with_file(self, tmp_path):
        """Should return saved update ID."""
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 12345}')

        with patch("scripts.poll_commands.STATE_FILE", state_file):
            from scripts.poll_commands import load_state

            assert load_state() == 12345

    def test_load_state_invalid_json(self, tmp_path):
        """Should return 0 for invalid JSON."""
        state_file = tmp_path / "state.json"
        state_file.write_text("not valid json")

        with patch("scripts.poll_commands.STATE_FILE", state_file):
            from scripts.poll_commands import load_state

            assert load_state() == 0

    def test_save_state(self, tmp_path):
        """Should save state to file."""
        state_dir = tmp_path / "state"
        state_file = state_dir / "state.json"

        with patch("scripts.poll_commands.STATE_DIR", state_dir):
            with patch("scripts.poll_commands.STATE_FILE", state_file):
                from scripts.poll_commands import save_state

                save_state(99999)

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["last_update_id"] == 99999


class TestHandleCommand:
    """Tests for command handling."""

    @pytest.mark.asyncio
    async def test_handle_start_command(self):
        """Should send welcome message for /start."""
        # Skip if telegram not available
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/start", mock_client, mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["chat_id"] == 12345
        assert "ליקוטי הלכות יומי" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_about_command(self):
        """Should send about message for /about."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/about", mock_client, mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "ליקוטי הלכות" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_help_command(self):
        """Should send help message for /help."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/help", mock_client, mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "/today" in call_kwargs["text"]
        assert "/about" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self):
        """Should send error for unknown commands."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/unknown", mock_client, mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "/help" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_today_command_success(self, sample_daily_pair):
        """Should send halachot for /today."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        await handle_command(mock_bot, 12345, "/today", mock_client, mock_selector)

        # Should have sent at least one message
        assert mock_bot.send_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_today_command_no_pair(self):
        """Should send error when no pair available."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_client = MagicMock()
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.return_value = None

        await handle_command(mock_bot, 12345, "/today", mock_client, mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "נסה שוב" in call_kwargs["text"]
