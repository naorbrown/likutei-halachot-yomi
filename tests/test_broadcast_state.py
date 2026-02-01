"""Tests for broadcast state management."""

import json
from datetime import date, timedelta

import pytest

from src.broadcast_state import (
    get_last_broadcast_date,
    has_broadcast_today,
    mark_broadcast_complete,
    set_last_broadcast_date,
)


@pytest.fixture(autouse=True)
def clean_broadcast_state(tmp_path, monkeypatch):
    """Use a temporary broadcast state file for each test."""
    test_file = tmp_path / "broadcast_state.json"
    monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)
    monkeypatch.setattr("src.broadcast_state.STATE_DIR", tmp_path)
    yield
    if test_file.exists():
        test_file.unlink()


class TestGetLastBroadcastDate:
    def test_returns_none_when_no_file(self, tmp_path, monkeypatch):
        """Should return None when state file doesn't exist."""
        result = get_last_broadcast_date()
        assert result is None

    def test_returns_date_from_file(self, tmp_path, monkeypatch):
        """Should load last broadcast date from JSON file."""
        test_file = tmp_path / "broadcast_state.json"
        test_file.write_text(json.dumps({"last_broadcast_date": "2026-02-01"}))
        monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)

        result = get_last_broadcast_date()
        assert result == date(2026, 2, 1)

    def test_handles_invalid_json(self, tmp_path, monkeypatch):
        """Should return None on invalid JSON."""
        test_file = tmp_path / "broadcast_state.json"
        test_file.write_text("not valid json")
        monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)

        result = get_last_broadcast_date()
        assert result is None

    def test_handles_invalid_date_format(self, tmp_path, monkeypatch):
        """Should return None on invalid date format."""
        test_file = tmp_path / "broadcast_state.json"
        test_file.write_text(json.dumps({"last_broadcast_date": "not-a-date"}))
        monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)

        result = get_last_broadcast_date()
        assert result is None


class TestSetLastBroadcastDate:
    def test_saves_date_to_file(self, tmp_path, monkeypatch):
        """Should save broadcast date to JSON file."""
        test_file = tmp_path / "broadcast_state.json"
        monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)
        monkeypatch.setattr("src.broadcast_state.STATE_DIR", tmp_path)

        set_last_broadcast_date(date(2026, 2, 1))

        data = json.loads(test_file.read_text())
        assert data["last_broadcast_date"] == "2026-02-01"

    def test_creates_directory_if_needed(self, tmp_path, monkeypatch):
        """Should create state directory if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "dir"
        test_file = nested_dir / "broadcast_state.json"
        monkeypatch.setattr("src.broadcast_state.BROADCAST_STATE_FILE", test_file)
        monkeypatch.setattr("src.broadcast_state.STATE_DIR", nested_dir)

        set_last_broadcast_date(date(2026, 2, 1))

        assert test_file.exists()


class TestHasBroadcastToday:
    def test_returns_false_when_no_prior_broadcast(self, tmp_path, monkeypatch):
        """Should return False when no broadcast has ever been done."""
        result = has_broadcast_today()
        assert result is False

    def test_returns_true_when_already_broadcast_today(self, tmp_path, monkeypatch):
        """Should return True when already broadcast today."""
        today = date.today()
        set_last_broadcast_date(today)

        result = has_broadcast_today()
        assert result is True

    def test_returns_false_when_last_broadcast_was_yesterday(
        self, tmp_path, monkeypatch
    ):
        """Should return False when last broadcast was yesterday."""
        yesterday = date.today() - timedelta(days=1)
        set_last_broadcast_date(yesterday)

        result = has_broadcast_today()
        assert result is False

    def test_returns_true_when_last_broadcast_is_future(self, tmp_path, monkeypatch):
        """Should return True if last broadcast date is in the future (edge case)."""
        tomorrow = date.today() + timedelta(days=1)
        set_last_broadcast_date(tomorrow)

        result = has_broadcast_today()
        assert result is True

    def test_with_specific_target_date(self, tmp_path, monkeypatch):
        """Should check against provided target date instead of today."""
        target = date(2026, 2, 15)
        set_last_broadcast_date(date(2026, 2, 14))  # Day before target

        result = has_broadcast_today(target)
        assert result is False

        set_last_broadcast_date(date(2026, 2, 15))  # Same as target

        result = has_broadcast_today(target)
        assert result is True


class TestMarkBroadcastComplete:
    def test_marks_today_as_complete(self, tmp_path, monkeypatch):
        """Should mark today as broadcast complete."""
        mark_broadcast_complete()

        assert has_broadcast_today() is True
        assert get_last_broadcast_date() == date.today()

    def test_marks_specific_date_as_complete(self, tmp_path, monkeypatch):
        """Should mark specific date as broadcast complete."""
        target = date(2026, 3, 15)
        mark_broadcast_complete(target)

        assert get_last_broadcast_date() == target


class TestDuplicateBroadcastPrevention:
    """Integration-style tests for the duplicate prevention scenario."""

    def test_dual_cron_scenario(self, tmp_path, monkeypatch):
        """Simulate the dual DST cron scenario where both 3am and 4am UTC fire."""
        today = date.today()

        # First cron job at 3am UTC - should broadcast
        assert has_broadcast_today(today) is False
        # ... broadcast would happen here ...
        mark_broadcast_complete(today)

        # Second cron job at 4am UTC - should NOT broadcast
        assert has_broadcast_today(today) is True

    def test_manual_rerun_after_scheduled(self, tmp_path, monkeypatch):
        """Manual workflow_dispatch should not duplicate after scheduled run."""
        today = date.today()

        # Scheduled run
        assert has_broadcast_today(today) is False
        mark_broadcast_complete(today)

        # Manual rerun later
        assert has_broadcast_today(today) is True

    def test_next_day_after_broadcast(self, tmp_path, monkeypatch):
        """Next day should allow broadcast again."""
        yesterday = date.today() - timedelta(days=1)
        today = date.today()

        # Yesterday's broadcast
        mark_broadcast_complete(yesterday)

        # Today should be allowed
        assert has_broadcast_today(today) is False
