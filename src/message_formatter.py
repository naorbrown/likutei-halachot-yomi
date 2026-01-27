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

    def __init__(self, max_length: int = 4096, include_footer: bool = True):
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
        all_messages = []

        for i, (portion, sefaria_text) in enumerate(zip(portions, sefaria_texts), 1):
            he_ref = self._escape_html(portion.he_ref or portion.ref)
            description = self._escape_html(portion.description) if portion.description else ""

            if sefaria_text and sefaria_text.hebrew_text:
                # We have Sefaria text - include it
                hebrew_text = self._escape_html(sefaria_text.hebrew_combined)
                sefaria_url = sefaria_text.sefaria_url

                # Build the message content
                content = f"""
<b>📚 {he_ref}</b>
{description}

{hebrew_text}

<a href="{sefaria_url}">📖 קרא בספריא</a>
"""
            else:
                # No Sefaria text available
                content = f"""
<b>📚 {he_ref}</b>
{description}

⚠️ הטקסט לא זמין כרגע. נסה שוב מאוחר יותר.
"""

            # Add footer
            footer = """
<i>לוח: אשרינו - קהילת ברסלב העולמית
נ נח נחמ נחמן מאומן 🙏</i>
"""

            # Combine header + content + footer
            full_message = header + content
            if self.include_footer:
                full_message += footer

            # If message is too long, split the Hebrew text across multiple messages
            if len(full_message) > self.max_length:
                # Split into multiple messages
                messages = self._split_long_message(header, he_ref, description, hebrew_text, sefaria_url, footer)
                all_messages.extend(messages)
            else:
                all_messages.append(FormattedMessage(text=full_message.strip()))

        return all_messages if all_messages else [FormattedMessage(text=header + "\nאין תוכן להיום")]

    def _split_long_message(
        self,
        header: str,
        he_ref: str,
        description: str,
        hebrew_text: str,
        sefaria_url: str,
        footer: str
    ) -> List[FormattedMessage]:
        """Split a long message into multiple parts."""
        messages = []

        # Calculate how much space we have for text in each message
        overhead = len(header) + len(he_ref) + len(description) + len(footer) + 200  # 200 for HTML tags
        max_text_per_message = self.max_length - overhead

        # Split the Hebrew text
        text_parts = []
        remaining = hebrew_text
        while remaining:
            if len(remaining) <= max_text_per_message:
                text_parts.append(remaining)
                break
            else:
                # Find a good break point (end of paragraph)
                break_point = remaining.rfind('\n\n', 0, max_text_per_message)
                if break_point == -1:
                    break_point = remaining.rfind('\n', 0, max_text_per_message)
                if break_point == -1:
                    break_point = max_text_per_message

                text_parts.append(remaining[:break_point])
                remaining = remaining[break_point:].lstrip()

        # Create messages
        total_parts = len(text_parts)
        for idx, text_part in enumerate(text_parts, 1):
            part_label = f" (חלק {idx}/{total_parts})" if total_parts > 1 else ""

            if idx == 1:
                # First message includes header
                msg = f"""{header}
<b>📚 {he_ref}</b>{part_label}
{description}

{text_part}
"""
            else:
                # Continuation messages
                msg = f"""<b>📚 {he_ref}</b>{part_label}

{text_part}
"""

            # Add link and footer to last message
            if idx == total_parts:
                msg += f"""
<a href="{sefaria_url}">📖 קרא בספריא</a>
{footer}
"""

            messages.append(FormattedMessage(text=msg.strip()))

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
