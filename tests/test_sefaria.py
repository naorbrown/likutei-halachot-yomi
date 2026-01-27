"""Tests for Sefaria client."""

import json
from unittest.mock import patch

import pytest
import responses

from src.models import HalachaSection
from src.sefaria import VOLUMES, SefariaClient


class TestSefariaClient:
    """Tests for SefariaClient."""

    @pytest.fixture
    def mock_catalog_data(self):
        """Mock catalog data for testing."""
        return [
            {
                "volume": "Orach Chaim",
                "section": "Laws of Morning Conduct",
                "section_he": "הלכות השכמת הבוקר",
                "ref_base": "Likutei_Halakhot,_Orach_Chaim,_Laws_of_Morning_Conduct",
                "has_english": True,
            },
            {
                "volume": "Yoreh Deah",
                "section": "Laws of Slaughtering",
                "section_he": "הלכות שחיטה",
                "ref_base": "Likutei_Halakhot,_Yoreh_Deah,_Laws_of_Slaughtering",
                "has_english": False,
            },
        ]

    @pytest.fixture
    def client(self, tmp_path, mock_catalog_data):
        """Create a client with mock catalog."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        catalog_path = data_dir / "sections.json"
        catalog_path.write_text(json.dumps(mock_catalog_data))

        with patch("src.sefaria.get_data_dir", return_value=data_dir):
            client = SefariaClient()
            # Force load the catalog while patch is active
            _ = client.catalog
            return client

    def test_load_catalog(self, client, mock_catalog_data):
        """Client should load catalog correctly."""
        catalog = client.catalog
        assert len(catalog) == len(mock_catalog_data)
        assert all(isinstance(s, HalachaSection) for s in catalog)

    def test_get_sections_by_volume(self, client):
        """Should filter sections by volume."""
        oc_sections = client.get_sections_by_volume("Orach Chaim")
        assert len(oc_sections) == 1
        assert oc_sections[0].volume == "Orach Chaim"

    def test_clean_text(self, client):
        """Should clean HTML tags from text."""
        html = "<b>Bold text</b> and <i>italic</i>"
        result = client._clean_text(html)
        assert result == "Bold text and italic"

    @responses.activate
    def test_get_text_success(self, client):
        """Should fetch text from API."""
        responses.add(
            responses.GET,
            "https://www.sefaria.org/api/texts/Test.1.1",
            json={"he": "Hebrew text", "text": "English text"},
            status=200,
        )

        result = client.get_text("Test.1.1")
        assert result is not None
        assert result["he"] == "Hebrew text"

    @responses.activate
    def test_get_text_failure(self, client):
        """Should return None on API error."""
        responses.add(
            responses.GET,
            "https://www.sefaria.org/api/texts/Test.1.1",
            json={"error": "Not found"},
            status=404,
        )

        result = client.get_text("Test.1.1")
        assert result is None


class TestVolumes:
    """Tests for volume configuration."""

    def test_four_volumes_defined(self):
        """Should have exactly 4 volumes."""
        assert len(VOLUMES) == 4

    def test_volume_names(self):
        """Should have correct volume names."""
        assert "Orach Chaim" in VOLUMES
        assert "Yoreh Deah" in VOLUMES
        assert "Even HaEzer" in VOLUMES
        assert "Choshen Mishpat" in VOLUMES
