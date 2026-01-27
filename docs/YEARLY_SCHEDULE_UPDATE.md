# Yearly Schedule Update Guide

This document outlines the process for updating the Likutei Halachot Yomi schedule for each new Hebrew year. Follow this guide precisely to ensure accuracy.

## Overview

The Likutei Halachot Yomi follows the Ashreinu calendar, a 4-year cycle through the complete Likutei Halachot. Each year, a new schedule PDF is published by Ashreinu/Breslov.

**Current Year:** 5786 (Cycle 5/מחזור ה׳)

## When to Update

Update the schedule approximately **2-4 weeks before Rosh Hashanah** each year, once the new Ashreinu calendar is published.

## Step-by-Step Process

### 1. Obtain the New Schedule PDF

**Source:** [Breslov News - Ashreinu Calendar](https://www.breslevnews.net/אשרינו-לוח-דף-היומי-בליקוטי-הלכות-ל/)

1. Visit the Breslov News website
2. Download the current year's Likutei Halachot Yomi calendar PDF
3. Save to project root as `likutei_halachot_YEAR.pdf` (e.g., `likutei_halachot_5787.pdf`)

### 2. Extract Schedule Data

Create a new JSON file: `data/ashreinu_schedule_YEAR.json`

**JSON Structure:**
```json
{
  "meta": {
    "description": "Ashreinu Likutei Halachot Yomi Schedule for YEAR",
    "source": "Ashreinu/Breslov PDF Calendar from breslevnews.net",
    "cycle": N,
    "note": "Cycle N starts on [date] with [volume]",
    "sefaria_base_url": "https://www.sefaria.org/Likutei_Halakhot"
  },
  "schedule": {
    "month:day": {
      "daf": PAGE_NUMBER,
      "volume": "VOLUME_NAME",
      "part": PART_NUMBER,
      "parsha": "PARSHA_NAME"
    }
  }
}
```

**Volume Names (use exactly):**
- `Orach_Chaim` - אורח חיים
- `Yoreh_Deah` - יורה דעה
- `Even_HaEzer` - אבן העזר
- `Choshen_Mishpat` - חושן משפט

**Month Keys (use exactly):**
- `tishrei`, `cheshvan`, `kislev`, `tevet`, `shevat`
- `adar` (or `adar_i` and `adar_ii` in leap years)
- `nisan`, `iyar`, `sivan`, `tammuz`, `av`, `elul`

**Special Values:**
- For introduction/hakdama: `"daf": "hakdama"`
- Add `"note": "..."` for special transitions (cycle starts, volume changes)

### 3. PDF Extraction Tips

1. **Hebrew Numbers (Gematria):**
   - א=1, ב=2, ג=3, ד=4, ה=5, ו=6, ז=7, ח=8, ט=9
   - י=10, כ=20, ל=30, מ=40, נ=50, ס=60, ע=70, פ=80, צ=90
   - ק=100, ר=200, ש=300, ת=400
   - Example: רטו = 200+9+6 = 215

2. **PDF Structure:**
   - Schedule is organized by weekly Torah portion (Parsha)
   - Each parsha shows 7 days (Sunday-Shabbat)
   - High Holidays may have special entries

3. **Key Transitions to Watch:**
   - Cycle start date (when Orach Chaim Part 1 begins)
   - Volume transitions (Part 1 → Part 2, or changing volumes)
   - Leap year Adar handling

### 4. Update Schedule Manager

Edit `src/schedule.py`:

```python
# Update the filename in ScheduleManager.__init__
self.ashreinu_schedule_file = data_dir / "ashreinu_schedule_YEAR.json"
```

### 5. Quality Assurance Checklist

Run these checks before deploying:

- [ ] **Entry Count:** Verify ~365 entries (or ~385 for leap year)
- [ ] **Month Coverage:** All 12 months (13 in leap year) present
- [ ] **Day Coverage:** Check each month has correct number of days
- [ ] **Daf Continuity:** Page numbers should be sequential within each volume
- [ ] **Volume Transitions:** Verify cycle start and any volume changes
- [ ] **Parsha Accuracy:** Spot-check parsha names against Hebrew calendar
- [ ] **Special Days:** High Holidays, Sukkot period handled correctly

**Test Script:**
```bash
python3 -c "
from src.schedule import ScheduleManager
from pathlib import Path
import json

manager = ScheduleManager(Path('data'))
schedule = manager.load_schedule()
entries = schedule['schedule']

print(f'Total entries: {len(entries)}')
print(f'Cycle: {schedule[\"meta\"][\"cycle\"]}')

# Check months
months = set(k.split(':')[0] for k in entries.keys())
print(f'Months: {sorted(months)}')

# Check a few dates
test_dates = ['tishrei:1', 'shevat:15', 'nisan:15']
for date in test_dates:
    if date in entries:
        print(f'{date}: daf {entries[date][\"daf\"]} ({entries[date][\"volume\"]})')
"
```

### 6. Update Bot Description

If the cycle number changes, update `scripts/update_bot_profile.py`:

```python
BOT_DESCRIPTION = '''...לוח שנה מדויק לשנת תשפ״ז (מחזור ו׳)...'''
```

Then run:
```bash
python scripts/update_bot_profile.py
```

### 7. Commit and Deploy

```bash
# Stage changes
git add data/ashreinu_schedule_YEAR.json
git add src/schedule.py
git add scripts/update_bot_profile.py

# Commit
git commit -m "Update schedule for Hebrew year YEAR (Cycle N)"

# Push
git push origin main
```

## Yearly Schedule File Archive

| Year | Cycle | Start Date | Notes |
|------|-------|------------|-------|
| 5786 | 5 | 3 Shevat (Bo) | OC Part 1 starts mid-year |
| 5787 | 6 | TBD | Update when available |

## Troubleshooting

### Common Issues

1. **Missing entries:** Check for typos in month keys
2. **Wrong daf numbers:** Verify gematria conversion
3. **Sefaria API errors:** Check reference format matches Sefaria exactly
4. **Bot not updating:** Verify GitHub Actions workflow ran

### Contact

For questions about the Ashreinu schedule: [Breslov News](https://www.breslevnews.net)

---

*Last Updated: January 2026*
*Maintainer: @naorbrown*
