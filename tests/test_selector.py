"""Tests for halacha selection logic."""

from datetime import date
from unittest.mock import Mock, patch

import pytest

from src.sefaria import SefariaClient
from src.selector import HalachaSelector


class TestHalachaSelector:
    """Tests for HalachaSelector."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Sefaria client."""
        return Mock(spec=SefariaClient)

    @pytest.fixture
    def selector(self, mock_client):
        """Create a selector with mock client."""
        return HalachaSelector(mock_client)

    def test_same_date_same_seed(self, selector):
        """Same date should produce same seed."""
        date1 = date(2024, 1, 27)
        seed1 = selector._get_daily_seed(date1)
        seed2 = selector._get_daily_seed(date1)
        assert seed1 == seed2

    def test_different_dates_different_seeds(self, selector):
        """Different dates should produce different seeds."""
        date1 = date(2024, 1, 27)
        date2 = date(2024, 1, 28)
        seed1 = selector._get_daily_seed(date1)
        seed2 = selector._get_daily_seed(date2)
        assert seed1 != seed2

    def test_deterministic_volume_selection(self, selector):
        """Same date should select same volumes."""
        test_date = date(2024, 1, 27)
        rng1 = selector._get_daily_rng(test_date)
        rng2 = selector._get_daily_rng(test_date)

        vol1a, vol1b = selector._select_two_volumes(rng1)
        vol2a, vol2b = selector._select_two_volumes(rng2)

        assert vol1a == vol2a
        assert vol1b == vol2b

    def test_volumes_are_different(self, selector):
        """Selected volumes should always be different."""
        for day in range(1, 31):
            test_date = date(2024, 1, day)
            rng = selector._get_daily_rng(test_date)
            vol1, vol2 = selector._select_two_volumes(rng)
            assert vol1 != vol2, f"Same volume selected on {test_date}"

    def test_get_daily_pair_calls_client(
        self, selector, mock_client, sample_halacha_oc, sample_halacha_yd, tmp_path
    ):
        """get_daily_pair should call client for both volumes."""
        mock_client.get_random_halacha_from_volume.side_effect = [
            sample_halacha_oc,
            sample_halacha_yd,
        ]

        # Use temp cache dir to avoid polluting real cache
        with patch("src.selector.CACHE_DIR", tmp_path):
            result = selector.get_daily_pair(date(2098, 1, 1))

        assert result is not None
        assert mock_client.get_random_halacha_from_volume.call_count == 2

    def test_get_daily_pair_returns_none_on_failure(
        self, selector, mock_client, tmp_path
    ):
        """get_daily_pair should return None if client fails (no cache)."""
        mock_client.get_random_halacha_from_volume.return_value = None

        # Use temp cache dir to avoid polluting real cache
        with patch("src.selector.CACHE_DIR", tmp_path):
            result = selector.get_daily_pair(date(2099, 12, 31))

        assert result is None
