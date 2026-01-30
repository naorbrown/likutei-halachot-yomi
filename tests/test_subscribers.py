"""Tests for subscriber management."""

import json

import pytest

from src.subscribers import (
    add_subscriber,
    get_subscriber_count,
    is_subscribed,
    load_subscribers,
    remove_subscriber,
    save_subscribers,
)


@pytest.fixture(autouse=True)
def clean_subscribers(tmp_path, monkeypatch):
    """Use a temporary subscribers file for each test."""
    test_file = tmp_path / "subscribers.json"
    monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)
    monkeypatch.setattr("src.subscribers.STATE_DIR", tmp_path)
    yield
    if test_file.exists():
        test_file.unlink()


class TestLoadSubscribers:
    def test_returns_empty_set_when_no_file(self, tmp_path, monkeypatch):
        """Should return empty set when file doesn't exist."""
        result = load_subscribers()
        assert result == set()

    def test_loads_subscribers_from_file(self, tmp_path, monkeypatch):
        """Should load subscribers from JSON file."""
        test_file = tmp_path / "subscribers.json"
        test_file.write_text(json.dumps({"subscribers": [123, 456, 789]}))
        monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)

        result = load_subscribers()
        assert result == {123, 456, 789}

    def test_handles_invalid_json(self, tmp_path, monkeypatch):
        """Should return empty set on invalid JSON."""
        test_file = tmp_path / "subscribers.json"
        test_file.write_text("not valid json")
        monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)

        result = load_subscribers()
        assert result == set()


class TestSaveSubscribers:
    def test_saves_subscribers_to_file(self, tmp_path, monkeypatch):
        """Should save subscribers to JSON file."""
        test_file = tmp_path / "subscribers.json"
        monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)
        monkeypatch.setattr("src.subscribers.STATE_DIR", tmp_path)

        save_subscribers({123, 456})

        data = json.loads(test_file.read_text())
        assert set(data["subscribers"]) == {123, 456}

    def test_creates_directory_if_needed(self, tmp_path, monkeypatch):
        """Should create state directory if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "dir"
        test_file = nested_dir / "subscribers.json"
        monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)
        monkeypatch.setattr("src.subscribers.STATE_DIR", nested_dir)

        save_subscribers({123})

        assert test_file.exists()


class TestAddSubscriber:
    def test_adds_new_subscriber(self, tmp_path, monkeypatch):
        """Should add new subscriber and return True."""
        result = add_subscriber(123)
        assert result is True
        assert is_subscribed(123)

    def test_returns_false_for_existing_subscriber(self, tmp_path, monkeypatch):
        """Should return False if already subscribed."""
        add_subscriber(123)
        result = add_subscriber(123)
        assert result is False


class TestRemoveSubscriber:
    def test_removes_existing_subscriber(self, tmp_path, monkeypatch):
        """Should remove subscriber and return True."""
        add_subscriber(123)
        result = remove_subscriber(123)
        assert result is True
        assert not is_subscribed(123)

    def test_returns_false_for_nonexistent_subscriber(self, tmp_path, monkeypatch):
        """Should return False if not subscribed."""
        result = remove_subscriber(999)
        assert result is False


class TestIsSubscribed:
    def test_returns_true_for_subscriber(self, tmp_path, monkeypatch):
        """Should return True for subscribed user."""
        add_subscriber(123)
        assert is_subscribed(123) is True

    def test_returns_false_for_non_subscriber(self, tmp_path, monkeypatch):
        """Should return False for non-subscribed user."""
        assert is_subscribed(999) is False


class TestGetSubscriberCount:
    def test_returns_zero_when_empty(self, tmp_path, monkeypatch):
        """Should return 0 when no subscribers."""
        assert get_subscriber_count() == 0

    def test_returns_correct_count(self, tmp_path, monkeypatch):
        """Should return correct subscriber count."""
        add_subscriber(123)
        add_subscriber(456)
        add_subscriber(789)
        assert get_subscriber_count() == 3
