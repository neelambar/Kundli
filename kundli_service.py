from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from CreateBirthChart import calculate_kundli, render_chart_fragment
from geo import format_offset, utc_offset_hours


def parse_birth_form(form):
    """Validates the submitted form. Returns a normalized record or raises ValueError."""
    rec = {k: (form.get(k) or "").strip() for k in ("name", "date", "time", "place", "lat", "lon", "timezone")}
    if not rec["name"]:
        raise ValueError("Please enter a name.")
    if not rec["place"]:
        raise ValueError("Please enter a birth place.")
    try:
        datetime.strptime(rec["date"], "%Y-%m-%d")
    except ValueError:
        raise ValueError("Please enter a valid date of birth.")
    if len(rec["time"]) == 5:
        rec["time"] += ":00"
    try:
        datetime.strptime(rec["time"], "%H:%M:%S")
    except ValueError:
        raise ValueError("Please enter a valid time of birth.")
    try:
        rec["lat"], rec["lon"] = float(rec["lat"]), float(rec["lon"])
    except ValueError:
        raise ValueError("Latitude/longitude missing — click Find next to the birth place and pick a match.")
    if not (-90 <= rec["lat"] <= 90 and -180 <= rec["lon"] <= 180):
        raise ValueError("Latitude must be within ±90 and longitude within ±180.")
    try:
        ZoneInfo(rec["timezone"])
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"Unknown timezone '{rec['timezone']}'. Use an IANA name like Asia/Kolkata.")
    return rec


def build_chart(rec):
    year, month, day = map(int, rec["date"].split("-"))
    hour, minute, second = map(int, rec["time"].split(":"))
    tz_offset = utc_offset_hours(rec["timezone"], year, month, day, hour, minute, second)
    data = calculate_kundli(year, month, day, hour, minute, second, rec["lat"], rec["lon"], tz_offset)
    data["birth_info"]["tz"] = format_offset(tz_offset)
    return render_chart_fragment(data, name=rec["name"], place=rec["place"])
