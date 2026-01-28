"""Message formatting for Telegram."""

import logging
from datetime import date

from .models import DailyPair, Halacha

logger = logging.getLogger(__name__)

# Maximum Telegram message length
MAX_MESSAGE_LENGTH = 4096


def format_halacha(halacha: Halacha, number: int) -> str:
    """Format a single halacha with hyperlinked title and full text."""
    # Full title hyperlinked to Sefaria
    label = "א" if number == 1 else "ב"
    title = f'<a href="{halacha.sefaria_url}"><b>{label}. הלכות {halacha.section.section_he}</b></a>'
    volume = f"<i>{halacha.section.volume_he}</i>"

    # Full Hebrew text
    hebrew = halacha.hebrew_text

    # English if available
    english_part = ""
    if halacha.english_text:
        english_part = f"\n\n<i>{halacha.english_text}</i>"

    # Link at bottom
    link = f'<a href="{halacha.sefaria_url}">📖 קרא עוד בספריא / Read more on Sefaria</a>'

    return f"""{title}
{volume}

{hebrew}{english_part}

{link}"""


def format_daily_message(pair: DailyPair, for_date: date | None = None) -> list[str]:
    """Format daily message. Returns list of messages (split if too long)."""
    if for_date is None:
        for_date = date.today()

    date_str = for_date.strftime("%d/%m/%Y")
    first = format_halacha(pair.first, 1)
    second = format_halacha(pair.second, 2)

    # Try single message first
    single = f"""<b>📚 ליקוטי הלכות יומי</b> | {date_str}

{first}

━━━━━━━━━━━━━━━

{second}

<i>נ נח נחמ נחמן מאומן</i>"""

    if len(single) <= MAX_MESSAGE_LENGTH:
        return [single]

    # Split into two messages
    msg1 = f"""<b>📚 ליקוטי הלכות יומי</b> | {date_str}

{first}"""

    msg2 = f"""{second}

<i>נ נח נחמ נחמן מאומן</i>"""

    return [msg1, msg2]


def format_welcome_message() -> str:
    """Format the welcome message."""
    return """<b>📚 ברוכים הבאים לליקוטי הלכות יומי!</b>

כל יום תקבלו שתי הלכות מליקוטי הלכות לרבי נתן מברסלב.

<b>פקודות:</b>
/today - הלכות היום
/about - אודות הבוט

<i>נ נח נחמ נחמן מאומן</i>"""


def format_about_message() -> str:
    """Format the about message."""
    return """<b>📖 אודות ליקוטי הלכות יומי</b>

<b>ליקוטי הלכות</b> - ספר יסוד בחסידות ברסלב מאת רבי נתן מברסלב.

<b>ארבעת החלקים:</b>
• אורח חיים
• יורה דעה
• אבן העזר
• חושן משפט

<a href="https://www.sefaria.org/Likutei_Halakhot">ספריא</a> | <a href="https://github.com/naorbrown/likutei-halachot-yomi">GitHub</a>

<i>נ נח נחמ נחמן מאומן</i>"""


def format_error_message() -> str:
    """Format an error message."""
    return """<b>😔 שגיאה</b>

אירעה שגיאה. אנא נסו שוב.

<i>נ נח נחמ נחמן מאומן</i>"""
