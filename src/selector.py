"""Daily halacha selection logic."""

import hashlib
import logging
import random
from datetime import date

from .models import DailyPair
from .sefaria import VOLUMES, SefariaClient

logger = logging.getLogger(__name__)


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

    def get_daily_pair(self, for_date: date | None = None) -> DailyPair | None:
        """
        Get the pair of halachot for a given date.

        Selection is deterministic - same date always returns same pair.
        """
        if for_date is None:
            for_date = date.today()

        rng = self._get_daily_rng(for_date)
        vol1, vol2 = self._select_two_volumes(rng)

        logger.info(f"Selecting halachot for {for_date}: {vol1} + {vol2}")

        # Get first halacha
        first = self.client.get_random_halacha_from_volume(vol1, rng)
        if not first:
            logger.error(f"Failed to get halacha from {vol1}")
            return None

        # Get second halacha
        second = self.client.get_random_halacha_from_volume(vol2, rng)
        if not second:
            logger.error(f"Failed to get halacha from {vol2}")
            return None

        return DailyPair(
            first=first,
            second=second,
            date_seed=self._get_daily_seed(for_date),
        )
