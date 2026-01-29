"""Pytest configuration and fixtures."""

from datetime import date

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
