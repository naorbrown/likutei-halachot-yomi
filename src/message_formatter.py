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
            if sefaria_text and sefaria_text.hebrew_text:
                hebrew_text = self._escape_html(sefaria_text.hebrew_combined)
                he_ref = self._escape_html(sefaria_text.he_ref or portion.he_ref)

                # Truncate if needed (leave room for rest of message)
                max_portion_len = self.max_length - len(header) - 500
                if len(hebrew_text) > max_portion_len:
                    hebrew_text = hebrew_text[:max_portion_len] + "..."

                portion_text = f"""
<b>{i}. {he_ref}</b>

{hebrew_text}

<a href="{sefaria_text.sefaria_url}">📚 קרא עוד בספריא</a>

{self.PORTION_SEPARATOR}
"""
            else:
                he_ref = self._escape_html(portion.he_ref or portion.ref)
                portion_text = f"""
<b>{i}. {he_ref}</b>

⚠️ לא ניתן לטעון את הטקסט מספריא

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

<i>מקור: <a href="https://www.sefaria.org/Likutei_Halakhot">ספריא - ליקוטי הלכות</a></i>
"""
        if self.include_footer:
            if len(current_text) + len(footer) <= self.max_length:
                current_text += footer

        messages.append(FormattedMessage(text=current_text.strip()))

        return messages

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
