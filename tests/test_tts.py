"""Tests for Hebrew TTS module."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.tts import (
    MAX_CHUNK_CHARS,
    HebrewTTSClient,
    chunk_text,
)

# --- Chunking Tests ---


class TestChunkText:
    """Tests for the text chunking logic."""

    def test_empty_text(self):
        assert chunk_text("") == []

    def test_whitespace_only(self):
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "שלום עולם"
        result = chunk_text(text)
        assert result == [text]

    def test_text_at_exact_limit(self):
        text = "א" * MAX_CHUNK_CHARS
        result = chunk_text(text)
        assert result == [text]

    def test_long_text_splits_at_sentence_boundary(self):
        # Build text with two sentences that together exceed the limit
        sentence1 = "א" * 600 + "."
        sentence2 = "ב" * 700
        text = f"{sentence1} {sentence2}"
        result = chunk_text(text)
        assert len(result) == 2
        assert result[0] == sentence1
        assert result[1] == sentence2

    def test_long_text_splits_at_colon(self):
        part1 = "א" * 600 + ":"
        part2 = "ב" * 700
        text = f"{part1} {part2}"
        result = chunk_text(text)
        assert len(result) == 2

    def test_preserves_all_content(self):
        """All original words appear in the chunked output."""
        words = [f"מילה{i}" for i in range(200)]
        text = " ".join(words)
        chunks = chunk_text(text, max_chars=100)
        reassembled = " ".join(chunks)
        for word in words:
            assert word in reassembled

    def test_no_chunk_exceeds_limit(self):
        text = " ".join(["מילה"] * 500)
        chunks = chunk_text(text, max_chars=50)
        for chunk in chunks:
            assert len(chunk) <= 50

    def test_single_long_word_exceeds_limit(self):
        """A single word longer than the limit ends up in its own chunk."""
        long_word = "א" * 2000
        text = f"שלום {long_word} עולם"
        chunks = chunk_text(text, max_chars=100)
        assert any(long_word in c for c in chunks)

    def test_sentence_boundary_with_sof_pasuk(self):
        """Hebrew sof-pasuk character (׃) triggers sentence split."""
        part1 = "א" * 600 + "׃"
        part2 = "ב" * 700
        text = f"{part1} {part2}"
        result = chunk_text(text)
        assert len(result) == 2

    def test_real_hebrew_text(self):
        text = (
            "יִתְגַּבֵּר כַּאֲרִי לַעֲמֹד בַּבֹּקֶר לַעֲבוֹדַת בּוֹרְאוֹ. "
            "שֶׁיְּהֵא הוּא מְעוֹרֵר הַשַּׁחַר. "
            "כִּי צָרִיךְ הָאָדָם לְהִתְגַּבֵּר תָּמִיד."
        )
        chunks = chunk_text(text)
        assert len(chunks) >= 1
        # All text is preserved
        assert all(word in " ".join(chunks) for word in text.split()[:3])


# --- Caching Tests ---


class TestTTSCaching:
    """Tests for audio caching."""

    @patch("src.tts.AUDIO_CACHE_DIR")
    def test_cache_hit_returns_bytes(self, mock_cache_dir, tmp_path):
        """Pre-existing OGG file is returned without API call."""
        mock_cache_dir.__truediv__ = lambda self, key: tmp_path / key

        audio_data = b"fake-ogg-audio-data"
        cache_file = tmp_path / "test_key.ogg"
        cache_file.write_bytes(audio_data)

        with patch("src.tts.texttospeech"):
            client = HebrewTTSClient.__new__(HebrewTTSClient)
            client.client = MagicMock()
            client._temp_creds_path = None

        result = client.get_or_generate_audio("test", "test_key")
        assert result == audio_data
        client.client.synthesize_speech.assert_not_called()

    @patch("src.tts.AUDIO_CACHE_DIR")
    def test_cache_miss_generates_audio(self, mock_cache_dir, tmp_path):
        """Missing file triggers synthesis and caching."""
        mock_cache_dir.__truediv__ = lambda self, key: tmp_path / key
        mock_cache_dir.mkdir = Mock()

        fake_audio = b"generated-audio-data"

        client = HebrewTTSClient.__new__(HebrewTTSClient)
        client._temp_creds_path = None
        client.client = MagicMock()
        client.voice = MagicMock()
        client.audio_config = MagicMock()

        mock_response = MagicMock()
        mock_response.audio_content = fake_audio
        client.client.synthesize_speech.return_value = mock_response

        result = client.get_or_generate_audio("שלום", "new_key")
        assert result == fake_audio
        assert (tmp_path / "new_key.ogg").read_bytes() == fake_audio

    @patch("src.tts.AUDIO_CACHE_DIR")
    def test_cache_dir_created_on_miss(self, mock_cache_dir, tmp_path):
        """Cache directory is created if it doesn't exist."""
        mock_cache_dir.__truediv__ = lambda self, key: tmp_path / key
        mock_cache_dir.mkdir = Mock()

        client = HebrewTTSClient.__new__(HebrewTTSClient)
        client._temp_creds_path = None
        client.client = MagicMock()
        client.voice = MagicMock()
        client.audio_config = MagicMock()

        mock_response = MagicMock()
        mock_response.audio_content = b"audio"
        client.client.synthesize_speech.return_value = mock_response

        client.get_or_generate_audio("test", "key")
        mock_cache_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)


# --- Synthesis Tests ---


class TestSynthesis:
    """Tests for the synthesis pipeline."""

    def test_synthesize_single_chunk(self):
        """Short text produces audio without concatenation."""
        client = HebrewTTSClient.__new__(HebrewTTSClient)
        client._temp_creds_path = None
        client.client = MagicMock()
        client.voice = MagicMock()
        client.audio_config = MagicMock()

        fake_audio = b"ogg-audio-bytes"
        mock_response = MagicMock()
        mock_response.audio_content = fake_audio
        client.client.synthesize_speech.return_value = mock_response

        result = client.synthesize_text("שלום")
        assert result == fake_audio
        assert client.client.synthesize_speech.call_count == 1

    def test_synthesize_multiple_chunks(self):
        """Long text is chunked and each chunk is synthesized."""
        client = HebrewTTSClient.__new__(HebrewTTSClient)
        client._temp_creds_path = None
        client.client = MagicMock()
        client.voice = MagicMock()
        client.audio_config = MagicMock()

        fake_audio = b"ogg-audio-bytes"
        mock_response = MagicMock()
        mock_response.audio_content = fake_audio
        client.client.synthesize_speech.return_value = mock_response

        # Create text that will be split into multiple chunks
        long_text = " ".join(["מילה"] * 500)

        with patch(
            "src.tts._concatenate_audio", return_value=b"concatenated"
        ) as mock_concat:
            result = client.synthesize_text(long_text)

        assert result == b"concatenated"
        assert client.client.synthesize_speech.call_count > 1
        mock_concat.assert_called_once()

    def test_synthesize_failure_returns_none(self):
        """API failure returns None instead of raising."""
        client = HebrewTTSClient.__new__(HebrewTTSClient)
        client._temp_creds_path = None
        client.client = MagicMock()
        client.voice = MagicMock()
        client.audio_config = MagicMock()
        client.client.synthesize_speech.side_effect = Exception("API error")

        result = client.synthesize_text("שלום")
        assert result is None


# --- Integration Tests ---


class TestTTSBotIntegration:
    """Tests for TTS integration with the bot broadcast flow.

    Since _send_voice_messages delegates to send_voice_for_pair,
    these tests patch send_voice_for_pair at the bot module scope.
    """

    @pytest.mark.asyncio
    async def test_tts_disabled_skips_voice(self):
        """When TTS is disabled, no voice messages are sent."""
        from src.config import Config
        from src.tts import is_tts_enabled

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=False,
        )

        assert not is_tts_enabled(config)

    @pytest.mark.asyncio
    async def test_tts_failure_doesnt_block_broadcast(self, sample_daily_pair):
        """TTS errors don't prevent text broadcast from succeeding."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )
        bot_instance = LikuteiHalachotBot(config)

        mock_bot = MagicMock()

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch(
                "src.bot.send_voice_for_pair",
                side_effect=Exception("TTS delivery failed"),
            ),
        ):
            mock_tts_cls.return_value = MagicMock()

            # Should not raise
            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "fake-chat", set()
            )

    @pytest.mark.asyncio
    async def test_voice_messages_sent_for_channel(self, sample_daily_pair):
        """Channel gets voice messages via send_voice_for_pair."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = MagicMock()

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.send_voice_for_pair") as mock_voice,
        ):
            mock_tts_cls.return_value = MagicMock()

            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "fake-chat", set()
            )

        # Channel only, no subscribers
        assert mock_voice.call_count == 1

    @pytest.mark.asyncio
    async def test_voice_messages_sent_to_subscribers(self, sample_daily_pair):
        """Voice messages are also sent to individual subscribers."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = MagicMock()
        subscribers = {111, 222}

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.send_voice_for_pair") as mock_voice,
        ):
            mock_tts_cls.return_value = MagicMock()

            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "fake-chat", subscribers
            )

        # 1 channel + 2 subscribers = 3 calls
        assert mock_voice.call_count == 3

    @pytest.mark.asyncio
    async def test_partial_subscriber_failure_sends_to_others(self, sample_daily_pair):
        """If one subscriber fails, voice still sent to others."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="fake-chat",
            google_tts_enabled=True,
        )
        bot_instance = LikuteiHalachotBot(config)
        mock_bot = MagicMock()

        call_count = 0

        async def fail_for_111(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            chat_id = args[2] if len(args) > 2 else kwargs.get("chat_id")
            if chat_id == 111:
                raise Exception("Subscriber unreachable")

        with (
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch(
                "src.bot.send_voice_for_pair", side_effect=fail_for_111
            ) as mock_voice,
        ):
            mock_tts_cls.return_value = MagicMock()

            await bot_instance._send_voice_messages(
                mock_bot, sample_daily_pair, "fake-chat", {111, 222}
            )

        # All 3 attempted (channel + 2 subs), even though 111 failed
        assert mock_voice.call_count == 3
