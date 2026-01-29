"""Daily halacha selection logic."""

import hashlib
import json
import logging
import random
from datetime import date
from pathlib import Path

from .config import get_data_dir
from .models import DailyPair, Halacha, HalachaSection
from .sefaria import VOLUMES, SefariaClient

logger = logging.getLogger(__name__)

# Cache file for daily pairs
CACHE_DIR = get_data_dir() / "cache"


class HalachaSelector:
    """Selects two random halachot from different volumes each day."""

    def __init__(self, client: SefariaClient):
        self.client = client

    def _get_daily_seed(self, for_date: date) -> str:
        """Generate a deterministic seed for a given date."""
        return for_date.isoformat()

    def _get_daily_rng(self, for_date: date) -> random.Random:
        """Get a seeded RNG for deterministic daily selection."""
        seed = self._get_daily_seed(for_date)
        # Use hash for better distribution
        seed_int = int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)
        return random.Random(seed_int)

    def _select_two_volumes(self, rng: random.Random) -> tuple[str, str]:
        """Select two different volumes for the day."""
        volumes = VOLUMES.copy()
        rng.shuffle(volumes)
        return volumes[0], volumes[1]

    def _get_cache_path(self, for_date: date) -> Path:
        """Get the cache file path for a date."""
        return CACHE_DIR / f"pair_{for_date.isoformat()}.json"

    def _load_cached_pair(self, for_date: date) -> DailyPair | None:
        """Load cached daily pair if available."""
        cache_path = self._get_cache_path(for_date)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct the DailyPair from cached data
            first_section = HalachaSection(**data["first"]["section"])
            first = Halacha(
                section=first_section,
                chapter=data["first"]["chapter"],
                siman=data["first"]["siman"],
                hebrew_text=data["first"]["hebrew_text"],
                english_text=data["first"].get("english_text"),
                sefaria_url=data["first"]["sefaria_url"],
            )

            second_section = HalachaSection(**data["second"]["section"])
            second = Halacha(
                section=second_section,
                chapter=data["second"]["chapter"],
                siman=data["second"]["siman"],
                hebrew_text=data["second"]["hebrew_text"],
                english_text=data["second"].get("english_text"),
                sefaria_url=data["second"]["sefaria_url"],
            )

            logger.info(f"Loaded cached pair for {for_date}")
            return DailyPair(first=first, second=second, date_seed=data["date_seed"])
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to load cache for {for_date}: {e}")
            return None

    def _save_cached_pair(self, pair: DailyPair, for_date: date) -> None:
        """Save daily pair to cache."""
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = self._get_cache_path(for_date)

        data = {
            "date_seed": pair.date_seed,
            "first": {
                "section": {
                    "volume": pair.first.section.volume,
                    "section": pair.first.section.section,
                    "section_he": pair.first.section.section_he,
                    "ref_base": pair.first.section.ref_base,
                    "has_english": pair.first.section.has_english,
                },
                "chapter": pair.first.chapter,
                "siman": pair.first.siman,
                "hebrew_text": pair.first.hebrew_text,
                "english_text": pair.first.english_text,
                "sefaria_url": pair.first.sefaria_url,
            },
            "second": {
                "section": {
                    "volume": pair.second.section.volume,
                    "section": pair.second.section.section,
                    "section_he": pair.second.section.section_he,
                    "ref_base": pair.second.section.ref_base,
                    "has_english": pair.second.section.has_english,
                },
                "chapter": pair.second.chapter,
                "siman": pair.second.siman,
                "hebrew_text": pair.second.hebrew_text,
                "english_text": pair.second.english_text,
                "sefaria_url": pair.second.sefaria_url,
            },
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached pair for {for_date}")

    def _get_fallback_halacha(self, volume: str, rng: random.Random) -> Halacha | None:
        """Create a fallback halacha with just section info when API fails."""
        sections = self.client.get_sections_by_volume(volume)
        if not sections:
            return None

        section = rng.choice(sections)
        # Create a minimal halacha with section info and a link
        return Halacha(
            section=section,
            chapter=1,
            siman=1,
            hebrew_text="לא ניתן לטעון את הטקסט כרגע. לחץ על הקישור לקריאה בספריא.",
            english_text=None,
            sefaria_url=f"https://www.sefaria.org/{section.ref_base.replace(' ', '_')}",
        )

    def get_daily_pair(self, for_date: date | None = None) -> DailyPair | None:
        """
        Get the pair of halachot for a given date.

        Selection is deterministic - same date always returns same pair.
        Uses caching to avoid repeated API calls.
        Always returns something (even fallback) unless catalog is missing.
        """
        if for_date is None:
            for_date = date.today()

        # Try to load from cache first
        cached = self._load_cached_pair(for_date)
        if cached:
            return cached

        # Fetch from API
        rng = self._get_daily_rng(for_date)
        vol1, vol2 = self._select_two_volumes(rng)

        logger.info(f"Selecting halachot for {for_date}: {vol1} + {vol2}")

        # Get first halacha (with fallback)
        first = self.client.get_random_halacha_from_volume(vol1, rng)
        if not first:
            logger.warning(f"API failed for {vol1}, using fallback")
            first = self._get_fallback_halacha(vol1, rng)
        if not first:
            logger.error(f"Failed to get halacha from {vol1}")
            return None

        # Get second halacha (with fallback)
        second = self.client.get_random_halacha_from_volume(vol2, rng)
        if not second:
            logger.warning(f"API failed for {vol2}, using fallback")
            second = self._get_fallback_halacha(vol2, rng)
        if not second:
            logger.error(f"Failed to get halacha from {vol2}")
            return None

        pair = DailyPair(
            first=first,
            second=second,
            date_seed=self._get_daily_seed(for_date),
        )

        # Only cache if we got real content (not fallback)
        fallback_marker = "לא ניתן לטעון"
        if (
            fallback_marker not in first.hebrew_text
            and fallback_marker not in second.hebrew_text
        ):
            self._save_cached_pair(pair, for_date)

        return pair
