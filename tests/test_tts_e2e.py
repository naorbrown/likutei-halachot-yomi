"""End-to-end tests for TTS across all content delivery paths.

Verifies that voice messages are sent alongside text messages
in every path: daily broadcast, scheduled broadcast, poll commands.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tts import send_voice_for_pair

# --- Standalone send_voice_for_pair tests ---


class TestSendVoiceForPair:
    """Tests for the standalone send_voice_for_pair function."""

    @pytest.mark.asyncio
    async def test_sends_two_voice_messages(self, sample_daily_pair):
        """Sends one voice message per halacha."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            await send_voice_for_pair(mock_bot, sample_daily_pair, 12345)

        assert mock_bot.send_voice.call_count == 2

    @pytest.mark.asyncio
    async def test_voice_captions_include_section_names(self, sample_daily_pair):
        """Voice message captions contain the section name."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            await send_voice_for_pair(mock_bot, sample_daily_pair, 12345)

        captions = [
            call.kwargs["caption"] for call in mock_bot.send_voice.call_args_list
        ]
        assert any("הלכות השכמת הבוקר" in c for c in captions)
        assert any("הלכות שחיטה" in c for c in captions)

    @pytest.mark.asyncio
    async def test_passes_credentials_to_tts_client(self, sample_daily_pair):
        """Credentials JSON is forwarded to HebrewTTSClient."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            await send_voice_for_pair(
                mock_bot, sample_daily_pair, 12345, credentials_json='{"key": "val"}'
            )

        mock_tts_cls.assert_called_once_with('{"key": "val"}')

    @pytest.mark.asyncio
    async def test_failure_does_not_raise(self, sample_daily_pair):
        """TTS failure is caught internally — never raises to caller."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts_cls.side_effect = Exception("credential error")

            # Should not raise
            await send_voice_for_pair(mock_bot, sample_daily_pair, 12345)

    @pytest.mark.asyncio
    async def test_partial_failure_sends_available(self, sample_daily_pair):
        """If one halacha's TTS fails, the other still sends."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.side_effect = [None, b"fake-audio"]
            mock_tts_cls.return_value = mock_tts

            await send_voice_for_pair(mock_bot, sample_daily_pair, 12345)

        assert mock_bot.send_voice.call_count == 1

    @pytest.mark.asyncio
    async def test_uses_send_voice_with_timeouts(self, sample_daily_pair):
        """Voice sends include increased timeouts for large files."""
        mock_bot = AsyncMock()

        with patch("src.tts.HebrewTTSClient") as mock_tts_cls:
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            await send_voice_for_pair(mock_bot, sample_daily_pair, 12345)

        for call in mock_bot.send_voice.call_args_list:
            assert call.kwargs["read_timeout"] == 30
            assert call.kwargs["write_timeout"] == 30


# --- Poll commands TTS integration ---


class TestPollCommandsTTS:
    """Tests for TTS in poll_commands.py /start and /today paths."""

    @pytest.mark.asyncio
    async def test_start_sends_voice_when_tts_enabled(self, sample_daily_pair):
        """The /start command sends voice messages when TTS is enabled."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/start", mock_selector, config)

        # Text messages sent
        assert mock_bot.send_message.call_count >= 2
        # Voice sent
        mock_voice.assert_called_once_with(
            mock_bot, sample_daily_pair, 12345, config.google_tts_credentials_json
        )

    @pytest.mark.asyncio
    async def test_today_sends_voice_when_tts_enabled(self, sample_daily_pair):
        """The /today command sends voice messages when TTS is enabled."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/today", mock_selector, config)

        # Text messages sent
        assert mock_bot.send_message.call_count >= 1
        # Voice sent
        mock_voice.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_voice_when_tts_disabled(self, sample_daily_pair):
        """No voice messages when TTS is disabled."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
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
    async def test_no_voice_when_config_is_none(self, sample_daily_pair):
        """No voice messages when config is not passed (backwards compat)."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            # config=None (default) — no voice
            await handle_command(mock_bot, 12345, "/start", mock_selector)

        mock_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_info_command_no_voice(self):
        """The /info command never sends voice (no daily content)."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()

        with patch("scripts.poll_commands.send_voice_for_pair") as mock_voice:
            await handle_command(mock_bot, 12345, "/info", mock_selector, config)

        mock_voice.assert_not_called()

    @pytest.mark.asyncio
    async def test_voice_failure_doesnt_block_text(self, sample_daily_pair):
        """TTS failure in poll commands doesn't prevent text delivery."""
        try:
            from scripts.poll_commands import handle_command
        except ImportError:
            pytest.skip("telegram not available")

        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
        )

        mock_bot = AsyncMock()
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        with patch(
            "scripts.poll_commands.send_voice_for_pair",
            side_effect=Exception("TTS crashed"),
        ):
            # Should not raise — text is already sent before voice
            await handle_command(mock_bot, 12345, "/today", mock_selector, config)

        # Text messages still sent despite voice failure
        assert mock_bot.send_message.call_count >= 1


# --- Scheduled broadcast TTS integration ---


class TestScheduledBroadcastTTS:
    """Tests for TTS in bot.py _scheduled_broadcast path."""

    @pytest.mark.asyncio
    async def test_scheduled_broadcast_sends_voice(self, sample_daily_pair):
        """Scheduled broadcast sends voice after text when TTS enabled."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

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

        # Text messages sent
        assert mock_context.bot.send_message.call_count >= 1
        # Voice sent
        mock_voice.assert_called_once_with(
            mock_context.bot,
            sample_daily_pair,
            "fake-chat",
            credentials_json='{"type": "service_account"}',
        )

    @pytest.mark.asyncio
    async def test_scheduled_broadcast_no_voice_when_disabled(self, sample_daily_pair):
        """Scheduled broadcast skips voice when TTS disabled."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

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


# --- Full broadcast flow TTS integration ---


class TestBroadcastFlowTTS:
    """Tests for TTS in the full daily broadcast flow."""

    @pytest.mark.asyncio
    async def test_broadcast_sends_text_then_voice(self, sample_daily_pair):
        """Full broadcast sends text messages first, then voice messages."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100123456",
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
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
            mock_bot.__aexit__ = AsyncMock(return_value=False)

            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            result = await bot_instance.send_daily_broadcast()

        assert result is True
        # Text messages sent
        assert mock_bot.send_message.call_count >= 1
        # Voice messages sent (2 halachot)
        assert mock_bot.send_voice.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_voice_failure_still_succeeds(self, sample_daily_pair):
        """Broadcast returns True even when voice delivery fails."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100123456",
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
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            mock_bot.__aenter__ = AsyncMock(return_value=mock_bot)
            mock_bot.__aexit__ = AsyncMock(return_value=False)

            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.side_effect = Exception("TTS exploded")
            mock_tts_cls.return_value = mock_tts

            result = await bot_instance.send_daily_broadcast()

        # Broadcast succeeds despite TTS failure
        assert result is True
        # Text still delivered
        assert mock_bot.send_message.call_count >= 1
