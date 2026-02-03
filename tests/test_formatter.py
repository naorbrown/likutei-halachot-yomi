"""Tests for message formatting."""

from src.formatter import (
    MAX_MESSAGE_LENGTH,
    # Backwards compatibility
    format_about_message,
    format_daily_message,
    format_error_message,
    format_help_message,
    format_info_message,
    format_welcome_message,
    split_text,
)


class TestSplitText:
    """Tests for text splitting."""

    def test_short_text_unchanged(self):
        text = "Short text"
        assert split_text(text, 100) == [text]

    def test_long_text_split(self):
        text = "Word1 Word2 Word3 Word4 Word5"
        result = split_text(text, 15)
        assert len(result) >= 2
        assert all(len(chunk) <= 15 for chunk in result)


class TestFormatDailyMessage:
    """Tests for daily message formatting."""

    def test_format_daily_message(self, sample_daily_pair, fixed_date):
        result = format_daily_message(sample_daily_pair, fixed_date)
        assert isinstance(result, list)
        assert len(result) >= 1
        combined = "".join(result)
        assert "ליקוטי הלכות יומי" in combined
        assert "נ נח נחמ נחמן מאומן" in combined

    def test_no_duplicate_halachot_in_title(self, sample_daily_pair, fixed_date):
        """Ensure title doesn't duplicate 'הלכות' (section_he already contains it)."""
        result = format_daily_message(sample_daily_pair, fixed_date)
        combined = "".join(result)
        assert "הלכות הלכות" not in combined

    def test_message_parts_under_length_limit(self, sample_daily_pair, fixed_date):
        result = format_daily_message(sample_daily_pair, fixed_date)
        for msg in result:
            assert len(msg) <= MAX_MESSAGE_LENGTH + 100  # Buffer for closing


class TestStaticMessages:
    """Tests for static messages."""

    def test_welcome_message(self):
        result = format_welcome_message()
        assert "ליקוטי הלכות יומי" in result
        assert "שתי הלכות חדשות" in result

    def test_info_message(self):
        """Info message should contain about and help content."""
        result = format_info_message()
        assert "ליקוטי הלכות" in result
        assert "/today" in result
        assert "/info" in result

    def test_error_message(self):
        result = format_error_message()
        assert "נסה שוב" in result


class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""

    def test_about_message_alias(self):
        """format_about_message should return info message."""
        result = format_about_message()
        assert "ליקוטי הלכות" in result

    def test_help_message_alias(self):
        """format_help_message should return info message."""
        result = format_help_message()
        assert "/today" in result
