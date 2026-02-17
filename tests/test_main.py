"""Tests for main.py broadcast timing logic."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from main import (
    ISRAEL_TZ,
    already_sent_today,
    is_broadcast_hour,
    mark_sent_today,
)


class TestIsBroadcastHour:
    """Tests for DST-aware broadcast timing with GHA delay tolerance."""

    def test_returns_true_at_3am_israel_winter(self):
        """3am Israel time in winter (IST, UTC+2) should return True."""
        winter_3am_israel = datetime(2026, 1, 15, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_3am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_true_at_3am_israel_summer(self):
        """3am Israel time in summer (IDT, UTC+3) should return True."""
        summer_3am_israel = datetime(2026, 7, 15, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = summer_3am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_true_at_4am_israel_delayed(self):
        """4am Israel time should return True (GHA cron delay tolerance)."""
        winter_4am_israel = datetime(2026, 1, 15, 2, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_4am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_true_at_5am_israel_delayed(self):
        """5am Israel time should return True (extreme GHA cron delay)."""
        winter_5am_israel = datetime(2026, 1, 15, 3, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_5am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_returns_false_at_2am_israel(self):
        """2am Israel time should return False (too early)."""
        winter_2am_israel = datetime(2026, 1, 15, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_2am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_returns_false_at_6am_israel(self):
        """6am Israel time should return False (past the window)."""
        winter_6am_israel = datetime(2026, 1, 15, 4, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = winter_6am_israel.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is False

    def test_handles_dst_transition_spring(self):
        """Test behavior during spring DST transition (clocks forward)."""
        # On DST transition day (March 27, 2026 in Israel)
        # After transition: 0am UTC = 3am Israel (UTC+3)
        post_transition = datetime(2026, 3, 27, 0, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_handles_dst_transition_fall(self):
        """Test behavior during fall DST transition (clocks back)."""
        # On DST transition day (October 25, 2026 in Israel)
        # After transition: 1am UTC = 3am Israel (UTC+2)
        post_transition = datetime(2026, 10, 25, 1, 30, 0, tzinfo=ZoneInfo("UTC"))
        with patch("main.datetime") as mock_datetime:
            mock_datetime.now.return_value = post_transition.astimezone(ISRAEL_TZ)
            assert is_broadcast_hour() is True

    def test_integration_with_actual_time(self):
        """Verify the function works with actual datetime.now()."""
        result = is_broadcast_hour()
        assert isinstance(result, bool)


class TestAlreadySentToday:
    """Tests for the double-send prevention guard."""

    def test_returns_false_when_no_marker(self, tmp_path, monkeypatch):
        """Should return False when marker file doesn't exist."""
        monkeypatch.setattr("main.BROADCAST_MARKER", tmp_path / "marker.txt")
        assert already_sent_today() is False

    def test_returns_true_when_sent_today(self, tmp_path, monkeypatch):
        """Should return True when marker matches today's date."""
        marker = tmp_path / "marker.txt"
        monkeypatch.setattr("main.BROADCAST_MARKER", marker)
        today = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d")
        marker.write_text(today)
        assert already_sent_today() is True

    def test_returns_false_when_sent_yesterday(self, tmp_path, monkeypatch):
        """Should return False when marker has yesterday's date."""
        marker = tmp_path / "marker.txt"
        monkeypatch.setattr("main.BROADCAST_MARKER", marker)
        marker.write_text("2020-01-01")
        assert already_sent_today() is False

    def test_mark_sent_today_creates_file(self, tmp_path, monkeypatch):
        """mark_sent_today() should create the marker with today's date."""
        marker = tmp_path / "state" / "marker.txt"
        monkeypatch.setattr("main.BROADCAST_MARKER", marker)
        mark_sent_today()
        today = datetime.now(ISRAEL_TZ).strftime("%Y-%m-%d")
        assert marker.read_text() == today

    def test_mark_then_check(self, tmp_path, monkeypatch):
        """mark_sent_today() followed by already_sent_today() returns True."""
        marker = tmp_path / "marker.txt"
        monkeypatch.setattr("main.BROADCAST_MARKER", marker)
        mark_sent_today()
        assert already_sent_today() is True
