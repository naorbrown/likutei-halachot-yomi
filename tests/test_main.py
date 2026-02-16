"""Tests for main.py broadcast timing logic."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from main import ISRAEL_TZ, is_broadcast_hour


class TestIsBroadcastHour:
    """Tests for DST-aware broadcast timing."""

    def test_returns_true_at_3am_israel_winter(self):
        """3am Israel time in winter (IST, UTC+2) should return True."""
        # Winter: 1am UTC = 3am Israel (UTC+2)
        winter_3am_israel = datetime(2026, 1, 15, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_3am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_true_at_3am_israel_summer(self):
        """3am Israel time in summer (IDT, UTC+3) should return True."""
        # Summer: 0am UTC = 3am Israel (UTC+3)
        summer_3am_israel = datetime(2026, 7, 15, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = summer_3am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_false_at_2am_israel_winter(self):
        """2am Israel time in winter should return False."""
        # Winter: 0am UTC = 2am Israel (UTC+2) - this is the early trigger
        winter_2am_israel = datetime(2026, 1, 15, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_2am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_returns_false_at_4am_israel_summer(self):
        """4am Israel time in summer should return False."""
        # Summer: 1am UTC = 4am Israel (UTC+3) - this is the late trigger
        summer_4am_israel = datetime(2026, 7, 15, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = summer_4am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_handles_dst_transition_spring(self):
        """Test behavior during spring DST transition (clocks forward)."""
        # On DST transition day (March 27, 2026 in Israel)
        # After transition: 0am UTC = 3am Israel (UTC+3)
        # The 0am UTC run should send (it's 3am Israel)
        post_transition = datetime(2026, 3, 27, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            # After DST change, 0am UTC is 3am Israel time
            assert is_broadcast_hour() is True

    def test_handles_dst_transition_fall(self):
        """Test behavior during fall DST transition (clocks back)."""
        # On DST transition day (October 25, 2026 in Israel)
        # After transition: 1am UTC = 3am Israel (UTC+2)
        # The 1am UTC run should send
        post_transition = datetime(2026, 10, 25, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            # After DST change, 1am UTC is 3am Israel time
            assert is_broadcast_hour() is True

    def test_integration_with_actual_time(self):
        """Verify the function works with actual datetime.now()."""
        # Just verify it doesn't raise an exception
        result = is_broadcast_hour()
        assert isinstance(result, bool)
