"""End-to-end tests for the bot command flow.

These tests verify the complete flow from cache to command response,
ensuring the full pipeline works together.
"""

import json
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
