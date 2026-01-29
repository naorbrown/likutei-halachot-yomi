"""Tests for the commands module."""

from unittest.mock import MagicMock

from src.commands import (
    # Backwards compatibility
    get_about_message,
    get_daily_messages,
    get_error_message,
    get_help_message,
    get_info_message,
    get_start_messages,
    get_today_messages,
)


class TestGetStartMessages:
    """Tests for get_start_messages function (/start command)."""

    def test_returns_welcome_and_content(self, sample_daily_pair):
        """Should return welcome message followed by daily content."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        messages = get_start_messages(mock_selector)

        # Should have at least welcome + content messages
        assert len(messages) >= 2
        # First message should be welcome
        assert "ליקוטי הלכות יומי" in messages[0]

    def test_uses_cached_messages_when_available(self, sample_daily_pair):
        """Should use cached messages for instant response."""
        cached = ["welcome", "content1", "content2"]
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = cached

        messages = get_start_messages(mock_selector)

        assert messages == cached
        mock_selector.get_daily_pair.assert_not_called()

    def test_returns_error_when_no_pair(self):
        """Should return welcome + error when no pair available."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = None

        messages = get_start_messages(mock_selector)

        assert len(messages) == 2
        assert "נסה שוב" in messages[1]

    def test_returns_error_on_exception(self):
        """Should return welcome + error when selector raises exception."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.side_effect = Exception("API error")

        messages = get_start_messages(mock_selector)

        assert len(messages) == 2
        assert "נסה שוב" in messages[1]


class TestGetTodayMessages:
    """Tests for get_today_messages function (/today command)."""

    def test_returns_content_without_welcome(self, sample_daily_pair):
        """Should return just content (no welcome) for returning users."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        messages = get_today_messages(mock_selector)

        # Should have content but NOT welcome
        assert len(messages) >= 1
        # First message should be content, not welcome
        assert "הלכות" in messages[0] or "📜" in messages[0]

    def test_skips_welcome_from_cached_messages(self):
        """Should skip welcome message from cache."""
        cached = ["welcome msg", "content1", "content2"]
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = cached

        messages = get_today_messages(mock_selector)

        # Should skip first message (welcome)
        assert messages == ["content1", "content2"]

    def test_returns_error_when_no_pair(self):
        """Should return error when no pair available."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = None

        messages = get_today_messages(mock_selector)

        assert len(messages) == 1
        assert "נסה שוב" in messages[0]

    def test_returns_error_on_exception(self):
        """Should return error when selector raises exception."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.side_effect = Exception("API error")

        messages = get_today_messages(mock_selector)

        assert len(messages) == 1
        assert "נסה שוב" in messages[0]


class TestStaticMessages:
    """Tests for static message functions."""

    def test_info_message_content(self):
        """Info message should contain about and help content."""
        msg = get_info_message()

        assert "ליקוטי הלכות" in msg
        assert "/today" in msg
        assert "/info" in msg
        assert "ספריא" in msg.lower() or "sefaria" in msg.lower()

    def test_error_message_content(self):
        """Error message should contain retry instruction."""
        msg = get_error_message()

        assert "נסה שוב" in msg


class TestBackwardsCompatibility:
    """Tests for backwards compatibility aliases."""

    def test_get_daily_messages_alias(self, sample_daily_pair):
        """get_daily_messages should work as alias for get_start_messages."""
        mock_selector = MagicMock()
        mock_selector.get_cached_messages.return_value = None
        mock_selector.get_daily_pair.return_value = sample_daily_pair

        messages = get_daily_messages(mock_selector)

        assert len(messages) >= 2

    def test_get_about_message_alias(self):
        """get_about_message should return info message."""
        msg = get_about_message()
        assert "ליקוטי הלכות" in msg

    def test_get_help_message_alias(self):
        """get_help_message should return info message."""
        msg = get_help_message()
        assert "/today" in msg
