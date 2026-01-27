"""
Schedule management for Likutei Halachot Yomi.

This module handles the daily learning schedule, mapping Hebrew dates
to specific portions of Likutei Halachot.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from .hebrew_calendar import (
    HebrewDate, get_day_of_year, get_days_in_year, is_leap_year,
    MONTH_TISHREI, MONTH_CHESHVAN, MONTH_KISLEV, MONTH_TEVET, MONTH_SHEVAT,
    MONTH_ADAR, MONTH_ADAR_II, MONTH_NISAN, MONTH_IYAR, MONTH_SIVAN,
    MONTH_TAMMUZ, MONTH_AV, MONTH_ELUL, get_month_length
)

logger = logging.getLogger(__name__)


@dataclass
class DailyPortion:
    """Represents a single daily learning portion."""
    ref: str  # Sefaria reference
    he_ref: str  # Hebrew reference
    description: str = ""
    section_name: str = ""
    chapter: int = 0
    subsection: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref": self.ref,
            "heRef": self.he_ref,
            "description": self.description,
            "sectionName": self.section_name,
            "chapter": self.chapter,
            "subsection": self.subsection,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DailyPortion":
        return cls(
            ref=data.get("ref", ""),
            he_ref=data.get("heRef", ""),
            description=data.get("description", ""),
            section_name=data.get("sectionName", ""),
            chapter=data.get("chapter", 0),
            subsection=data.get("subsection", 0),
        )


@dataclass
class DaySchedule:
    """Schedule for a single day."""
    hebrew_date: str  # Format: "month_key:day" e.g., "shevat:9"
    portions: List[DailyPortion] = field(default_factory=list)
    special_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "portions": [p.to_dict() for p in self.portions],
            "note": self.special_note,
        }


# Complete list of all Likutei Halachot sections in order
# This is the canonical order for learning through the entire work
LIKUTEI_HALACHOT_SECTIONS = [
    # Orach Chaim
    ("Laws of Morning Conduct", "הלכות השכמת הבוקר", 5),
    ("Laws of Morning Hand Washing", "הלכות נטילת ידים שחרית", 6),
    ("Laws of Fringes", "הלכות ציצית", 5),
    ("Laws of Phylacteries", "הלכות תפילין", 6),
    ("Laws for Morning Blessings", "הלכות ברכת השחר", 5),
    ("Laws of Torah Blessings", "הלכות ברכות התורה", 6),
    ("Laws of Kaddish", "הלכות קדיש", 1),
    ("Laws of Reciting Shema", "הלכות קריאת שמע", 5),
    ("Laws of Prayer", "הלכות תפלה", 5),
    ("Laws of Priestly Blessings", "הלכות נשיאת כפים", 5),
    ("Laws of Tachanun", "הלכות נפילת אפים", 2),
    ("Laws of Sidra Kaddish", "הלכות קדושה דסידרא", 2),
    ("Laws of Reading the Torah", "הלכות קריאת התורה", 6),
    ("Laws of the Synagogue", "הלכות בית הכנסת", 7),
    ("Laws of Business", "הלכות משא ומתן", 5),
    ("Laws of Washing One's Hands for a Meal", "הלכות נטילת ידים לסעודה ובציעת הפת", 6),
    ("Laws of Meals", "הלכות סעודה", 5),
    ("Laws of Grace After Meals and Washing after Meals", "הלכות ברכת המזון ומים אחרונים", 5),
    ("Laws of Blessings Over Fruit", "הלכות ברכת הפרות", 5),
    ("Laws of Blessing on Fragrance", "הלכות ברכת הריח", 5),
    ("Laws of Thanksgiving Blessings", "הלכות ברכת הודאה", 5),
    ("Laws of Blessing on Sights and Other Blessings", "הלכות ברכות הראיה וברכות פרטיות", 5),
    ("Laws for Afternoon Prayer", "הלכות תפלת המנחה", 7),
    ("Laws for Evening Prayer", "הלכות תפלת ערבית", 5),
    ("Laws of Reciting Shema Before Retiring", "הלכות קריאת שמע שעל המטה", 5),
    ("Laws of the Sabbath", "הלכות שבת", 7),
    ("Laws of Joining Domains", "הלכות תחומין וערובי תחומין", 5),
    ("Laws of the New Moon", "הלכות ראש חדש", 7),
    ("Laws of Passover", "הלכות פסח", 9),
    ("Laws of Counter the Omer", "הלכות ספירת העמר", 5),
    ("Laws of the Shavuot Festival", "הלכות שבועות", 4),
    ("Laws of the Festival Day", "הלכות יום טוב", 5),
    ("Laws of the Week Days of a Festival", "הלכות חול המועד", 3),
    ("Laws of the Ninth of Av and Other Fast Days", "הלכות תשעה באב ותעניות", 5),
    ("Laws of the New Year", "הלכות ראש השנה", 6),
    ("Laws of the Day of Atonement", "הלכות יום הכפורים", 5),
    ("Laws of the Festival of Booths", "הלכות סוכה", 8),
    ("Laws of the Palm Branch", "הלכות לולב ואתרוג", 6),
    ("Laws of the Hoshana Rabba Festival", "הלכות הושענא רבה", 2),
    ("Laws of the Hannukah Festival", "הלכות חנוכה", 7),
    ("Laws of the Four Festive Torah Portions", "הלכות ארבע פרשיות", 3),
    ("Laws of Purim", "הלכות פורים", 6),
    # Yoreh Deah
    ("Laws of Slaughtering", "הלכות שחיטה", 5),
    ("Laws of Unfit Animals", "הלכות טרפות", 4),
    ("Laws of Priestly Gifts", "הלכות מתנות כהונה", 4),
    ("Laws of a Limb from a Live Animal", "הלכות אבר מן החי", 4),
    ("Laws of Meat that was Unobserved", "הלכות הלכות בשר שנתעלם מן העין", 2),
    ("Laws of Fat and Blood", "הלכות חלב ודם", 5),
    ("Laws of Blood", "הלכות דם", 5),
    ("Laws of Salting", "הלכות מליחה", 5),
    ("Laws of Domesticated and Undomesticated Animals", "הלכות סימני בהמה וחיה טהורה", 4),
    ("Laws of Things that Come from a Live Animal", "הלכות דברים היוצאים מן החי", 4),
    ("Laws of Birds", "הלכות סימני עוף טהור", 4),
    ("Laws of Fish", "הלכות דגים", 3),
    ("Laws of Insects", "הלכות תולעים", 3),
    ("Laws of Eggs", "הלכות ביצים", 4),
    ("Laws of Meat and Milk", "הלכות בשר בחלב", 5),
    ("Laws of Mixtures", "הלכות תערובות", 5),
    ("Laws of Non Jewish Food", "הלכות מאכלי עכו\"ם", 4),
    ("Laws of Kashering Vessels", "הלכות הכשר כלים", 4),
    ("Laws of Taste Transfer", "הלכות נותן טעם לפגם", 4),
    ("Laws of Libational Wine", "הלכות יין נסך", 4),
    ("Laws of Wine Vessels", "הלכות כלי היין", 3),
    ("Laws of Idol Worship", "הלכות עבודת אלילים", 4),
    ("Laws of Interest", "הלכות ריבית", 5),
    ("Laws of Idolatrous Practices", "הלכות חוקות העכו\"ם", 4),
    ("Laws of Sourcerers and Enchanters", "הלכות מעונן ומנחש", 3),
    ("Laws of Shaving and Tatooing", "הלכות קרחה וכתובת קעקע", 4),
    ("Laws of Shaving", "הלכות גילוח", 5),
    ("Laws of Forbidden Dresss", "הלכות לא ילבש", 4),
    ("Laws of a Menstruant", "הלכות נדה", 4),
    ("Laws of Ritual Baths", "הלכות מקוואות", 4),
    ("Laws of Vows", "הלכות נדרים", 5),
    ("Laws of Oaths", "הלכות שבועות", 4),
    ("Laws of Honouring One's Father and Mother", "הלכות כבוד אב ואם", 3),
    ("Laws of Honouring One's Rabbi and a Torah Scholar", "הלכות כבוד רבו ותלמיד חכם", 3),
    ("Laws of Teachers", "הלכות מלמדים", 4),
    ("Laws of Torah Study", "הלכות תלמוד תורה", 5),
    ("Laws of Charity", "הלכות צדקה", 5),
    ("Laws of Circumcision", "הלכות מילה", 5),
    ("Laws of Slaves", "הלכות עבדים", 3),
    ("Laws of Converts", "הלכות גרים", 5),
    ("Laws of a Torah Scroll", "הלכות ספר תורה", 4),
    ("Laws of a Mezuzah", "הלכות מזוזה", 5),
    ("Laws of Sending Away the Mother Bird", "הלכות שלוח הקן", 5),
    ("Laws of New Grain", "הלכות חדש", 4),
    ("Laws of Three Year Old Trees", "הלכות ערלה", 5),
    ("Laws of Mixed Crops", "הלכות כלאי הכרם ואילן", 4),
    ("Laws of Mixed Breeding", "הלכות כלאי בהמה", 3),
    ("Laws of Fobidden Fabric Blends", "הלכות כלאי בגדים", 5),
    ("Laws of Redeeming the Firstborn", "הלכות פדיון בכור", 5),
    ("Laws of Firstborn Kosher Animals", "הלכות בכור בהמה טהורה", 4),
    ("Laws of Firstborn Donkey", "הלכות פדיון פטר חמור", 4),
    ("Laws of Separating From Dough", "הלכות חלה", 5),
    ("Laws of Tithes", "הלכות תרומות ומעשרות", 4),
    ("Laws of First Shearings", "הלכות ראשית הגז", 4),
    # Even HaEzer
    ("Laws of Procreation", "הלכות פריה ורביה ואישות", 4),
    ("Laws of Matrimony", "הלכות אישות", 3),
    ("Laws of Sanctification", "הלכות קדושין", 3),
    ("Laws of a Bill of Marriage", "הלכות כתובות", 4),
    ("Laws of a Bill of Divorce", "הלכות גטין", 4),
    ("Laws of Levirate Marriage", "הלכות יבום", 4),
    ("Laws of Adulterer", "הלכות סוטה", 3),
    ("Laws of Rape and Seduction", "הלכות אונס ומפתה", 3),
    # Choshen Mishpat
    ("Laws for Judges", "הלכות דינים", 5),
    ("Laws of Testimony", "הלכות עדות", 5),
    ("Laws of Loans", "הלכות הלואה", 5),
    ("Laws of Plaintiffs and Defendants", "הלכות טוען ונטען", 4),
    ("Laws of Collecting Loans", "הלכות גבית מלוה", 4),
    ("Laws of Collecting Loans from Orphans", "הלכות גבית חוב מהיתומים", 3),
    ("Laws of Collecting Loans from Purchasers and Laws Designated Collection", "הלכות גבית חוב מהלקוחות ואפותיקי", 3),
    ("Laws of an Agent Collecting Debts and Authorisation", "הלכות העושה שליח לגבות חובו", 2),
    ("Laws of Authorisation", "הלכות כח והרשאה", 3),
    ("Laws of Guaranteeing", "הלכות ערב", 4),
    ("Laws of Movable Property", "הלכות חזקת מטלטלין", 4),
    ("Laws of Immovable Property", "הלכות חזקת קרקעות", 4),
    ("Laws of Neighbor Damages", "הלכות נזקי שכנים", 4),
    ("Laws of Immovable Partnerships", "הלכות שותפים בקרקע", 3),
    ("Laws of Divisions of Partnerships", "הלכות חלקת שתפים", 3),
    ("Laws of Boundaries", "הלכות מצרנות", 3),
    ("Laws of Partners", "הלכות שתפין", 4),
    ("Laws of Emissaries", "הלכות שלוחין", 4),
    ("Laws of Buying and Selling", "הלכות מקח וממכר", 5),
    ("Laws of Over and Under Charging", "הלכות אונאה", 5),
    ("Laws of Gifting", "הלכות מתנה", 5),
    ("Laws of a Deathly Ill Person", "הלכות מתנת שכיב מרע", 4),
    ("Laws of Lost and Found", "הלכות אבדה ומציאה", 5),
    ("Laws of Unloading and Loading", "הלכות פריקה וטעינה", 3),
    ("Laws of Ownerless Property and Property of Non Jews", "הלכות הפקר ונכסי הגר", 4),
    ("Laws of Inheritance", "הלכות נחלות", 4),
    ("Laws of an Apotropos", "הלכות אפטרופוס", 3),
    ("Laws of Deposit and Four Guards", "הלכות פקדון וארבעה שומרים", 5),
    ("Laws for Paid Guardians", "הלכות שומר שכר", 5),
    ("Laws of Artisans", "הלכות אמנין", 4),
    ("Laws of Hiring", "הלכות שוכר", 4),
    ("Laws of Leasing and Contract Work", "הלכות חכירות וקבלנות", 3),
    ("Laws of Hiring Labourers", "הלכות שכירות פועלים", 5),
    ("Laws of Borrowing", "הלכות שאלה", 5),
    ("Laws of Theft", "הלכות גנבה", 5),
    ("Laws of Stealing", "הלכות גזלה", 4),
    ("Laws of Damages", "הלכות נזיקין", 4),
    ("Laws of Causing a Loss and Reporting to Government", "הלכות מאבד ממון חברו ומסור", 3),
    ("Laws of Monetary Damages", "הלכות נזקי ממון", 3),
    ("Laws of Injuring a Person", "הלכות חובל בחברו", 5),
    ("Laws of Roof Rails and Preservation of Life", "הלכות מעקה ושמירת הנפש", 5),
]


def build_sefaria_ref(section_name: str, chapter: int = 1, subsection: int = 1) -> str:
    """
    Build a Sefaria reference for a Likutei Halachot section.

    Args:
        section_name: English section name
        chapter: Chapter number (Halakhah number)
        subsection: Subsection within the chapter

    Returns:
        Formatted Sefaria reference
    """
    # Format section name for URL
    formatted_name = section_name.replace(" ", "_")
    return f"Likutei_Halakhot,_Orach_Chaim,_{formatted_name}.{chapter}.{subsection}"


def generate_yearly_schedule(year: int) -> Dict[str, Dict[str, Any]]:
    """
    Generate a complete yearly schedule for Likutei Halachot Yomi.

    The schedule distributes all sections across the Hebrew year,
    learning approximately one chapter subsection per day.

    Args:
        year: Hebrew year

    Returns:
        Dictionary mapping "month_key:day" to portion data
    """
    # Calculate total days in year
    total_days = get_days_in_year(year)
    leap = is_leap_year(year)

    # Calculate total chapters/subsections
    total_portions = sum(chapters for _, _, chapters in LIKUTEI_HALACHOT_SECTIONS)
    logger.info(f"Generating schedule for year {year}: {total_days} days, {total_portions} portions")

    # Create schedule dictionary
    schedule = {}

    # Build flat list of all portions
    all_portions = []
    for section_name, he_section_name, num_chapters in LIKUTEI_HALACHOT_SECTIONS:
        for chapter in range(1, num_chapters + 1):
            all_portions.append((section_name, he_section_name, chapter))

    # Distribute portions across days
    # If more days than portions, some days get multiple sections
    # If more portions than days, some days get multiple portions
    portions_per_day = max(1, len(all_portions) // total_days)

    day_num = 1
    portion_idx = 0

    month_order = [MONTH_TISHREI, MONTH_CHESHVAN, MONTH_KISLEV, MONTH_TEVET,
                   MONTH_SHEVAT, MONTH_ADAR]
    if leap:
        month_order.append(MONTH_ADAR_II)
    month_order.extend([MONTH_NISAN, MONTH_IYAR, MONTH_SIVAN, MONTH_TAMMUZ, MONTH_AV, MONTH_ELUL])

    from .hebrew_calendar import MONTH_NAMES

    for month in month_order:
        month_key = MONTH_NAMES[month][0]
        month_length = get_month_length(year, month)

        for day in range(1, month_length + 1):
            key = f"{month_key}:{day}"
            portions = []

            # Assign portion(s) for this day
            for _ in range(portions_per_day):
                if portion_idx < len(all_portions):
                    section_name, he_section_name, chapter = all_portions[portion_idx]

                    # Build the Sefaria reference
                    # Note: Adjust the chelek based on section type
                    chelek = determine_chelek(section_name)
                    ref = f"Likutei_Halakhot,_{chelek},_{section_name.replace(' ', '_')}.{chapter}.1"

                    portions.append(DailyPortion(
                        ref=ref,
                        he_ref=f"ליקוטי הלכות, {he_section_name} {chapter}",
                        section_name=section_name,
                        chapter=chapter,
                        subsection=1,
                    ))
                    portion_idx += 1

            schedule[key] = {
                "portions": [p.to_dict() for p in portions],
            }
            day_num += 1

    return schedule


def determine_chelek(section_name: str) -> str:
    """Determine which chelek (part) a section belongs to."""
    # Yoreh Deah sections
    yoreh_deah = [
        "Laws of Slaughtering", "Laws of Unfit Animals", "Laws of Priestly Gifts",
        "Laws of a Limb from a Live Animal", "Laws of Meat that was Unobserved",
        "Laws of Fat and Blood", "Laws of Blood", "Laws of Salting",
        "Laws of Domesticated and Undomesticated Animals", "Laws of Things that Come from a Live Animal",
        "Laws of Birds", "Laws of Fish", "Laws of Insects", "Laws of Eggs",
        "Laws of Meat and Milk", "Laws of Mixtures", "Laws of Non Jewish Food",
        "Laws of Kashering Vessels", "Laws of Taste Transfer", "Laws of Libational Wine",
        "Laws of Wine Vessels", "Laws of Idol Worship", "Laws of Interest",
        "Laws of Idolatrous Practices", "Laws of Sourcerers and Enchanters",
        "Laws of Shaving and Tatooing", "Laws of Shaving", "Laws of Forbidden Dresss",
        "Laws of a Menstruant", "Laws of Ritual Baths", "Laws of Vows", "Laws of Oaths",
        "Laws of Honouring One's Father and Mother", "Laws of Honouring One's Rabbi and a Torah Scholar",
        "Laws of Teachers", "Laws of Torah Study", "Laws of Charity", "Laws of Circumcision",
        "Laws of Slaves", "Laws of Converts", "Laws of a Torah Scroll", "Laws of a Mezuzah",
        "Laws of Sending Away the Mother Bird", "Laws of New Grain", "Laws of Three Year Old Trees",
        "Laws of Mixed Crops", "Laws of Mixed Breeding", "Laws of Fobidden Fabric Blends",
        "Laws of Redeeming the Firstborn", "Laws of Firstborn Kosher Animals",
        "Laws of Firstborn Donkey", "Laws of Separating From Dough", "Laws of Tithes",
        "Laws of First Shearings",
    ]

    # Even HaEzer sections
    even_haezer = [
        "Laws of Procreation", "Laws of Matrimony", "Laws of Sanctification",
        "Laws of a Bill of Marriage", "Laws of a Bill of Divorce", "Laws of Levirate Marriage",
        "Laws of Adulterer", "Laws of Rape and Seduction",
    ]

    # Choshen Mishpat sections
    choshen_mishpat = [
        "Laws for Judges", "Laws of Testimony", "Laws of Loans",
        "Laws of Plaintiffs and Defendants", "Laws of Collecting Loans",
        "Laws of Collecting Loans from Orphans",
        "Laws of Collecting Loans from Purchasers and Laws Designated Collection",
        "Laws of an Agent Collecting Debts and Authorisation", "Laws of Authorisation",
        "Laws of Guaranteeing", "Laws of Movable Property", "Laws of Immovable Property",
        "Laws of Neighbor Damages", "Laws of Immovable Partnerships",
        "Laws of Divisions of Partnerships", "Laws of Boundaries", "Laws of Partners",
        "Laws of Emissaries", "Laws of Buying and Selling", "Laws of Over and Under Charging",
        "Laws of Gifting", "Laws of a Deathly Ill Person", "Laws of Lost and Found",
        "Laws of Unloading and Loading", "Laws of Ownerless Property and Property of Non Jews",
        "Laws of Inheritance", "Laws of an Apotropos", "Laws of Deposit and Four Guards",
        "Laws for Paid Guardians", "Laws of Artisans", "Laws of Hiring",
        "Laws of Leasing and Contract Work", "Laws of Hiring Labourers", "Laws of Borrowing",
        "Laws of Theft", "Laws of Stealing", "Laws of Damages",
        "Laws of Causing a Loss and Reporting to Government", "Laws of Monetary Damages",
        "Laws of Injuring a Person", "Laws of Roof Rails and Preservation of Life",
    ]

    if section_name in yoreh_deah:
        return "Yoreh_Deah"
    elif section_name in even_haezer:
        return "Even_HaEzer"
    elif section_name in choshen_mishpat:
        return "Choshen_Mishpat"
    else:
        return "Orach_Chaim"


class ScheduleManager:
    """Manages the Likutei Halachot Yomi schedule."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.schedule_file = data_dir / "schedule.json"
        self._schedule: Optional[Dict] = None

    def load_schedule(self) -> Dict:
        """Load schedule from file or generate if not exists."""
        if self._schedule is not None:
            return self._schedule

        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    self._schedule = json.load(f)
                    logger.info(f"Loaded schedule from {self.schedule_file}")
                    return self._schedule
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading schedule: {e}")

        # Generate default schedule
        logger.info("Generating new schedule")
        self._schedule = self._generate_default_schedule()
        self.save_schedule()
        return self._schedule

    def save_schedule(self):
        """Save schedule to file."""
        if self._schedule is None:
            return

        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(self._schedule, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved schedule to {self.schedule_file}")

    def _generate_default_schedule(self) -> Dict:
        """Generate the default schedule structure."""
        schedule_data = generate_yearly_schedule(5786)

        return {
            "meta": {
                "description": "Likutei Halachot Yomi - Daily Learning Schedule",
                "source": "Based on sequential learning through Likutei Halachot",
                "sefaria_url": "https://www.sefaria.org/Likutei_Halakhot",
                "ashreinu_url": "https://www.breslevnews.net/אשרינו-לוח-דף-היומי-בליקוטי-הלכות-ל/",
                "generated_for_year": 5786,
            },
            "schedule": schedule_data,
        }

    def get_daily_portions(self, hebrew_date: HebrewDate) -> List[DailyPortion]:
        """Get the portions for a specific Hebrew date."""
        schedule = self.load_schedule()
        schedule_data = schedule.get("schedule", {})

        key = f"{hebrew_date.month_key}:{hebrew_date.day}"
        day_data = schedule_data.get(key, {})
        portions_data = day_data.get("portions", [])

        return [DailyPortion.from_dict(p) for p in portions_data]

    def update_portion(self, month_key: str, day: int, portions: List[DailyPortion]):
        """Update the portions for a specific day."""
        schedule = self.load_schedule()
        key = f"{month_key}:{day}"

        if "schedule" not in schedule:
            schedule["schedule"] = {}

        schedule["schedule"][key] = {
            "portions": [p.to_dict() for p in portions]
        }

        self._schedule = schedule
        self.save_schedule()
