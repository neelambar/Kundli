import datetime
import json
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

# Free geocoder, no API key needed. Returns lat/lon and IANA timezone per place.
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_places(query, count=8):
    """
    Looks up a birth place by name. Returns a list of
    {label, lat, lon, timezone} dicts, best match first.
    """
    params = urllib.parse.urlencode({"name": query, "count": count, "language": "en", "format": "json"})
    with urllib.request.urlopen(f"{GEOCODE_URL}?{params}", timeout=10) as resp:
        payload = json.load(resp)

    places = []
    for r in payload.get("results", []):
        parts = [r.get("name"), r.get("admin2"), r.get("admin1"), r.get("country")]
        label = ", ".join(dict.fromkeys(p for p in parts if p))  # drop blanks and repeats
        places.append({
            "label": label,
            "lat": r["latitude"],
            "lon": r["longitude"],
            "timezone": r.get("timezone") or "UTC",
        })
    return places


def utc_offset_hours(tz_name, year, month, day, hour, minute, second):
    """
    UTC offset (in hours) that was in effect at the given local birth time,
    so historical DST / zone changes are respected.
    """
    local = datetime.datetime(year, month, day, hour, minute, second, tzinfo=ZoneInfo(tz_name))
    return local.utcoffset().total_seconds() / 3600.0


def format_offset(hours):
    sign = "+" if hours >= 0 else "-"
    total_min = round(abs(hours) * 60)
    return f"{sign}{total_min // 60:02d}:{total_min % 60:02d}"
