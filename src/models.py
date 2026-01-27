"""Data models for Likutei Halachot Yomi."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HalachaSection:
    """Represents a section of Likutei Halachot in Sefaria."""

    volume: str  # Orach Chaim, Yoreh Deah, Even HaEzer, Choshen Mishpat
    section: str  # English section name
    section_he: str  # Hebrew section name
    ref_base: str  # Base Sefaria reference (without chapter/section numbers)
    has_english: bool = False

    @property
    def volume_he(self) -> str:
        """Get Hebrew volume name."""
        mapping = {
            "Orach Chaim": "אורח חיים",
            "Yoreh Deah": "יורה דעה",
            "Even HaEzer": "אבן העזר",
            "Choshen Mishpat": "חושן משפט",
        }
        return mapping.get(self.volume, self.volume)


@dataclass(frozen=True)
class Halacha:
    """A single halacha with its text and metadata."""

    section: HalachaSection
    chapter: int  # Halakha number
    siman: int  # Section within halakha
    hebrew_text: str
    english_text: str | None
    sefaria_url: str

    @property
    def reference(self) -> str:
        """Full Sefaria reference string."""
        return f"{self.section.ref_base}.{self.chapter}.{self.siman}"

    @property
    def hebrew_reference(self) -> str:
        """Hebrew reference for display."""
        return f"ליקוטי הלכות, {self.section.volume_he}, {self.section.section_he} {self.chapter}:{self.siman}"


@dataclass(frozen=True)
class DailyPair:
    """A pair of halachot for the day from two different volumes."""

    first: Halacha
    second: Halacha
    date_seed: str  # Date string used for deterministic selection

    def __post_init__(self):
        """Validate that halachot are from different volumes."""
        if self.first.section.volume == self.second.section.volume:
            raise ValueError("Daily pair must contain halachot from different volumes")
