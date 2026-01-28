"""Message formatting for Telegram."""

from datetime import date

from .models import DailyPair, Halacha

MAX_MESSAGE_LENGTH = 4000


def split_text(text: str, max_len: int) -> list[str]:
    """Split text into chunks at word boundaries."""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind(" ", 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    return chunks


def format_halacha_messages(
    halacha: Halacha, number: int, date_str: str = ""
) -> list[str]:
    """Format a halacha into messages."""
    label = "א" if number == 1 else "ב"
    emoji = "📜" if number == 1 else "📖"
    title = f'{emoji} <a href="{halacha.sefaria_url}"><b>{label}. {halacha.section.section_he}</b></a>'
    volume = f"<i>{halacha.section.volume_he}</i>"
    link = f'<a href="{halacha.sefaria_url}">המשך בספריא →</a>'

    header = f"<b>📚 ליקוטי הלכות יומי</b> | {date_str}\n\n" if date_str else ""
    base = f"{header}{title}\n{volume}\n\n"
    footer = f"\n\n{link}"

    available = MAX_MESSAGE_LENGTH - len(base) - len(footer) - 100
    hebrew_chunks = split_text(halacha.hebrew_text, available)

    messages = []
    for i, chunk in enumerate(hebrew_chunks):
        msg = f"{base}{chunk}" if i == 0 else f"{title} (המשך)\n\n{chunk}"
        if i == len(hebrew_chunks) - 1:
            msg += footer
        messages.append(msg)

    return messages


def format_daily_message(pair: DailyPair, for_date: date | None = None) -> list[str]:
    """Format daily message as list of messages."""
    if for_date is None:
        for_date = date.today()
    date_str = for_date.strftime("%d/%m/%Y")

    messages = []
    messages.extend(format_halacha_messages(pair.first, 1, date_str))
    messages.extend(format_halacha_messages(pair.second, 2, ""))
    messages[-1] += "\n\n<i>נ נח נחמ נחמן מאומן</i>"
    return messages


def format_welcome_message() -> str:
    return """<b>📚 ברוכים הבאים לליקוטי הלכות יומי!</b>

שתי הלכות יומיות מספר ליקוטי הלכות של רבי נתן מברסלב.

<b>פקודות:</b>
/today - 📖 הלכות היום
/about - ℹ️ אודות
/help - ❓ עזרה

<i>נ נח נחמ נחמן מאומן</i>"""


def format_about_message() -> str:
    return """<b>ℹ️ אודות ליקוטי הלכות יומי</b>

<b>ליקוטי הלכות</b> - ספר יסוד בחסידות ברסלב מאת רבי נתן מברסלב, תלמידו הגדול של רבי נחמן מאומן.

הספר מכיל ביאורים עמוקים על השולחן ערוך לפי תורת רבי נחמן.

<b>קישורים:</b>
📚 <a href="https://www.sefaria.org/Likutei_Halakhot">ספריא</a>
💻 <a href="https://github.com/naorbrown/likutei-halachot-yomi">קוד פתוח</a>

<i>נ נח נחמ נחמן מאומן</i>"""


def format_help_message() -> str:
    return """<b>❓ עזרה</b>

<b>פקודות זמינות:</b>

/start - התחלה והרשמה
/today - קבלת הלכות היום
/about - מידע על הבוט
/help - הודעה זו

<b>איך זה עובד?</b>
כל יום מתפרסמות שתי הלכות חדשות משני חלקים שונים של ליקוטי הלכות.

<b>שאלות?</b>
פנו אלינו ב-<a href="https://github.com/naorbrown/likutei-halachot-yomi/issues">GitHub</a>

<i>נ נח נחמ נחמן מאומן</i>"""


def format_error_message() -> str:
    return """<b>😔 שגיאה</b>

אירעה שגיאה. אנא נסו שוב מאוחר יותר.

<i>נ נח נחמ נחמן מאומן</i>"""
