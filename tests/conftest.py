"""Pytest configuration and fixtures."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models import DailyPair, Halacha, HalachaSection


@pytest.fixture
def sample_section_oc():
    """Sample Orach Chaim section."""
    return HalachaSection(
        volume="Orach Chaim",
        section="Laws of Morning Conduct",
        section_he="הלכות השכמת הבוקר",
        ref_base="Likutei_Halakhot,_Orach_Chaim,_Laws_of_Morning_Conduct",
        has_english=True,
    )


@pytest.fixture
def sample_section_yd():
    """Sample Yoreh Deah section."""
    return HalachaSection(
        volume="Yoreh Deah",
        section="Laws of Slaughtering",
        section_he="הלכות שחיטה",
        ref_base="Likutei_Halakhot,_Yoreh_Deah,_Laws_of_Slaughtering",
        has_english=False,
    )


@pytest.fixture
def sample_halacha_oc(sample_section_oc):
    """Sample halacha from Orach Chaim."""
    return Halacha(
        section=sample_section_oc,
        chapter=1,
        siman=1,
        hebrew_text="יִתְגַּבֵּר כַּאֲרִי לַעֲמֹד בַּבֹּקֶר לַעֲבוֹדַת בּוֹרְאוֹ",
        english_text="One should strengthen oneself like a lion to rise in the morning",
        sefaria_url="https://www.sefaria.org/Likutei_Halakhot,_Orach_Chaim,_Laws_of_Morning_Conduct.1.1",
    )


@pytest.fixture
def sample_halacha_yd(sample_section_yd):
    """Sample halacha from Yoreh Deah."""
    return Halacha(
        section=sample_section_yd,
        chapter=1,
        siman=1,
        hebrew_text="הנה ידוע שעיקר השחיטה היא להמשיך חיות לכל העולמות",
        english_text=None,
        sefaria_url="https://www.sefaria.org/Likutei_Halakhot,_Yoreh_Deah,_Laws_of_Slaughtering.1.1",
    )


@pytest.fixture
def sample_daily_pair(sample_halacha_oc, sample_halacha_yd):
    """Sample daily pair."""
    return DailyPair(
        first=sample_halacha_oc,
        second=sample_halacha_yd,
        date_seed="2024-01-27",
    )


@pytest.fixture
def fixed_date():
    """Fixed date for deterministic testing."""
    return date(2024, 1, 27)


@pytest.fixture
def sample_audio_bytes():
    """Minimal audio bytes stub for TTS tests."""
    return b"OggS\x00\x02\x00\x00fake-ogg-opus-audio-data"


@pytest.fixture
def isolated_subscribers(tmp_path, monkeypatch):
    """Redirect subscriber storage to a temp directory for e2e tests.

    Non-autouse: only tests that explicitly request this fixture get isolation.
    Returns the tmp_path so tests can inspect files if needed.
    """
    test_file = tmp_path / "subscribers.json"
    monkeypatch.setattr("src.subscribers.SUBSCRIBERS_FILE", test_file)
    monkeypatch.setattr("src.subscribers.STATE_DIR", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Shared E2E fixtures — reduce boilerplate across broadcast / poll tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_telegram_bot():
    """Pre-configured AsyncMock Telegram Bot that works as an async context manager.

    Provides: send_message (returns message with id=1), send_voice, __aenter__/__aexit__.
    """
    bot = AsyncMock()
    result = MagicMock()
    result.message_id = 1
    bot.send_message.return_value = result
    bot.__aenter__ = AsyncMock(return_value=bot)
    bot.__aexit__ = AsyncMock(return_value=False)
    return bot


@pytest.fixture
def mock_selector(sample_daily_pair):
    """MagicMock HalachaSelector that returns sample_daily_pair.

    get_cached_messages returns None (forces fresh fetch path).
    get_daily_pair returns sample_daily_pair.
    """
    sel = MagicMock()
    sel.get_cached_messages.return_value = None
    sel.get_daily_pair.return_value = sample_daily_pair
    return sel


@pytest.fixture
def broadcast_bot_instance(sample_daily_pair, mock_selector):
    """LikuteiHalachotBot instance with a mocked selector for broadcast tests."""
    from src.bot import LikuteiHalachotBot
    from src.config import Config

    config = Config(
        telegram_bot_token="fake-token",
        telegram_chat_id="-100999",
    )
    bot_instance = LikuteiHalachotBot(config)
    bot_instance.selector = mock_selector
    return bot_instance


@pytest.fixture
def broadcast_env(mock_telegram_bot):
    """Context-manager helper that patches Bot, subscribers, TTS, and unified channel.

    Usage::

        with broadcast_env(subscribers={111, 222}, tts=False, unified=False):
            result = await bot_instance.send_daily_broadcast()

    Returns a callable(subscribers, tts, unified) that yields a context manager.
    """
    import contextlib
    from unittest.mock import patch

    @contextlib.contextmanager
    def _env(subscribers=None, tts=True, unified=False):
        subscribers = subscribers or set()
        patches = [
            patch("src.bot.Bot", return_value=mock_telegram_bot),
            patch("src.bot.load_subscribers", return_value=subscribers),
            patch("src.bot.HebrewTTSClient"),
            patch("src.bot.is_unified_channel_enabled", return_value=unified),
        ]
        if unified:
            patches.append(patch("src.bot.publish_text_to_unified_channel"))
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            yield mock_telegram_bot

    return _env


@pytest.fixture
def isolated_poll_state(tmp_path, monkeypatch):
    """Redirect poll state files to a temp directory.

    Returns the tmp_path so tests can inspect files.
    """
    state_file = tmp_path / "last_update_id.json"
    monkeypatch.setattr("scripts.poll_commands.STATE_FILE", state_file)
    monkeypatch.setattr("scripts.poll_commands.STATE_DIR", tmp_path)
    return tmp_path
