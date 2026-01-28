"""Sefaria API client for fetching Likutei Halachot texts."""

import json
import logging
import random
import re
from typing import Any

import requests

from .config import get_data_dir
from .models import Halacha, HalachaSection

logger = logging.getLogger(__name__)

# Volumes to select from (must pick 2 different ones each day)
VOLUMES = ["Orach Chaim", "Yoreh Deah", "Even HaEzer", "Choshen Mishpat"]


class SefariaClient:
    """Client for the Sefaria API."""

    BASE_URL = "https://www.sefaria.org/api"
    WEB_URL = "https://www.sefaria.org"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "LikuteiHalachotYomiBot/2.0"})
        self._catalog: list[HalachaSection] | None = None

    @property
    def catalog(self) -> list[HalachaSection]:
        """Load and cache the section catalog."""
        if self._catalog is None:
            self._catalog = self._load_catalog()
        return self._catalog

    def _load_catalog(self) -> list[HalachaSection]:
        """Load the pre-built section catalog."""
        catalog_path = get_data_dir() / "sections.json"
        if not catalog_path.exists():
            raise FileNotFoundError(
                f"Section catalog not found at {catalog_path}. "
                "Run 'python -m scripts.build_catalog' to generate it."
            )

        with open(catalog_path, encoding="utf-8") as f:
            data = json.load(f)

        return [
            HalachaSection(
                volume=item["volume"],
                section=item["section"],
                section_he=item["section_he"],
                ref_base=item["ref_base"],
                has_english=item.get("has_english", False),
            )
            for item in data
        ]

    def get_sections_by_volume(self, volume: str) -> list[HalachaSection]:
        """Get all sections for a specific volume."""
        return [s for s in self.catalog if s.volume == volume]

    def get_text(self, reference: str) -> dict[str, Any] | None:
        """Fetch text from Sefaria API."""
        url = f"{self.BASE_URL}/texts/{reference}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {reference}: {e}")
            return None

    def get_section_structure(self, section: HalachaSection) -> dict[str, Any] | None:
        """Get the structure (available chapters/simanim) for a section."""
        url = f"{self.BASE_URL}/v2/index/{section.ref_base.replace(',', '%2C')}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            result: dict[str, Any] = response.json()
            return result
        except requests.RequestException as e:
            logger.error(f"Failed to get structure for {section.section}: {e}")
            return None

    def fetch_halacha(
        self, section: HalachaSection, chapter: int, siman: int
    ) -> Halacha | None:
        """Fetch a specific halacha from Sefaria."""
        reference = f"{section.ref_base}.{chapter}.{siman}"
        data = self.get_text(reference)

        if not data:
            return None

        # Extract Hebrew text
        hebrew = data.get("he", "")
        if isinstance(hebrew, list):
            hebrew = " ".join(str(p) for p in hebrew if p)

        # Clean HTML tags but preserve structure
        hebrew = self._clean_text(hebrew)

        if not hebrew or len(hebrew) < 10:
            logger.warning(f"No Hebrew text for {reference}")
            return None

        # Extract English text if available
        english = data.get("text", "")
        if isinstance(english, list):
            english = " ".join(str(p) for p in english if p)
        english = self._clean_text(english) if english else None

        if english and len(english) < 10:
            english = None

        # Build Sefaria URL
        sefaria_url = f"{self.WEB_URL}/{reference.replace(' ', '_')}"

        return Halacha(
            section=section,
            chapter=chapter,
            siman=siman,
            hebrew_text=hebrew,
            english_text=english,
            sefaria_url=sefaria_url,
        )

    def _clean_text(self, text: str) -> str:
        """Clean HTML and normalize text."""
        if not text:
            return ""
        # Remove HTML tags but keep text content
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def get_random_halacha_from_volume(
        self, volume: str, rng: random.Random
    ) -> Halacha | None:
        """
        Get a random halacha from a specific volume.

        Uses the provided RNG for deterministic selection.
        """
        sections = self.get_sections_by_volume(volume)
        if not sections:
            logger.error(f"No sections found for volume {volume}")
            return None

        # Try up to 10 times to find a valid halacha
        for attempt in range(10):
            section = rng.choice(sections)

            # Try to get a random chapter and siman
            # Most sections have chapters 1-5 and simanim 1-10
            chapter = rng.randint(1, 5)
            siman = rng.randint(1, 5)

            halacha = self.fetch_halacha(section, chapter, siman)
            if halacha:
                logger.info(
                    f"Found halacha: {halacha.reference} (attempt {attempt + 1})"
                )
                return halacha

            # If chapter.siman didn't work, try chapter.1
            halacha = self.fetch_halacha(section, chapter, 1)
            if halacha:
                logger.info(
                    f"Found halacha: {halacha.reference} (attempt {attempt + 1})"
                )
                return halacha

            # Try chapter 1 as fallback
            halacha = self.fetch_halacha(section, 1, 1)
            if halacha:
                logger.info(
                    f"Found halacha: {halacha.reference} (attempt {attempt + 1})"
                )
                return halacha

        logger.error(f"Failed to find valid halacha in {volume} after 10 attempts")
        return None
