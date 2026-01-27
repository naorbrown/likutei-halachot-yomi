"""
Message formatting for Telegram messages.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from .hebrew_calendar import HebrewDate
from .schedule import DailyPortion
from .sefaria_client import SefariaText

logger = logging.getLogger(__name__)

# HebrewBooks book IDs for Likutei Halachot volumes
# These create direct links to specific pages in the PDF scans
HEBREWBOOKS_IDS = {
    ("Orach_Chaim", 1): 14144,   # OC Part 1
    ("Orach_Chaim", 2): 14145,   # OC Part 2
    ("Yoreh_Deah", 1): 14146,    # YD Part 1
    ("Yoreh_Deah", 2): 14147,    # YD Part 2
    ("Even_HaEzer", 1): 14148,   # EH
    ("Choshen_Mishpat", 1): 14149,  # CM Part 1
    ("Choshen_Mishpat", 2): 14150,  # CM Part 2
}

def get_hebrewbooks_page_link(volume: str, part: int, daf: int) -> str:
    """
    Generate a HebrewBooks link to the specific page.

    HebrewBooks URLs support direct page links:
    https://hebrewbooks.org/pdfpager.aspx?req=BOOK_ID&pgnum=PAGE_NUM

    Note: The page number in the PDF may differ from the daf number
    due to title pages, introductions, etc. We add an offset.
    """
    book_id = HEBREWBOOKS_IDS.get((volume, part), 14144)
    # Add offset for front matter (typically ~10-15 pages)
    # This is approximate - exact mapping would need per-volume calibration
    page_offset = 10
    pdf_page = daf + page_offset
    return f"https://hebrewbooks.org/pdfpager.aspx?req={book_id}&pgnum={pdf_page}"

# Hebrew volume names for display
VOLUME_HEBREW = {
    "Orach_Chaim": "אורח חיים",
    "Yoreh_Deah": "יורה דעה",
    "Even_HaEzer": "אבן העזר",
    "Choshen_Mishpat": "חושן משפט",
}


@dataclass
class FormattedMessage:
    """A formatted message ready for sending."""
    text: str
    parse_mode: str = "HTML"

    def __len__(self) -> int:
        return len(self.text)


class MessageFormatter:
    """Formats daily Likutei Halachot messages for Telegram using HTML."""

    SEPARATOR_LINE = "═" * 30
    PORTION_SEPARATOR = "─" * 20

    def __init__(self, max_length: int = 4000, include_footer: bool = True):
        self.max_length = max_length
        self.include_footer = include_footer

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;'))

    def format_daily_message(
        self,
        hebrew_date: HebrewDate,
        portions: List[DailyPortion],
        sefaria_texts: List[Optional[SefariaText]],
    ) -> List[FormattedMessage]:
        """
        Format the daily message with all portions.

        Args:
            hebrew_date: Today's Hebrew date
            portions: List of daily portions
            sefaria_texts: Corresponding Sefaria texts (None if fetch failed)

        Returns:
            List of FormattedMessage objects (split if too long)
        """
        # Build header
        header = f"""📖 <b>ליקוטי הלכות יומי</b>
📅 {self._escape_html(hebrew_date.full_date_hebrew)}

{self.SEPARATOR_LINE}
"""

        # Handle no portions
        if not portions:
            text = header + """
⚠️ <b>לא נמצאו הלכות להיום</b>

בדוק את קובץ schedule.json או צור קשר עם מנהל הבוט.
"""
            return [FormattedMessage(text=text)]

        # Build portion sections
        portion_texts = []
        for i, (portion, sefaria_text) in enumerate(zip(portions, sefaria_texts), 1):
            he_ref = self._escape_html(portion.he_ref or portion.ref)
            description = self._escape_html(portion.description) if portion.description else ""

            # Extract volume, part, and daf for HebrewBooks link
            volume_part = self._parse_volume_part(portion.section_name)
            daf_num = portion.chapter if portion.chapter > 0 else 1

            # Generate direct page link to HebrewBooks
            hebrewbooks_link = get_hebrewbooks_page_link(volume_part[0], volume_part[1], daf_num)

            if sefaria_text and sefaria_text.hebrew_text:
                # We have Sefaria text - include it
                hebrew_text = self._escape_html(sefaria_text.hebrew_combined)

                # Truncate if needed (leave room for rest of message)
                max_portion_len = self.max_length - len(header) - 500
                if len(hebrew_text) > max_portion_len:
                    hebrew_text = hebrew_text[:max_portion_len] + "..."

                portion_text = f"""
<b>📚 {he_ref}</b>
{description}

{hebrew_text}

<a href="{sefaria_text.sefaria_url}">📖 קרא בספריא</a> | <a href="{hebrewbooks_link}">📜 HebrewBooks דף {daf_num}</a>

{self.PORTION_SEPARATOR}
"""
            else:
                # No Sefaria text - provide HebrewBooks link with page number
                portion_text = f"""
<b>📚 {he_ref}</b>
{description}

👆 לחץ על הקישור למטה לקריאת הדף המלא:

<a href="{hebrewbooks_link}">📜 לימוד דף {daf_num} ב-HebrewBooks</a>

{self.PORTION_SEPARATOR}
"""

            portion_texts.append(portion_text)

        # Combine and split if needed
        messages = []
        current_text = header

        for portion_text in portion_texts:
            if len(current_text) + len(portion_text) > self.max_length:
                # Start a new message
                messages.append(FormattedMessage(text=current_text.strip()))
                current_text = portion_text
            else:
                current_text += portion_text

        # Add footer to last message
        footer = """

<i>לוח: אשרינו - קהילת ברסלב העולמית
נ נח נחמ נחמן מאומן 🙏</i>
"""
        if self.include_footer:
            if len(current_text) + len(footer) <= self.max_length:
                current_text += footer

        messages.append(FormattedMessage(text=current_text.strip()))

        return messages

    def _parse_volume_part(self, section_name: str) -> tuple:
        """Parse volume and part from section name like 'Choshen Mishpat Part 2'."""
        if not section_name:
            return ("Orach_Chaim", 1)

        # Try to extract volume and part
        section_lower = section_name.lower()
        part = 1
        if "part 2" in section_lower:
            part = 2

        if "orach" in section_lower or "chaim" in section_lower:
            return ("Orach_Chaim", part)
        elif "yoreh" in section_lower or "deah" in section_lower:
            return ("Yoreh_Deah", part)
        elif "even" in section_lower or "ezer" in section_lower:
            return ("Even_HaEzer", 1)
        elif "choshen" in section_lower or "mishpat" in section_lower:
            return ("Choshen_Mishpat", part)

        return ("Orach_Chaim", 1)

    def format_test_message(self, hebrew_date: HebrewDate, portions: List[DailyPortion]) -> str:
        """
        Format a simple test message showing what will be sent.

        Args:
            hebrew_date: Today's Hebrew date
            portions: List of daily portions

        Returns:
            Plain text preview
        """
        lines = [
            f"Hebrew Date: {hebrew_date.full_date_hebrew}",
            f"Month Key: {hebrew_date.month_key}",
            f"Day: {hebrew_date.day}",
            "",
            f"Portions ({len(portions)}):",
        ]

        for i, portion in enumerate(portions, 1):
            lines.append(f"  {i}. {portion.he_ref}")
            lines.append(f"     Ref: {portion.ref}")
            lines.append("")

        return "\n".join(lines)
