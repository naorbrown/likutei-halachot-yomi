"""
Hebrew calendar utilities for Likutei Halachot Yomi.
"""

from dataclasses import dataclass
from datetime import date
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Hebrew month constants
MONTH_TISHREI = 7
MONTH_CHESHVAN = 8
MONTH_KISLEV = 9
MONTH_TEVET = 10
MONTH_SHEVAT = 11
MONTH_ADAR = 12
MONTH_ADAR_II = 13
MONTH_NISAN = 1
MONTH_IYAR = 2
MONTH_SIVAN = 3
MONTH_TAMMUZ = 4
MONTH_AV = 5
MONTH_ELUL = 6

# Month names mapping
MONTH_NAMES = {
    MONTH_NISAN: ("nisan", "ניסן"),
    MONTH_IYAR: ("iyar", "אייר"),
    MONTH_SIVAN: ("sivan", "סיון"),
    MONTH_TAMMUZ: ("tammuz", "תמוז"),
    MONTH_AV: ("av", "אב"),
    MONTH_ELUL: ("elul", "אלול"),
    MONTH_TISHREI: ("tishrei", "תשרי"),
    MONTH_CHESHVAN: ("cheshvan", "חשוון"),
    MONTH_KISLEV: ("kislev", "כסלו"),
    MONTH_TEVET: ("tevet", "טבת"),
    MONTH_SHEVAT: ("shevat", "שבט"),
    MONTH_ADAR: ("adar", "אדר"),
    MONTH_ADAR_II: ("adar_ii", "אדר ב׳"),
}

# Hebrew numerals for days
HEBREW_NUMERALS = {
    1: "א׳", 2: "ב׳", 3: "ג׳", 4: "ד׳", 5: "ה׳",
    6: "ו׳", 7: "ז׳", 8: "ח׳", 9: "ט׳", 10: "י׳",
    11: "י״א", 12: "י״ב", 13: "י״ג", 14: "י״ד", 15: "ט״ו",
    16: "ט״ז", 17: "י״ז", 18: "י״ח", 19: "י״ט", 20: "כ׳",
    21: "כ״א", 22: "כ״ב", 23: "כ״ג", 24: "כ״ד", 25: "כ״ה",
    26: "כ״ו", 27: "כ״ז", 28: "כ״ח", 29: "כ״ט", 30: "ל׳",
}

# Hebrew year formatting
HEBREW_YEAR_PREFIX = {
    5: "ה׳",
}

HEBREW_YEAR_LETTERS = {
    400: "ת", 300: "ש", 200: "ר", 100: "ק",
    90: "צ", 80: "פ", 70: "ע", 60: "ס", 50: "נ",
    40: "מ", 30: "ל", 20: "כ", 10: "י",
    9: "ט", 8: "ח", 7: "ז", 6: "ו", 5: "ה",
    4: "ד", 3: "ג", 2: "ב", 1: "א",
}


@dataclass
class HebrewDate:
    """Represents a Hebrew date."""
    year: int
    month: int
    day: int

    @property
    def month_key(self) -> str:
        """Get the English month key for schedule lookup."""
        return MONTH_NAMES.get(self.month, ("unknown", ""))[0]

    @property
    def month_hebrew(self) -> str:
        """Get the Hebrew month name."""
        return MONTH_NAMES.get(self.month, ("", "לא ידוע"))[1]

    @property
    def day_hebrew(self) -> str:
        """Get the Hebrew day numeral."""
        return HEBREW_NUMERALS.get(self.day, str(self.day))

    @property
    def year_hebrew(self) -> str:
        """Get the Hebrew year representation."""
        return format_hebrew_year(self.year)

    @property
    def full_date_hebrew(self) -> str:
        """Get full formatted Hebrew date."""
        return f"{self.day_hebrew} {self.month_hebrew} {self.year_hebrew}"

    def __str__(self) -> str:
        return self.full_date_hebrew


def format_hebrew_year(year: int) -> str:
    """Format Hebrew year number as Hebrew letters."""
    # For years like 5786, we typically show just the last 3 digits with ה׳ prefix
    # 5786 -> ה׳תשפ״ו
    remainder = year % 1000  # Get last 3 digits (786)

    result = "ה׳"
    for value in sorted(HEBREW_YEAR_LETTERS.keys(), reverse=True):
        while remainder >= value:
            result += HEBREW_YEAR_LETTERS[value]
            remainder -= value

    # Add gershayim before last letter
    if len(result) > 2:
        result = result[:-1] + "״" + result[-1]

    return result


def get_hebrew_date(gregorian_date: Optional[date] = None) -> HebrewDate:
    """
    Get the Hebrew date for a given Gregorian date.

    Uses pyluach if available, otherwise returns a hardcoded date for testing.
    """
    if gregorian_date is None:
        gregorian_date = date.today()

    try:
        from pyluach import dates
        heb_date = dates.HebrewDate.from_pydate(gregorian_date)
        return HebrewDate(
            year=heb_date.year,
            month=heb_date.month,
            day=heb_date.day
        )
    except ImportError:
        logger.warning("pyluach not available, using fallback date")
        # Fallback for testing - January 27, 2026 = 9 Shevat 5786
        return HebrewDate(year=5786, month=MONTH_SHEVAT, day=9)


def is_leap_year(year: int) -> bool:
    """Check if a Hebrew year is a leap year."""
    return (7 * year + 1) % 19 < 7


def get_month_length(year: int, month: int) -> int:
    """Get the number of days in a Hebrew month."""
    # Months with 30 days
    thirty_day_months = {MONTH_NISAN, MONTH_SIVAN, MONTH_AV, MONTH_TISHREI, MONTH_SHEVAT}

    # Months with 29 days
    twenty_nine_day_months = {MONTH_IYAR, MONTH_TAMMUZ, MONTH_ELUL, MONTH_TEVET, MONTH_ADAR_II}

    if month in thirty_day_months:
        return 30
    elif month in twenty_nine_day_months:
        return 29
    elif month == MONTH_CHESHVAN:
        # Cheshvan can have 29 or 30 days
        return 30  # Simplified - would need actual calculation
    elif month == MONTH_KISLEV:
        # Kislev can have 29 or 30 days
        return 30  # Simplified - would need actual calculation
    elif month == MONTH_ADAR:
        return 30 if is_leap_year(year) else 29
    else:
        return 30


def get_days_in_year(year: int) -> int:
    """Get total days in a Hebrew year (starting from Tishrei)."""
    months = [MONTH_TISHREI, MONTH_CHESHVAN, MONTH_KISLEV, MONTH_TEVET,
              MONTH_SHEVAT, MONTH_ADAR]
    if is_leap_year(year):
        months.append(MONTH_ADAR_II)
    months.extend([MONTH_NISAN, MONTH_IYAR, MONTH_SIVAN, MONTH_TAMMUZ, MONTH_AV, MONTH_ELUL])

    return sum(get_month_length(year, m) for m in months)


def get_day_of_year(hebrew_date: HebrewDate) -> int:
    """
    Get the day number within the Hebrew year (1-indexed, starting from 1 Tishrei).
    """
    year = hebrew_date.year
    month = hebrew_date.month
    day = hebrew_date.day

    # Order of months starting from Tishrei
    month_order = [MONTH_TISHREI, MONTH_CHESHVAN, MONTH_KISLEV, MONTH_TEVET,
                   MONTH_SHEVAT, MONTH_ADAR]
    if is_leap_year(year):
        month_order.append(MONTH_ADAR_II)
    month_order.extend([MONTH_NISAN, MONTH_IYAR, MONTH_SIVAN, MONTH_TAMMUZ, MONTH_AV, MONTH_ELUL])

    days = 0
    for m in month_order:
        if m == month:
            days += day
            break
        days += get_month_length(year, m)

    return days
