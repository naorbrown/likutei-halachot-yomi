"""Tests for the poll commands script."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from scripts.poll_commands import (
    RateLimiter,
    StateManager,
    convert_masechta_name,
    parse_command,
)


class TestStateManagement:
    """Tests for state loading and saving."""

    def test_load_state_no_file(self, tmp_path):
        """Should return None when state file doesn't exist."""
        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "nonexistent.json"),
        ):
            state = StateManager()
            assert state.get_last_update_id() is None

    def test_load_state_with_file(self, tmp_path):
        """Should return saved update ID."""
        state_file = tmp_path / "state.json"
        state_file.write_text('{"last_update_id": 12345}')

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", state_file),
        ):
            state = StateManager()
            assert state.get_last_update_id() == 12345

    def test_load_state_invalid_json(self, tmp_path):
        """Should return None for invalid JSON."""
        state_file = tmp_path / "state.json"
        state_file.write_text("not valid json")

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", state_file),
        ):
            state = StateManager()
            assert state.get_last_update_id() is None

    def test_save_state(self, tmp_path):
        """Should save state to file."""
        state_file = tmp_path / "state.json"

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", state_file),
        ):
            state = StateManager()
            state.set_last_update_id(99999)

        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["last_update_id"] == 99999


class TestRateLimiter:
    """Tests for rate limiting."""

    def test_allows_initial_request(self, tmp_path):
        """Should allow the first request."""
        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            assert limiter.is_allowed(123) is True

    def test_blocks_after_limit(self, tmp_path):
        """Should block after max requests."""
        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
            patch("scripts.poll_commands.RATE_LIMIT_MAX_REQUESTS", 3),
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            assert limiter.is_allowed(123) is True
            assert limiter.is_allowed(123) is True
            assert limiter.is_allowed(123) is True
            assert limiter.is_allowed(123) is False


class TestParseCommand:
    """Tests for command parsing."""

    def test_parse_simple_command(self):
        assert parse_command("/start") == "start"

    def test_parse_command_with_bot_name(self):
        assert parse_command("/today@mybot") == "today"

    def test_parse_no_command(self):
        assert parse_command("hello") is None

    def test_parse_empty(self):
        assert parse_command("") is None

    def test_parse_none(self):
        assert parse_command(None) is None


class TestConvertMasechta:
    """Tests for masechta name conversion."""

    def test_mapped_name(self):
        assert convert_masechta_name("Berakhot") == "Berachos"

    def test_unmapped_name(self):
        assert convert_masechta_name("Sanhedrin") == "Sanhedrin"


class TestHandleCommand:
    """Tests for command handling."""

    @pytest.mark.asyncio
    async def test_handle_start_sends_welcome(self, tmp_path):
        """Should send welcome message for /start."""
        from scripts.poll_commands import TelegramAPI, handle_command

        api = AsyncMock(spec=TelegramAPI)

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
            patch("scripts.poll_commands.SUBSCRIBERS_FILE", tmp_path / "subs.json"),
            patch("scripts.poll_commands.VIDEO_CACHE_FILE", tmp_path / "cache.json"),
            patch("scripts.poll_commands.send_todays_video", new_callable=AsyncMock),
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            await handle_command(api, 12345, "start", limiter, 99, state)

        # Should send welcome message
        api.send_message.assert_called_once()
        call_args = api.send_message.call_args
        assert call_args[0][0] == 12345  # chat_id
        assert "Welcome" in call_args[0][1] or "welcome" in call_args[0][1].lower()

    @pytest.mark.asyncio
    async def test_handle_today_sends_video(self, tmp_path):
        """Should send today's video for /today."""
        from scripts.poll_commands import TelegramAPI, handle_command

        api = AsyncMock(spec=TelegramAPI)

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
            patch("scripts.poll_commands.VIDEO_CACHE_FILE", tmp_path / "cache.json"),
            patch(
                "scripts.poll_commands.send_todays_video", new_callable=AsyncMock
            ) as mock_send,
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            await handle_command(api, 12345, "today", limiter, 99, state)

        mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_unknown_command_ignored(self, tmp_path):
        """Should silently ignore unknown commands."""
        from scripts.poll_commands import TelegramAPI, handle_command

        api = AsyncMock(spec=TelegramAPI)

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
            patch("scripts.poll_commands.VIDEO_CACHE_FILE", tmp_path / "cache.json"),
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            await handle_command(api, 12345, "unknown", limiter, 99, state)

        api.send_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_rate_limited_user_gets_message(self, tmp_path):
        """Should send rate limit message when user exceeds limit."""
        from scripts.poll_commands import TelegramAPI, handle_command

        api = AsyncMock(spec=TelegramAPI)

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
            patch("scripts.poll_commands.RATE_LIMIT_FILE", tmp_path / "rates.json"),
            patch("scripts.poll_commands.VIDEO_CACHE_FILE", tmp_path / "cache.json"),
            patch("scripts.poll_commands.RATE_LIMIT_MAX_REQUESTS", 0),
        ):
            state = StateManager()
            limiter = RateLimiter(state)
            await handle_command(api, 12345, "today", limiter, 99, state)

        api.send_message.assert_called_once()
        assert "Too many" in api.send_message.call_args[0][1]
