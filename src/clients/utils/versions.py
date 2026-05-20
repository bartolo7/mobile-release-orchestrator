from datetime import datetime, timedelta
"""
Versioning strategy for mobile applications.

Version format:
    {major}.{YY}{WW}{R}.{patch}

Example:
    4.26031.0

Breakdown:
    4       -> Platform major version
               iOS = 4
               Android = 5

    26      -> Last two digits of the ISO year (2026)

    03      -> ISO week number

    1       -> Day index within the week
               1 = Monday 
               2 = Tuesday 
               ...
               7 = Sunday 

    0       -> Patch version reserved for hotfixes

Purpose:
    This versioning format guarantees unique versions for multiple
    scheduled releases within the same week while keeping the patch
    version available exclusively for hotfix releases.

Examples:
    Monday release:
        4.26031.0

    Thursday release:
        4.26034.0

    Thursday hotfix:
        4.26034.1
"""

def create_app_version(platform: str) -> dict:
    ct = datetime.now()
    iso_year, week_number, _ = ct.isocalendar()
    year = iso_year
    week = week_number

    major = 5 if platform.lower() == "android" else 4
    patch = 0


    # Handle year rollover (simplified but correct enough for ISO weeks)
    max_weeks = datetime(year, 12, 28).isocalendar()[1]

    if week > max_weeks:
        week = 1
        year += 1

    week_padding = f"{week:02}"

    # Date of the week number
    day_index = ct.isoweekday()

    version = f"{major}.{str(year)[-2:]}{week_padding}{day_index}.{patch}"

    # Monday of current ISO week
    week_start = datetime.strptime(f"{year}-{week}-1", "%G-%V-%u")
    start_date = week_start + timedelta(days=3)   # Thursday
    release_date = week_start + timedelta(days=7) # Next Monday

    return {
        "ver": version,
        "start_date": start_date,
        "release_date": release_date,
    }