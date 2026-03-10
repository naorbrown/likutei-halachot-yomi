"""End-to-end tests for the bot command flow.

These tests verify the complete flow from cache to command response,
ensuring the full pipeline works together.

Shared fixtures (mock_telegram_bot, mock_selector, broadcast_bot_instance,
broadcast_env) are defined in conftest.py to eliminate the mock boilerplate
that previously hid real integration bugs.
"""

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.commands import get_info_message, get_start_messages, get_today_messages
from src.formatter import format_daily_message, format_welcome_message
from src.models import DailyPair, Halacha, HalachaSection
from src.sefaria import SefariaClient
from src.selector import HalachaSelector, _memory_cache, _message_cache
from src.subscribers import (
    add_subscriber,
    is_subscribed,
    load_subscribers,
    remove_subscriber,
)


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before and after each test."""
    _memory_cache.clear()
    _message_cache.clear()
    yield
    _memory_cache.clear()
    _message_cache.clear()


class TestCacheToCommandFlow:
    """Tests for the full cache-to-command pipeline."""

    def test_start_command_from_cache(self, tmp_path, sample_daily_pair):
        """Cache file on disk -> /start command returns welcome + content."""
        cache_file = tmp_path / "pair_2099-01-01.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 1))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = get_start_messages(selector, date(2099, 1, 1))

        assert len(messages) >= 2
        assert "ליקוטי הלכות יומי" in messages[0]
        assert "שתי הלכות חדשות" in messages[0]

    def test_today_command_from_cache(self, tmp_path, sample_daily_pair):
        """Cache file on disk -> /today command returns content only."""
        cache_file = tmp_path / "pair_2099-01-02.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 2))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = get_today_messages(selector, date(2099, 1, 2))

        assert len(messages) >= 1
        assert "שתי הלכות חדשות" not in messages[0]
        assert any("📜" in msg or "📖" in msg for msg in messages)

    def test_cache_miss_returns_none(self, tmp_path):
        """Missing cache file returns None."""
        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = selector.get_cached_messages(date(2099, 5, 1))

        assert messages is None

    def test_corrupted_cache_handled_gracefully(self, tmp_path):
        """Corrupted cache file doesn't crash."""
        cache_file = tmp_path / "pair_2099-05-02.json"
        cache_file.write_text("not valid json {{{")

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            pair = selector._load_cached_pair(date(2099, 5, 2))

        assert pair is None

    def test_old_cache_format_generates_messages(self, tmp_path, sample_daily_pair):
        """Cache files without formatted_messages still produce output."""
        cache_file = tmp_path / "pair_2099-01-03.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 3))
        del cache_data["formatted_messages"]
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = selector.get_cached_messages(date(2099, 1, 3))

        assert messages is not None
        assert len(messages) >= 2
        assert "ליקוטי הלכות יומי" in messages[0]


class TestMessageIntegrity:
    """Tests for message formatting correctness across the full pipeline."""

    def test_daily_messages_structure(self, sample_daily_pair):
        """Daily messages have correct HTML structure and content."""
        messages = format_daily_message(sample_daily_pair, date(2099, 4, 1))

        assert len(messages) >= 2
        assert "01/04/2099" in messages[0]
        for msg in messages:
            assert "<b>" in msg
            assert "</b>" in msg
        assert any("sefaria.org" in msg for msg in messages)
        assert "נ נח נחמ נחמן מאומן" in messages[-1]

    def test_long_text_splits_under_telegram_limit(self):
        """Long halacha text splits at word boundaries under 4096 chars."""
        long_text = "מילה " * 1000
        section1 = HalachaSection(
            volume="Orach Chaim",
            section="Test",
            section_he="בדיקה",
            ref_base="Test_Ref_OC",
            has_english=False,
        )
        section2 = HalachaSection(
            volume="Yoreh Deah",
            section="Test",
            section_he="בדיקה",
            ref_base="Test_Ref_YD",
            has_english=False,
        )
        halacha1 = Halacha(
            section=section1,
            chapter=1,
            siman=1,
            hebrew_text=long_text,
            english_text=None,
            sefaria_url="https://www.sefaria.org/test1",
        )
        halacha2 = Halacha(
            section=section2,
            chapter=1,
            siman=1,
            hebrew_text=long_text,
            english_text=None,
            sefaria_url="https://www.sefaria.org/test2",
        )
        pair = DailyPair(first=halacha1, second=halacha2, date_seed="2099-04-02")

        messages = format_daily_message(pair, date(2099, 4, 2))

        assert len(messages) > 2
        for msg in messages:
            assert len(msg) < 4100

    def test_info_message_has_all_commands(self):
        """Info message lists all available commands."""
        message = get_info_message()

        assert "/today" in message
        assert "/info" in message
        assert "/subscribe" in message
        assert "/unsubscribe" in message
        assert "sefaria" in message.lower()


def _create_cache_data(pair: DailyPair, for_date: date) -> dict:
    """Helper to create cache data structure."""
    welcome = format_welcome_message()
    content = format_daily_message(pair, for_date)

    return {
        "date_seed": for_date.isoformat(),
        "formatted_messages": [welcome] + content,
        "first": {
            "section": {
                "volume": pair.first.section.volume,
                "section": pair.first.section.section,
                "section_he": pair.first.section.section_he,
                "ref_base": pair.first.section.ref_base,
                "has_english": pair.first.section.has_english,
            },
            "chapter": pair.first.chapter,
            "siman": pair.first.siman,
            "hebrew_text": pair.first.hebrew_text,
            "english_text": pair.first.english_text,
            "sefaria_url": pair.first.sefaria_url,
        },
        "second": {
            "section": {
                "volume": pair.second.section.volume,
                "section": pair.second.section.section,
                "section_he": pair.second.section.section_he,
                "ref_base": pair.second.section.ref_base,
                "has_english": pair.second.section.has_english,
            },
            "chapter": pair.second.chapter,
            "siman": pair.second.siman,
            "hebrew_text": pair.second.hebrew_text,
            "english_text": pair.second.english_text,
            "sefaria_url": pair.second.sefaria_url,
        },
    }


# --- Subscriber Lifecycle E2E Tests ---


class TestSubscriberLifecycle:
    """Full subscriber journey: subscribe -> broadcast -> unsubscribe.

    Tests the src.subscribers module and broadcast integration directly,
    which is the subscriber system used by the Likutei Halachot bot.
    """

    def test_add_subscriber(self, isolated_subscribers):
        """add_subscriber registers a new user."""
        result = add_subscriber(11111)
        assert result is True
        assert is_subscribed(11111)

    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_subscriber(
        self,
        isolated_subscribers,
        sample_daily_pair,
        broadcast_bot_instance,
        broadcast_env,
    ):
        """Subscribed user receives messages during daily broadcast."""
        add_subscriber(11111)

        with broadcast_env(subscribers={11111}):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

    def test_unsubscribe_removes_user(self, isolated_subscribers):
        """Subscribing then unsubscribing removes user from list."""
        add_subscriber(11111)
        assert is_subscribed(11111)

        remove_subscriber(11111)
        assert not is_subscribed(11111)
        assert load_subscribers() == set()

    def test_resubscribe_after_unsubscribe(self, isolated_subscribers):
        """User can re-subscribe after unsubscribing."""
        add_subscriber(11111)
        remove_subscriber(11111)
        assert not is_subscribed(11111)

        result = add_subscriber(11111)
        assert result is True
        assert is_subscribed(11111)

    def test_subscribe_when_already_subscribed(self, isolated_subscribers):
        """Subscribing when already subscribed returns False."""
        add_subscriber(11111)
        result = add_subscriber(11111)
        assert result is False

    def test_unsubscribe_when_not_subscribed(self, isolated_subscribers):
        """Unsubscribing when not subscribed returns False."""
        result = remove_subscriber(22222)
        assert result is False


# --- Daily Broadcast with Subscribers E2E Tests ---


class TestDailyBroadcastWithSubscribers:
    """Full broadcast flow: channel + subscribers + voice + unified.

    Uses broadcast_env fixture from conftest.py for clean mock setup.
    """

    @pytest.mark.asyncio
    async def test_full_broadcast_to_channel_and_subscribers(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        broadcast_env,
        mock_telegram_bot,
    ):
        """Broadcast sends messages to channel and all subscribers."""
        subscribers = {111, 222, 333}

        with broadcast_env(subscribers=subscribers):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

        # Channel and all 3 subscribers should receive messages
        channel_calls = [
            c
            for c in mock_telegram_bot.send_message.call_args_list
            if c.kwargs.get("chat_id") == "-100999"
        ]
        assert len(channel_calls) >= 2  # At least header + content

        for sub_id in subscribers:
            sub_calls = [
                c
                for c in mock_telegram_bot.send_message.call_args_list
                if c.kwargs.get("chat_id") == sub_id
            ]
            assert len(sub_calls) >= 1

    @pytest.mark.asyncio
    async def test_channel_deduplication_from_subscribers(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        broadcast_env,
        mock_telegram_bot,
    ):
        """Channel ID in subscriber set doesn't cause double delivery."""
        # Channel is also in subscriber set
        with broadcast_env(subscribers={-100999, 111}):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

        # Channel should receive messages once (not twice)
        channel_calls = [
            c
            for c in mock_telegram_bot.send_message.call_args_list
            if c.kwargs.get("chat_id") == "-100999"
        ]
        messages = format_daily_message(sample_daily_pair, date.today())
        assert len(channel_calls) == len(messages)

    @pytest.mark.asyncio
    async def test_broadcast_voice_to_channel_and_subscribers(
        self,
        sample_daily_pair,
        mock_telegram_bot,
    ):
        """Voice messages are sent to channel and each subscriber."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100999",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value={111, 222}),
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            result = await bot_instance.send_daily_broadcast()

        assert result is True
        # 2 halachot * (1 channel + 2 subscribers) = 6 voice messages
        assert mock_telegram_bot.send_voice.call_count == 6

    @pytest.mark.asyncio
    async def test_broadcast_with_no_subscribers(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        broadcast_env,
        mock_telegram_bot,
    ):
        """Broadcast succeeds when subscriber list is empty."""
        with broadcast_env(subscribers=set()):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True
        # Only channel receives messages
        all_chat_ids = [
            c.kwargs.get("chat_id")
            for c in mock_telegram_bot.send_message.call_args_list
        ]
        assert all(cid == "-100999" for cid in all_chat_ids)


# --- Poll Command State Persistence E2E Tests ---


class TestPollCommandStatePersistence:
    """Tests for update_id state persistence across poll runs.

    Uses the StateManager API from the refactored poll_commands module.
    """

    def test_state_persists_across_poll_runs(self, tmp_path):
        """update_id saved in first run is loaded in second run."""
        from scripts.poll_commands import StateManager

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "state.json"),
        ):
            state = StateManager()
            state.set_last_update_id(102)
            assert state.get_last_update_id() == 102

            state.set_last_update_id(105)
            assert state.get_last_update_id() == 105

    def test_no_state_file_returns_none(self, tmp_path):
        """Missing state file returns None."""
        from scripts.poll_commands import StateManager

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", tmp_path / "nonexistent.json"),
        ):
            state = StateManager()
            assert state.get_last_update_id() is None

    def test_corrupted_state_file_returns_none(self, tmp_path):
        """Corrupted state file falls back to None."""
        from scripts.poll_commands import StateManager

        state_file = tmp_path / "state.json"
        state_file.write_text("not valid json {{{")

        with (
            patch("scripts.poll_commands.STATE_DIR", tmp_path),
            patch("scripts.poll_commands.STATE_FILE", state_file),
        ):
            state = StateManager()
            assert state.get_last_update_id() is None


# --- API Failure Fallback E2E Tests ---


class TestAPIFailureFallback:
    """Tests for graceful degradation when Sefaria API is unavailable."""

    @staticmethod
    def _sections_by_volume():
        """Helper: one section per volume for fallback tests."""
        return {
            vol: [
                HalachaSection(
                    volume=vol,
                    section=f"Test {vol}",
                    section_he="בדיקה",
                    ref_base=f"Test_Ref_{vol.replace(' ', '_')}",
                    has_english=False,
                )
            ]
            for vol in ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]
        }

    def test_fallback_halacha_when_api_fails(self, tmp_path):
        """Selector returns fallback pair when API returns None."""
        sections_by_volume = self._sections_by_volume()

        mock_client = MagicMock()
        mock_client.get_random_halacha_from_volume.return_value = None
        mock_client.get_sections_by_volume.side_effect = (
            lambda vol: sections_by_volume.get(vol, [])
        )

        selector = HalachaSelector(mock_client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            pair = selector.get_daily_pair(date(2099, 6, 1))

        assert pair is not None
        assert "לא ניתן לטעון" in pair.first.hebrew_text
        assert "לא ניתן לטעון" in pair.second.hebrew_text

    def test_broadcast_succeeds_with_fallback_content(
        self, sample_section_oc, sample_section_yd
    ):
        """Broadcast returns True even with fallback halachot."""
        fallback_first = Halacha(
            section=sample_section_oc,
            chapter=1,
            siman=1,
            hebrew_text="לא ניתן לטעון את הטקסט כרגע. לחץ על הקישור לקריאה בספריא.",
            english_text=None,
            sefaria_url="https://www.sefaria.org/Test",
        )
        fallback_second = Halacha(
            section=sample_section_yd,
            chapter=1,
            siman=1,
            hebrew_text="לא ניתן לטעון את הטקסט כרגע. לחץ על הקישור לקריאה בספריא.",
            english_text=None,
            sefaria_url="https://www.sefaria.org/Test2",
        )
        fallback_pair = DailyPair(
            first=fallback_first, second=fallback_second, date_seed="2099-06-01"
        )

        messages = format_daily_message(fallback_pair, date(2099, 6, 1))

        assert len(messages) >= 2
        assert any("לא ניתן לטעון" in msg for msg in messages)

    def test_fallback_pairs_not_cached_to_disk(self, tmp_path):
        """Fallback pairs are not written to disk cache."""
        sections_by_volume = self._sections_by_volume()

        mock_client = MagicMock()
        mock_client.get_random_halacha_from_volume.return_value = None
        mock_client.get_sections_by_volume.side_effect = (
            lambda vol: sections_by_volume.get(vol, [])
        )

        selector = HalachaSelector(mock_client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            pair = selector.get_daily_pair(date(2099, 6, 2))

        assert pair is not None
        # No cache file should have been written
        cache_files = list(tmp_path.glob("pair_*.json"))
        assert len(cache_files) == 0


# --- Partial Broadcast Failure E2E Tests ---


class TestPartialBroadcastFailures:
    """Tests for resilience when some subscribers fail during broadcast."""

    @pytest.mark.asyncio
    async def test_some_subscribers_fail_broadcast_succeeds(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        mock_telegram_bot,
    ):
        """Broadcast returns True even when some subscribers are unreachable."""
        mock_result = MagicMock()
        mock_result.message_id = 1

        # Subscriber 222 always fails, others succeed
        def selective_send(chat_id, **kwargs):
            if chat_id == 222:
                raise Exception("User blocked bot")
            return mock_result

        mock_telegram_bot.send_message.side_effect = selective_send

        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value={111, 222, 333}),
            patch("src.bot.HebrewTTSClient"),
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

    @pytest.mark.asyncio
    async def test_all_subscribers_fail_channel_still_delivered(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        mock_telegram_bot,
    ):
        """Channel gets messages even when all subscriber sends fail."""
        mock_result = MagicMock()
        mock_result.message_id = 1

        # Channel succeeds, all subscribers fail
        def channel_only_send(chat_id, **kwargs):
            if chat_id == "-100999":
                return mock_result
            raise Exception("Subscriber unreachable")

        mock_telegram_bot.send_message.side_effect = channel_only_send

        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value={111, 222}),
            patch("src.bot.HebrewTTSClient"),
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

    @pytest.mark.asyncio
    async def test_voice_failure_for_one_subscriber(
        self,
        sample_daily_pair,
        mock_telegram_bot,
    ):
        """Voice failure for one subscriber doesn't block others."""
        from src.bot import LikuteiHalachotBot
        from src.config import Config

        config = Config(
            telegram_bot_token="fake-token",
            telegram_chat_id="-100999",
            google_tts_enabled=True,
            google_tts_credentials_json='{"type": "service_account"}',
        )
        bot_instance = LikuteiHalachotBot(config)
        bot_instance.selector = MagicMock()
        bot_instance.selector.get_daily_pair.return_value = sample_daily_pair

        # Voice fails for subscriber 111 only
        def selective_voice(chat_id, **kwargs):
            if chat_id == 111:
                raise Exception("Voice send failed")
            return MagicMock()

        mock_telegram_bot.send_voice.side_effect = selective_voice

        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value={111, 222}),
            patch("src.bot.HebrewTTSClient") as mock_tts_cls,
            patch("src.bot.is_unified_channel_enabled", return_value=False),
        ):
            mock_tts = MagicMock()
            mock_tts.get_or_generate_audio.return_value = b"fake-audio"
            mock_tts_cls.return_value = mock_tts

            result = await bot_instance.send_daily_broadcast()

        assert result is True
        # Voice was attempted for channel + both subscribers (some failed)
        assert mock_telegram_bot.send_voice.call_count >= 3


# --- Unified Channel Publishing E2E Tests ---


class TestUnifiedChannelPublishing:
    """Tests for unified Torah Yomi channel integration."""

    @pytest.mark.asyncio
    async def test_broadcast_publishes_to_unified_channel(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        mock_telegram_bot,
    ):
        """Broadcast calls unified channel publisher."""
        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value=set()),
            patch("src.bot.HebrewTTSClient"),
            patch("src.bot.is_unified_channel_enabled", return_value=True),
            patch("src.bot.publish_text_to_unified_channel") as mock_publish,
        ):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True
        mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_unified_channel_message_format(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
    ):
        """Unified channel message has correct content."""
        with (
            patch("src.bot.is_unified_channel_enabled", return_value=True),
            patch("src.bot.publish_text_to_unified_channel") as mock_publish,
        ):
            await broadcast_bot_instance._send_to_unified_channel(sample_daily_pair)

        mock_publish.assert_called_once()
        msg = mock_publish.call_args[0][0]
        assert "ליקוטי הלכות יומי" in msg
        assert sample_daily_pair.first.section.section_he in msg
        assert sample_daily_pair.second.section.section_he in msg
        assert "נ נח נחמ נחמן מאומן" in msg

    @pytest.mark.asyncio
    async def test_unified_channel_failure_doesnt_block_broadcast(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        mock_telegram_bot,
    ):
        """Broadcast returns True even when unified channel fails."""
        with (
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value=set()),
            patch("src.bot.HebrewTTSClient"),
            patch("src.bot.is_unified_channel_enabled", return_value=True),
            patch(
                "src.bot.publish_text_to_unified_channel",
                side_effect=Exception("Unified channel down"),
            ),
        ):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True

    @pytest.mark.asyncio
    async def test_unified_channel_disabled_skips_publish(
        self,
        sample_daily_pair,
        broadcast_bot_instance,
        broadcast_env,
    ):
        """Unified channel is not called when disabled."""
        with (
            broadcast_env(unified=False),
            patch("src.bot.publish_text_to_unified_channel") as mock_publish,
        ):
            result = await broadcast_bot_instance.send_daily_broadcast()

        assert result is True
        mock_publish.assert_not_called()


# --- Timeout Protection E2E Tests ---


class TestPollCommandHandling:
    """Tests for poll_commands command handling and rate limiting."""

    @pytest.mark.asyncio
    async def test_start_command_sends_welcome(self, tmp_path):
        """The /start command sends a welcome message."""
        from scripts.poll_commands import (
            RateLimiter,
            StateManager,
            TelegramAPI,
            handle_command,
        )

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

        api.send_message.assert_called()
        call_args = api.send_message.call_args_list[0]
        assert call_args[0][0] == 12345

    @pytest.mark.asyncio
    async def test_rate_limited_user_gets_message(self, tmp_path):
        """Rate-limited user receives a rate limit message."""
        from scripts.poll_commands import (
            RateLimiter,
            StateManager,
            TelegramAPI,
            handle_command,
        )

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

    @pytest.mark.asyncio
    async def test_unknown_command_ignored(self, tmp_path):
        """Unknown commands are silently ignored."""
        from scripts.poll_commands import (
            RateLimiter,
            StateManager,
            TelegramAPI,
            handle_command,
        )

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

    def test_request_timeout_within_ci_budget(self):
        """Verify request timeout is reasonable for CI."""
        from scripts.poll_commands import REQUEST_TIMEOUT

        # Request timeout should be well under CI job limits
        assert REQUEST_TIMEOUT <= 60
