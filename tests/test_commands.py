"""Tests for the commands module."""

from unittest.mock import MagicMock

from src.commands import (
    get_about_message,
    get_daily_messages,
    get_error_message,
    get_help_message,
)


class TestGetDailyMessages:
    """Tests for get_daily_messages function."""

    def test_returns_welcome_and_content(self, sample_daily_pair):
        """Should return welcome message followed by daily content."""
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        messages = get_daily_messages(mock_selector)

        # Should have at least welcome + content messages
        assert len(messages) >= 2
        # First message should be welcome
        assert "ליקוטי הלכות יומי" in messages[0]

    def test_returns_error_when_no_pair(self):
        """Should return welcome + error when no pair available."""
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.return_value = None

        messages = get_daily_messages(mock_selector)

        # Should have welcome + error
        assert len(messages) == 2
        # Second message should be error
        assert "נסה שוב" in messages[1]

    def test_returns_error_on_exception(self):
        """Should return welcome + error when selector raises exception."""
        mock_selector = MagicMock()
        mock_selector.get_daily_pair.side_effect = Exception("API error")

        messages = get_daily_messages(mock_selector)

        # Should have welcome + error
        assert len(messages) == 2
        # Second message should be error
        assert "נסה שוב" in messages[1]


class TestStaticMessages:
    """Tests for static message functions."""

    def test_about_message_content(self):
        """About message should contain expected content."""
        msg = get_about_message()

        assert "ליקוטי הלכות" in msg
        assert "ספריא" in msg or "sefaria" in msg.lower()

    def test_help_message_content(self):
        """Help message should contain command references."""
        msg = get_help_message()

        assert "/today" in msg
        assert "/about" in msg

    def test_error_message_content(self):
        """Error message should contain retry instruction."""
        msg = get_error_message()

        assert "נסה שוב" in msg
