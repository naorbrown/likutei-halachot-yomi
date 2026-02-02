"""Tests for main.py broadcast timing logic."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from main import ISRAEL_TZ, is_broadcast_hour


class TestIsBroadcastHour:
    """Tests for DST-aware broadcast timing."""

    def test_returns_true_at_6am_israel_winter(self):
        """6am Israel time in winter (IST, UTC+2) should return True."""
        # Winter: 4am UTC = 6am Israel (UTC+2)
        winter_6am_israel = datetime(2026, 1, 15, 4, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_6am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_true_at_6am_israel_summer(self):
        """6am Israel time in summer (IDT, UTC+3) should return True."""
        # Summer: 3am UTC = 6am Israel (UTC+3)
        summer_6am_israel = datetime(2026, 7, 15, 3, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = summer_6am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_false_at_5am_israel_winter(self):
        """5am Israel time in winter should return False."""
        # Winter: 3am UTC = 5am Israel (UTC+2) - this is the early trigger
        winter_5am_israel = datetime(2026, 1, 15, 3, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_5am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_returns_false_at_7am_israel_summer(self):
        """7am Israel time in summer should return False."""
        # Summer: 4am UTC = 7am Israel (UTC+3) - this is the late trigger
        summer_7am_israel = datetime(2026, 7, 15, 4, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = summer_7am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_handles_dst_transition_spring(self):
        """Test behavior during spring DST transition (clocks forward)."""
        # On DST transition day (March 27, 2026 in Israel)
        # Before transition: 3am UTC = 5am Israel (UTC+2)
        # After transition: 3am UTC = 6am Israel (UTC+3)
        # The 3am UTC run should now send (it's 6am Israel)
        post_transition = datetime(2026, 3, 27, 3, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            # After DST change, 3am UTC is 6am Israel time
            assert is_broadcast_hour() is True

    def test_handles_dst_transition_fall(self):
        """Test behavior during fall DST transition (clocks back)."""
        # On DST transition day (October 25, 2026 in Israel)
        # Before transition: 3am UTC = 6am Israel (UTC+3)
        # After transition: 3am UTC = 5am Israel (UTC+2)
        # The 4am UTC run should send instead
        post_transition = datetime(2026, 10, 25, 4, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            # After DST change, 4am UTC is 6am Israel time
            assert is_broadcast_hour() is True

    def test_integration_with_actual_time(self):
        """Verify the function works with actual datetime.now()."""
        # Just verify it doesn't raise an exception
        result = is_broadcast_hour()
        assert isinstance(result, bool)
