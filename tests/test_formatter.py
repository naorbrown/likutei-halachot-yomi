"""Tests for message formatting."""

from src.formatter import (
    MAX_MESSAGE_LENGTH,
    format_about_message,
    format_daily_message,
    format_error_message,
    format_halacha,
    format_welcome_message,
    truncate_text,
)


class TestTruncateText:
    """Tests for text truncation."""

    def test_short_text_unchanged(self):
        text = "Short text"
        assert truncate_text(text, 100) == text

    def test_long_text_truncated(self):
        text = "This is a very long text that needs to be truncated"
        result = truncate_text(text, 20)
        assert len(result) <= 20
        assert result.endswith("...")

    def test_truncate_at_word_boundary(self):
        text = "Word1 Word2 Word3 Word4 Word5"
        result = truncate_text(text, 15)
        assert result == "Word1 Word2..."


class TestFormatHalacha:
    """Tests for single halacha formatting."""

    def test_format_with_english(self, sample_halacha_oc):
        result = format_halacha(sample_halacha_oc, 1)
        assert "א." in result
        assert sample_halacha_oc.section.section_he in result
        assert sample_halacha_oc.hebrew_text in result
        assert sample_halacha_oc.english_text in result
        assert "ספריא" in result

    def test_format_without_english(self, sample_halacha_yd):
        result = format_halacha(sample_halacha_yd, 2)
        assert "ב." in result
        assert sample_halacha_yd.section.section_he in result
        assert sample_halacha_yd.hebrew_text in result


class TestFormatDailyMessage:
    """Tests for full daily message formatting."""

    def test_format_daily_message(self, sample_daily_pair, fixed_date):
        result = format_daily_message(sample_daily_pair, fixed_date)

        # Check key elements
        assert "ליקוטי הלכות יומי" in result
        assert "27/01/2024" in result
        assert sample_daily_pair.first.section.section_he in result
        assert sample_daily_pair.second.section.section_he in result
        assert "נ נח נחמ נחמן מאומן" in result

    def test_message_under_length_limit(self, sample_daily_pair, fixed_date):
        result = format_daily_message(sample_daily_pair, fixed_date)
        assert len(result) <= MAX_MESSAGE_LENGTH


class TestStaticMessages:
    """Tests for static messages."""

    def test_welcome_message(self):
        result = format_welcome_message()
        assert "ברוכים הבאים" in result
        assert "Welcome" in result
        assert "/today" in result

    def test_about_message(self):
        result = format_about_message()
        assert "Rebbe Natan" in result
        assert "Sefaria" in result
        assert "GitHub" in result

    def test_error_message(self):
        result = format_error_message()
        assert "שגיאה" in result
