"""
Daf (page) to Sefaria section mapping for Likutei Halachot.

This module converts page numbers from the Ashreinu schedule to valid
Sefaria API references. The Ashreinu schedule uses daf (page) numbers,
while Sefaria uses section/siman/ot references.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class SefariaRef:
    """A valid Sefaria reference for Likutei Halachot."""
    ref: str  # e.g., "Likutei_Halakhot,_Choshen_Mishpat,_Laws_of_a_Deathly_Ill_Person.1.1"
    he_ref: str  # e.g., "ליקוטי הלכות, חושן משפט, הלכות מתנת שכיב מרע א׳:א׳"
    halakha_en: str  # e.g., "Laws of a Deathly Ill Person"
    halakha_he: str  # e.g., "הלכות מתנת שכיב מרע"
    siman: int  # Siman number within the halakha
    ot: int  # Ot (paragraph) number within the siman

    @property
    def sefaria_url(self) -> str:
        """Generate Sefaria URL for this reference."""
        return f"https://www.sefaria.org/{self.ref.replace(' ', '_')}"


class DafMapper:
    """
    Maps daf (page) numbers to Sefaria section references.

    The mapping is based on character count estimates from Sefaria text exports.
    Each daf is approximately 5500 characters of Hebrew text.
    """

    # Volume keys to mapping file names
    VOLUME_MAPPING_FILES = {
        ("Orach_Chaim", 1): "orach_chaim_1_daf_mapping.json",
        ("Orach_Chaim", 2): "orach_chaim_2_daf_mapping.json",
        ("Yoreh_Deah", 1): "yoreh_deah_1_daf_mapping.json",
        ("Yoreh_Deah", 2): "yoreh_deah_2_daf_mapping.json",
        ("Even_HaEzer", 1): "even_haezer_1_daf_mapping.json",
        ("Choshen_Mishpat", 1): "choshen_mishpat_1_daf_mapping.json",
        ("Choshen_Mishpat", 2): "choshen_mishpat_2_daf_mapping.json",
    }

    # Sefaria chelek names
    SEFARIA_CHELEK = {
        "Orach_Chaim": "Orach_Chaim",
        "Yoreh_Deah": "Yoreh_Deah",
        "Even_HaEzer": "Even_HaEzer",
        "Choshen_Mishpat": "Choshen_Mishpat",
    }

    def __init__(self, mappings_dir: Path):
        """
        Initialize the DafMapper.

        Args:
            mappings_dir: Directory containing daf mapping JSON files
        """
        self.mappings_dir = mappings_dir
        self._mappings: Dict[tuple, Dict] = {}
        self._load_all_mappings()

    def _load_all_mappings(self):
        """Load all available mapping files."""
        for (volume, part), filename in self.VOLUME_MAPPING_FILES.items():
            filepath = self.mappings_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self._mappings[(volume, part)] = json.load(f)
                    logger.info(f"Loaded daf mapping for {volume} Part {part}")
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load mapping {filename}: {e}")

    def has_mapping(self, volume: str, part: int) -> bool:
        """Check if a mapping exists for the given volume and part."""
        return (volume, part) in self._mappings

    def get_sefaria_ref(self, volume: str, part: int, daf: int) -> Optional[SefariaRef]:
        """
        Convert a daf number to a Sefaria reference.

        Args:
            volume: Volume name (e.g., "Choshen_Mishpat")
            part: Part number (1 or 2)
            daf: Page number in the printed edition

        Returns:
            SefariaRef object if mapping found, None otherwise
        """
        mapping = self._mappings.get((volume, part))
        if not mapping:
            logger.warning(f"No mapping available for {volume} Part {part}")
            return None

        # Search through halakhot to find the one containing this daf
        for halakha in mapping.get("halakhot", []):
            if halakha.get("start_daf", 0) <= daf <= halakha.get("end_daf", 0):
                # Found the halakha, now find the siman
                for siman in halakha.get("simanim", []):
                    if siman.get("start_daf", 0) <= daf <= siman.get("end_daf", 0):
                        # Found the siman, now find the ot
                        for ot in siman.get("otot", []):
                            if ot.get("start_daf", 0) <= daf <= ot.get("end_daf", 0):
                                # Found the exact ot
                                chelek = self.SEFARIA_CHELEK.get(volume, volume)
                                halakha_name = halakha.get("name_en", "")
                                siman_num = siman.get("siman", 1)
                                ot_num = ot.get("ot", 1)

                                # Build Sefaria reference
                                ref = f"Likutei_Halakhot,_{chelek},_{halakha_name.replace(' ', '_')}.{siman_num}.{ot_num}"
                                he_ref = f"ליקוטי הלכות, {self._get_hebrew_chelek(volume)}, {halakha.get('name_he', '')} {self._to_hebrew_num(siman_num)}:{self._to_hebrew_num(ot_num)}"

                                return SefariaRef(
                                    ref=ref,
                                    he_ref=he_ref,
                                    halakha_en=halakha_name,
                                    halakha_he=halakha.get("name_he", ""),
                                    siman=siman_num,
                                    ot=ot_num,
                                )

        logger.warning(f"Could not find mapping for daf {daf} in {volume} Part {part}")
        return None

    def get_all_refs_for_daf(self, volume: str, part: int, daf: int) -> List[SefariaRef]:
        """
        Get all Sefaria references that appear on a given daf.

        A single daf may contain multiple otot (paragraphs).

        Args:
            volume: Volume name
            part: Part number
            daf: Page number

        Returns:
            List of SefariaRef objects for all content on this daf
        """
        refs = []
        mapping = self._mappings.get((volume, part))
        if not mapping:
            return refs

        for halakha in mapping.get("halakhot", []):
            # Check if this halakha overlaps with our daf
            if halakha.get("end_daf", 0) < daf or halakha.get("start_daf", float('inf')) > daf:
                continue

            for siman in halakha.get("simanim", []):
                if siman.get("end_daf", 0) < daf or siman.get("start_daf", float('inf')) > daf:
                    continue

                for ot in siman.get("otot", []):
                    ot_start = ot.get("start_daf", 0)
                    ot_end = ot.get("end_daf", 0)

                    # Check if this ot overlaps with our daf
                    if ot_start <= daf <= ot_end or (ot_start <= daf + 1 and ot_end >= daf):
                        chelek = self.SEFARIA_CHELEK.get(volume, volume)
                        halakha_name = halakha.get("name_en", "")
                        siman_num = siman.get("siman", 1)
                        ot_num = ot.get("ot", 1)

                        ref = f"Likutei_Halakhot,_{chelek},_{halakha_name.replace(' ', '_')}.{siman_num}.{ot_num}"
                        he_ref = f"ליקוטי הלכות, {self._get_hebrew_chelek(volume)}, {halakha.get('name_he', '')} {self._to_hebrew_num(siman_num)}:{self._to_hebrew_num(ot_num)}"

                        refs.append(SefariaRef(
                            ref=ref,
                            he_ref=he_ref,
                            halakha_en=halakha_name,
                            halakha_he=halakha.get("name_he", ""),
                            siman=siman_num,
                            ot=ot_num,
                        ))

        return refs

    def _get_hebrew_chelek(self, volume: str) -> str:
        """Get Hebrew name for the chelek."""
        names = {
            "Orach_Chaim": "אורח חיים",
            "Yoreh_Deah": "יורה דעה",
            "Even_HaEzer": "אבן העזר",
            "Choshen_Mishpat": "חושן משפט",
        }
        return names.get(volume, volume)

    def _to_hebrew_num(self, num: int) -> str:
        """Convert number to Hebrew numerals (simplified)."""
        # Simple conversion for small numbers
        ones = ['', 'א׳', 'ב׳', 'ג׳', 'ד׳', 'ה׳', 'ו׳', 'ז׳', 'ח׳', 'ט׳']
        tens = ['', 'י', 'כ', 'ל', 'מ', 'נ', 'ס', 'ע', 'פ', 'צ']

        if num < 10:
            return ones[num]
        elif num < 100:
            return tens[num // 10] + (ones[num % 10].rstrip('׳') if num % 10 else '') + '׳'
        else:
            return str(num)  # Fall back to Arabic numerals for large numbers

    def get_mapping_info(self, volume: str, part: int) -> Optional[Dict[str, Any]]:
        """Get metadata about a mapping."""
        mapping = self._mappings.get((volume, part))
        if mapping:
            return mapping.get("metadata", {})
        return None


# Singleton instance
_mapper: Optional[DafMapper] = None


def get_daf_mapper(data_dir: Path) -> DafMapper:
    """Get or create the DafMapper singleton."""
    global _mapper
    if _mapper is None:
        mappings_dir = data_dir / "daf_mappings"
        _mapper = DafMapper(mappings_dir)
    return _mapper
