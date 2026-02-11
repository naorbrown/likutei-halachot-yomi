"""Tests for TTS toggle behavior across all delivery paths.

Verifies that is_tts_enabled() is the single source of truth and
that all content delivery paths (broadcast, scheduled, poll commands)
respect the toggle correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config import Config
from src.tts import is_tts_enabled


class TestIsTTSEnabled:
    """Unit tests for the is_tts_enabled() function."""

    def test_returns_false_when_config_is_none(self):
        assert is_tts_enabled(None) is False

    def test_returns_false_when_disabled(self):
        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=False,
        )
        assert is_tts_enabled(config) is False

    def test_returns_true_when_enabled(self):
        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
        )
        assert is_tts_enabled(config) is True

    def test_enabled_without_credentials(self):
        """TTS enabled but no credentials still returns True.

        Credentials validation happens at synthesis time, not at the toggle.
        """
        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json=None,
        )
        assert is_tts_enabled(config) is True


class TestBroadcastRespectsToggle:
    """Verify send_daily_broadcast checks is_tts_enabled."""

    @pytest.mark.asyncio
    async def test_broadcast_calls_voice_when_enabled(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100123",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        mock_bot = AsyncMock()
        mock_result = MagicMock()
        mock_result.message_id = 1
        mock_bot.send_message.return_value = mock_result

        with (
            patch("src.bot.Bot", return_value=mock_bot),
            patch("src.bot.load_subscribers", return_value=set()),
            patch("src.bot.is_unified_channel_enabled", return_value=False),
            patch.object(bot_instance, "_send_voice_messages") as mock_voice,
        ):
            mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
            mock_bot.__aexit__ = AsyncMock(return_value=False)

            result = await bot_instance.send_daily_broadcast()

        assert result is True
        mock_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_skips_voice_when_disabled(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100123",
            google_tts_enabled=False,
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        mock_bot = AsyncMock()
        mock_result = MagicMock()
        mock_result.message_id = 1
        mock_bot.send_message.return_value = mock_result

        with (
            patch("src.bot.Bot", return_value=mock_bot),
            patch("src.bot.load_subscribers", return_value=set()),
            patch("src.bot.is_unified_channel_enabled", return_value=False),
            patch.object(bot_instance, "_send_voice_messages") as mock_voice,
        ):
            mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
            mock_bot.__aexit__ = AsyncMock(return_value=False)

            result = await bot_instance.send_daily_broadcast()

        assert result is True
        mock_voice.assert_not_called()


class TestScheduledBroadcastRespectsToggle:
    """Verify _scheduled_broadcast checks is_tts_enabled."""

    @pytest.mark.asyncio
    async def test_scheduled_calls_voice_when_enabled(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        mock_context = MagicMock()
        mock_context.bot = AsyncMock()

        with patch("src.bot.send_voice_for_pair") as mock_voice:
            await bot_instance._scheduled_broadcast(mock_context)

        mock_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_scheduled_skips_voice_when_disabled(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=False,
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        mock_context = MagicMock()
        mock_context.bot = AsyncMock()

        with patch("src.bot.send_voice_for_pair") as mock_voice:
            await bot_instance._scheduled_broadcast(mock_context)

        mock_voice.assert_not_called()


class TestPollCommandsRespectsToggle:
    """Verify poll_commands checks is_tts_enabled for /start and /today."""

    @pytest.mark.asyncio
    async def test_start_voice_when_enabled(self, sample_daily_pair):
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "sa"}',
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/start", mock_selector, config)

        mock_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_no_voice_when_disabled(self, sample_daily_pair):
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=False,
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/start", mock_selector, config)

        mock_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_today_voice_when_enabled(self, sample_daily_pair):
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "sa"}',
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/today", mock_selector, config)

        mock_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_today_no_voice_when_disabled(self, sample_daily_pair):
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=False,
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/today", mock_selector, config)

        mock_voice.assert_not_called()


class TestConsolidatedVoiceDelivery:
    """Verify _send_voice_messages delegates to send_voice_for_pair."""

    @pytest.mark.asyncio
    async def test_voice_sent_to_channel_and_subscribers(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "sa"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = AsyncMock()
        subscribers = {111, 222}

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.send_voice_for_pair") as mock_voice,
        ):
            mock_tts = MagicMock()
            mock_tts_cls.return_value = mock_tts

            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "c", subscribers
            )

        # 1 channel + 2 subscribers = 3 calls
        assert mock_voice.call_count == 3

    @pytest.mark.asyncio
    async def test_tts_client_reused_across_recipients(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "sa"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = AsyncMock()

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.send_voice_for_pair") as mock_voice,
        ):
            mock_tts = MagicMock()
            mock_tts_cls.return_value = mock_tts

            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "c", {111}
            )

        # HebrewTTSClient instantiated exactly once
        mock_tts_cls.assert_called_once()
        # All calls share the same _tts_client kwarg
        for call in mock_voice.call_args_list:
            assert call.kwargs.get("_tts_client") is mock_tts

    @pytest.mark.asyncio
    async def test_subscriber_failure_doesnt_block_others(self, sample_daily_pair):
        from src.bot import LikuteiHalachotBot

        config = Config(
            telegram_bot_token="t",
            telegram_chat_id="c",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "sa"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = AsyncMock()

        call_count = 0

        async def fail_for_first(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            chat_id = args[2] if len(args) > 2 else kwargs.get("chat_id")
            if chat_id == 111:
                raise Exception("Subscriber voice failed")

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch(
                "src.bot.send_voice_for_pair", side_effect=fail_for_first
            ) as mock_voice,
        ):
            mock_tts = MagicMock()
            mock_tts_cls.return_value = mock_tts

            # Should not raise
            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "c", {111, 222}
            )

        # All 3 recipients attempted (channel + 2 subs)
        assert mock_voice.call_count == 3
