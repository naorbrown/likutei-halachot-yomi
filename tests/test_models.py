"""Tests for data models."""

import pytest

from src.models import DailyPair, Halacha


class TestHalachaSection:
    """Tests for HalachaSection model."""

    def test_volume_he_orach_chaim(self, sample_section_oc):
        assert sample_section_oc.volume_he == "אורח חיים"

    def test_volume_he_yoreh_deah(self, sample_section_yd):
        assert sample_section_yd.volume_he == "יורה דעה"

    def test_section_is_frozen(self, sample_section_oc):
        with pytest.raises(AttributeError):
            sample_section_oc.volume = "Something Else"


class TestHalacha:
    """Tests for Halacha model."""

    def test_reference(self, sample_halacha_oc):
        expected = "Likutei_Halakhot,_Orach_Chaim,_Laws_of_Morning_Conduct.1.1"
        assert sample_halacha_oc.reference == expected

    def test_hebrew_reference(self, sample_halacha_oc):
        ref = sample_halacha_oc.hebrew_reference
        assert "ליקוטי הלכות" in ref
        assert "אורח חיים" in ref
        assert "1:1" in ref

    def test_halacha_is_frozen(self, sample_halacha_oc):
        with pytest.raises(AttributeError):
            sample_halacha_oc.chapter = 2


class TestDailyPair:
    """Tests for DailyPair model."""

    def test_valid_pair(self, sample_halacha_oc, sample_halacha_yd):
        pair = DailyPair(
            first=sample_halacha_oc,
            second=sample_halacha_yd,
            date_seed="2024-01-27",
        )
        assert pair.first.section.volume == "Orach Chaim"
        assert pair.second.section.volume == "Yoreh Deah"

    def test_same_volume_raises_error(self, sample_halacha_oc, sample_section_oc):
        another_oc = Halacha(
            section=sample_section_oc,
            chapter=2,
            siman=1,
            hebrew_text="Some text",
            english_text=None,
            sefaria_url="https://example.com",
        )

        with pytest.raises(ValueError, match="different volumes"):
            DailyPair(
                first=sample_halacha_oc,
                second=another_oc,
                date_seed="2024-01-27",
            )
