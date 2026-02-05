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
    async def test_handle_start_command(self, sample_daily_pair):
        """Should send welcome + daily content for /start."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        await handle_command(mock_bot, 12345, "/start", mock_selector)

        # Should send welcome + content (at least 2 messages)
        assert mock_bot.send_message.call_count >= 2
        first_call_kwargs = mock_bot.send_message.call_args_list[0][1]
        assert first_call_kwargs["chat_id"] == 12345
        assert "ליקוטי הלכות יומי" in first_call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_today_command(self, sample_daily_pair):
        """Should send just content (no welcome) for /today."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        await handle_command(mock_bot, 12345, "/today", mock_selector)

        # Should send content (at least 1 message)
        assert mock_bot.send_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_handle_info_command(self):
        """Should send info message for /info."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/info", mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "ליקוטי הלכות" in call_kwargs["text"]
        assert "/today" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_about_command_backwards_compat(self):
        """Should send info message for /about (backwards compat)."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/about", mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "ליקוטי הלכות" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_help_command_backwards_compat(self):
        """Should send info message for /help (backwards compat)."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/help", mock_selector)

        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "/today" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self):
        """Should silently ignore unknown commands."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()

        await handle_command(mock_bot, 12345, "/unknown", mock_selector)

        # Unknown commands are silently ignored
        mock_bot.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_today_command_no_pair(self):
        """Should send error when no pair available."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = None

        await handle_command(mock_bot, 12345, "/today", mock_selector)

        # Should send error message
        assert mock_bot.send_message.call_count == 1
        call_kwargs = mock_bot.send_message.call_args[1]
        assert "נסה שוב" in call_kwargs["text"]

    @pytest.mark.asyncio
    async def test_handle_command_with_cached_messages(self, sample_daily_pair):
        """Should use cached messages for instant response."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = [
            "cached1",
            "cached2",
            "cached3",
        ]

        await handle_command(mock_bot, 12345, "/start", mock_selector)

        # Should send cached messages
        assert mock_bot.send_message.call_count == 3
        # Should NOT call get_daily_pair (used cache)
        mock_selector.get_daily_pair.assert_not_called()


class TestPollAndRespondResilience:
    """Tests for network resilience in poll_and_respond."""

    @pytest.mark.asyncio
    async def test_timeout_retries_then_succeeds(self):
        """Should retry on timeout and succeed."""
        try:
            from telegram.error import TimedOut
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import poll_and_respond

        mock_bot = AsyncMock()
        # First call times out, second succeeds with no updates
        mock_bot.get_updates = AsyncMock(
            side_effect=[TimedOut(), []]
        )
        mock_bot.delete_webhook = AsyncMock(return_value=True)

        with (
            patch("scripts.poll_commands.Config") as mock_config_cls,
            patch("scripts.poll_commands.SefariaClient"),
            patch("scripts.poll_commands.HalachaSelector") as mock_sel_cls,
            patch("scripts.poll_commands.load_state", return_value=0),
            patch("scripts.poll_commands.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_config_cls.from_env.return_value = MagicMock(
                telegram_bot_token="fake-token"
            )
            mock_sel_cls.return_value.get_cached_messages.return_value = None

            with patch("telegram.Bot", return_value=mock_bot):
                # Make the bot work as async context manager
                mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
                mock_bot.__aexit__ = AsyncMock(return_value=False)

                result = await poll_and_respond()

        assert result is True
        assert mock_bot.get_updates.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_exhausted_returns_true(self):
        """Should return True (non-fatal) when all retries exhausted."""
        try:
            from telegram.error import TimedOut
        except ImportError:
            pytest.skip("telegram not available")

        from scripts.poll_commands import poll_and_respond

        mock_bot = AsyncMock()
        mock_bot.get_updates = AsyncMock(side_effect=TimedOut())
        mock_bot.delete_webhook = AsyncMock(return_value=True)

        with (
            patch("scripts.poll_commands.Config") as mock_config_cls,
            patch("scripts.poll_commands.SefariaClient"),
            patch("scripts.poll_commands.HalachaSelector") as mock_sel_cls,
            patch("scripts.poll_commands.load_state", return_value=0),
            patch("scripts.poll_commands.asyncio.sleep", new_callable=AsyncMock),
        ):
            mock_config_cls.from_env.return_value = MagicMock(
                telegram_bot_token="fake-token"
            )
            mock_sel_cls.return_value.get_cached_messages.return_value = None

            with patch("telegram.Bot", return_value=mock_bot):
                mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
                mock_bot.__aexit__ = AsyncMock(return_value=False)

                result = await poll_and_respond()

        # Should succeed (non-fatal) even when all retries fail
        assert result is True
        assert mock_bot.get_updates.call_count == 3
