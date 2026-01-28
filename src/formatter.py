"""Message formatting for Telegram."""

import logging
from datetime import date

from .models import DailyPair, Halacha

logger = logging.getLogger(__name__)

# Maximum Telegram message length
MAX_MESSAGE_LENGTH = 4096

# Maximum text length per halacha to ensure message fits
MAX_HALACHA_TEXT_LENGTH = 1200


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max length, preserving word boundaries."""
    if len(text) <= max_length:
        return text

    # Find last space before max_length
    truncated = text[: max_length - len(suffix)]
    last_space = truncated.rfind(" ")

    if last_space > max_length // 2:
        truncated = truncated[:last_space]

    return truncated + suffix


def format_halacha(halacha: Halacha, number: int) -> str:
    """Format a single halacha for display."""
    # Header with volume and section
    header = f"<b>{'א' if number == 1 else 'ב'}. {halacha.section.section_he}</b>"
    subheader = f"<i>{halacha.section.volume_he}</i>"

    # Hebrew text (truncated if needed)
    hebrew = truncate_text(halacha.hebrew_text, MAX_HALACHA_TEXT_LENGTH)

    # English translation if available
    english_section = ""
    if halacha.english_text:
        english = truncate_text(halacha.english_text, MAX_HALACHA_TEXT_LENGTH // 2)
        english_section = f"\n\n<i>{english}</i>"

    # Sefaria link
    link = (
        f'<a href="{halacha.sefaria_url}">📖 Read more on Sefaria / קרא עוד בספריא</a>'
    )

    return f"""{header}
{subheader}

{hebrew}{english_section}

{link}"""


def format_daily_message(pair: DailyPair, for_date: date | None = None) -> str:
    """Format the complete daily message."""
    if for_date is None:
        for_date = date.today()

    # Date header
    date_str = for_date.strftime("%d/%m/%Y")

    # Opening
    opening = f"""<b>📚 ליקוטי הלכות יומי</b>
<i>{date_str}</i>

שתי הלכות אקראיות מליקוטי הלכות לרבי נתן מברסלב:

━━━━━━━━━━━━━━━"""

    # Format both halachot
    first = format_halacha(pair.first, 1)
    second = format_halacha(pair.second, 2)

    # Closing
    closing = """━━━━━━━━━━━━━━━

<i>נ נח נחמ נחמן מאומן</i>
🕯️ יהי רצון שנזכה ללמוד וללמד, לשמור ולעשות"""

    message = f"""{opening}

{first}

━━━━━━━━━━━━━━━

{second}

{closing}"""

    # Ensure message isn't too long
    if len(message) > MAX_MESSAGE_LENGTH:
        logger.warning(f"Message too long ({len(message)} chars), truncating")
        # Recalculate with shorter texts
        return format_daily_message_compact(pair, for_date)

    return message


def format_daily_message_compact(pair: DailyPair, for_date: date) -> str:
    """Format a more compact message when full version is too long."""
    date_str = for_date.strftime("%d/%m/%Y")

    # Shorter texts
    hebrew1 = truncate_text(pair.first.hebrew_text, 600)
    hebrew2 = truncate_text(pair.second.hebrew_text, 600)

    return f"""<b>📚 ליקוטי הלכות יומי</b> | {date_str}

<b>א. {pair.first.section.section_he}</b>
{hebrew1}
<a href="{pair.first.sefaria_url}">📖 ספריא</a>

<b>ב. {pair.second.section.section_he}</b>
{hebrew2}
<a href="{pair.second.sefaria_url}">📖 ספריא</a>

<i>נ נח נחמ נחמן מאומן</i>"""


def format_welcome_message() -> str:
    """Format the welcome message for new users."""
    return """<b>📚 Welcome to Likutei Halachot Yomi!</b>
<b>📚 ברוכים הבאים לליקוטי הלכות יומי!</b>

Every day, receive two random halachot from Likutei Halachot by Rebbe Natan of Breslov - the chief disciple of Rebbe Nachman of Uman.

כל יום תקבלו שתי הלכות אקראיות מליקוטי הלכות לרבי נתן מברסלב - תלמידו הגדול של רבי נחמן מאומן.

<b>What you'll receive / מה תקבלו:</b>
• Two halachot daily from different volumes
  שתי הלכות יומיות משני חלקים שונים
• Hebrew text with English translation (when available)
  טקסט בעברית עם תרגום לאנגלית (כשזמין)
• Direct Sefaria links for further study
  קישורים ישירים לספריא להמשך הלימוד

<b>Commands / פקודות:</b>
/today - Today's halachot / הלכות היום
/about - About this bot / אודות הבוט

<i>נ נח נחמ נחמן מאומן</i>
🕯️ Spreading the light of Rebbe Nachman"""


def format_about_message() -> str:
    """Format the about message."""
    return """<b>📖 About Likutei Halachot Yomi</b>
<b>📖 אודות ליקוטי הלכות יומי</b>

<b>Likutei Halachot</b> is a foundational work of Breslov Chassidut, written by Rebbe Natan of Breslov (1780-1844), the foremost disciple of Rebbe Nachman of Uman.

<b>ליקוטי הלכות</b> הוא ספר יסוד בחסידות ברסלב, שחובר על ידי רבי נתן מברסלב, תלמידו הגדול של רבי נחמן מאומן.

The work contains deep mystical insights on the Shulchan Aruch through the lens of Rebbe Nachman's teachings.

<b>The Four Sections / ארבעת החלקים:</b>
• <b>Orach Chaim</b> / אורח חיים - Daily conduct
• <b>Yoreh Deah</b> / יורה דעה - Dietary laws
• <b>Even HaEzer</b> / אבן העזר - Family law
• <b>Choshen Mishpat</b> / חושן משפט - Civil law

<b>Source / מקור:</b>
All texts from <a href="https://www.sefaria.org/Likutei_Halakhot">Sefaria</a> - a free digital library of Jewish texts.

<b>Open Source / קוד פתוח:</b>
<a href="https://github.com/naorbrown/likutei-halachot-yomi">GitHub</a>

<i>נ נח נחמ נחמן מאומן</i>"""


def format_error_message() -> str:
    """Format an error message."""
    return """<b>😔 Error / שגיאה</b>

Sorry, an error occurred while fetching the halachot.
Please try again later.

מצטערים, אירעה שגיאה בעת שליפת ההלכות.
אנא נסו שוב מאוחר יותר.

<i>נ נח נחמ נחמן מאומן</i>"""
