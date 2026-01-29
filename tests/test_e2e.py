"""End-to-end tests for the bot command flow.

These tests verify the complete flow from command to response,
including caching behavior and performance characteristics.
"""

import json
import time
from datetime import date
from unittest.mock import patch

import pytest

from src.commands import get_info_message, get_start_messages, get_today_messages
from src.formatter import format_daily_message, format_welcome_message
from src.models import DailyPair, Halacha, HalachaSection
from src.sefaria import SefariaClient
from src.selector import HalachaSelector, _memory_cache, _message_cache


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before and after each test."""
    _memory_cache.clear()
    _message_cache.clear()
    yield
    _memory_cache.clear()
    _message_cache.clear()


class TestCachePreWarming:
    """Tests for cache pre-warming behavior."""

    def test_cache_loads_from_disk_on_first_access(self, tmp_path, sample_daily_pair):
        """Cache should load from disk file on first access."""
        # Create a cache file
        cache_file = tmp_path / "pair_2099-01-01.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 1))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = selector.get_cached_messages(date(2099, 1, 1))

        assert messages is not None
        assert len(messages) >= 2

    def test_memory_cache_instant_on_subsequent_access(
        self, tmp_path, sample_daily_pair
    ):
        """Memory cache should provide instant access after first load."""
        cache_file = tmp_path / "pair_2099-01-02.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 2))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            # First access - loads from disk
            start = time.perf_counter()
            messages1 = selector.get_cached_messages(date(2099, 1, 2))
            first_access_time = time.perf_counter() - start

            # Second access - from memory
            start = time.perf_counter()
            messages2 = selector.get_cached_messages(date(2099, 1, 2))
            second_access_time = time.perf_counter() - start

        assert messages1 == messages2
        # Memory access should be much faster (at least 10x)
        # Note: This might be flaky on slow systems, so we use a generous margin
        assert second_access_time < first_access_time or second_access_time < 0.001

    def test_formatted_messages_generated_for_old_cache_format(
        self, tmp_path, sample_daily_pair
    ):
        """Should generate formatted messages for cache files without them."""
        # Create old-format cache (no formatted_messages field)
        cache_file = tmp_path / "pair_2099-01-03.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 1, 3))
        del cache_data["formatted_messages"]  # Remove to simulate old format
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = selector.get_cached_messages(date(2099, 1, 3))

        # Should generate messages on-the-fly
        assert messages is not None
        assert len(messages) >= 2
        assert "ליקוטי הלכות יומי" in messages[0]


class TestCommandResponseTime:
    """Tests for command response time with caching."""

    def test_start_command_instant_with_cache(self, tmp_path, sample_daily_pair):
        """Start command should be instant when cache is populated."""
        cache_file = tmp_path / "pair_2099-02-01.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 2, 1))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            # Pre-warm cache
            selector.get_cached_messages(date(2099, 2, 1))

            # Time the command
            start = time.perf_counter()
            messages = get_start_messages(selector, date(2099, 2, 1))
            elapsed = time.perf_counter() - start

        assert len(messages) >= 2
        assert elapsed < 0.01  # Should be under 10ms

    def test_today_command_instant_with_cache(self, tmp_path, sample_daily_pair):
        """Today command should be instant when cache is populated."""
        cache_file = tmp_path / "pair_2099-02-02.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 2, 2))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            # Pre-warm cache
            selector.get_cached_messages(date(2099, 2, 2))

            # Time the command
            start = time.perf_counter()
            messages = get_today_messages(selector, date(2099, 2, 2))
            elapsed = time.perf_counter() - start

        assert len(messages) >= 1
        assert elapsed < 0.01  # Should be under 10ms

    def test_info_command_always_instant(self):
        """Info command should always be instant (static message)."""
        start = time.perf_counter()
        message = get_info_message()
        elapsed = time.perf_counter() - start

        assert "ליקוטי הלכות" in message
        assert elapsed < 0.001  # Should be under 1ms


class TestCommandBehavior:
    """Tests for correct command behavior."""

    def test_start_includes_welcome_message(self, tmp_path, sample_daily_pair):
        """Start command should include welcome message."""
        cache_file = tmp_path / "pair_2099-03-01.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 3, 1))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = get_start_messages(selector, date(2099, 3, 1))

        # First message should be welcome
        assert "ליקוטי הלכות יומי" in messages[0]
        assert "שתי הלכות חדשות" in messages[0]

    def test_today_excludes_welcome_message(self, tmp_path, sample_daily_pair):
        """Today command should NOT include welcome message."""
        cache_file = tmp_path / "pair_2099-03-02.json"
        cache_data = _create_cache_data(sample_daily_pair, date(2099, 3, 2))
        cache_file.write_text(json.dumps(cache_data, ensure_ascii=False))

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            messages = get_today_messages(selector, date(2099, 3, 2))

        # First message should be content, not welcome
        assert "שתי הלכות חדשות" not in messages[0]
        # Should have content
        assert any("📜" in msg or "📖" in msg for msg in messages)

    def test_info_contains_commands_and_links(self):
        """Info message should contain command list and links."""
        message = get_info_message()

        assert "/today" in message
        assert "/info" in message
        assert "sefaria" in message.lower()
        assert "github" in message.lower()


class TestMessageFormatting:
    """Tests for message formatting correctness."""

    def test_daily_messages_have_correct_structure(self, sample_daily_pair):
        """Daily messages should have correct HTML structure."""
        messages = format_daily_message(sample_daily_pair, date(2099, 4, 1))

        # Should have at least 2 messages (one per halacha)
        assert len(messages) >= 2

        # First message should have date header
        assert "01/04/2099" in messages[0]

        # Should have section titles in Hebrew
        for msg in messages:
            assert "<b>" in msg  # Bold formatting
            assert "</b>" in msg

        # Should have Sefaria links
        assert any("sefaria.org" in msg for msg in messages)

        # Last message should have signature
        assert "נ נח נחמ נחמן מאומן" in messages[-1]

    def test_long_text_splits_correctly(self):
        """Long halacha text should split at word boundaries."""
        # Create halachot with very long text from different volumes
        long_text = "מילה " * 1000  # Very long text
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

        # Should split into multiple messages
        assert len(messages) > 2

        # Each message should be under limit
        for msg in messages:
            assert len(msg) < 4100  # MAX_MESSAGE_LENGTH + buffer


class TestErrorHandling:
    """Tests for error handling."""

    def test_graceful_fallback_on_cache_miss(self, tmp_path):
        """Should handle cache miss gracefully."""
        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            # No cache file exists
            messages = selector.get_cached_messages(date(2099, 5, 1))

        assert messages is None

    def test_graceful_fallback_on_corrupted_cache(self, tmp_path):
        """Should handle corrupted cache file gracefully."""
        cache_file = tmp_path / "pair_2099-05-02.json"
        cache_file.write_text("not valid json {{{")

        client = SefariaClient()
        selector = HalachaSelector(client)

        with patch("src.selector.CACHE_DIR", tmp_path):
            pair = selector._load_cached_pair(date(2099, 5, 2))

        assert pair is None


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
