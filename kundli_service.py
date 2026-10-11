import urllib.parse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from CreateBirthChart import calculate_kundli, render_chart_fragment
from geo import format_offset, utc_offset_hours

# Form/query fields for the transit chart's current place. Not stored with the kundli.
CURRENT_FIELDS = ("cur_place", "cur_lat", "cur_lon", "cur_timezone")


def _validate_location(rec, what):
    """Converts lat/lon to floats and checks the timezone. `what` names the place in error messages."""
    try:
        rec["lat"], rec["lon"] = float(rec["lat"]), float(rec["lon"])
    except ValueError:
        raise ValueError(f"Latitude/longitude missing — click Find next to the {what} and pick a match.")
    if not (-90 <= rec["lat"] <= 90 and -180 <= rec["lon"] <= 180):
        raise ValueError("Latitude must be within ±90 and longitude within ±180.")
    try:
        ZoneInfo(rec["timezone"])
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f"Unknown timezone '{rec['timezone']}'. Use an IANA name like Asia/Kolkata.")


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
    _validate_location(rec, "birth place")
    return rec


def current_place_fields(params):
    """The raw cur_* values from a form or query string, for refilling the form. Empty if no current place."""
    fields = {k: (params.get(k) or "").strip() for k in CURRENT_FIELDS}
    return fields if fields["cur_place"] else {}


def current_place_query(params):
    """'&cur_place=...' suffix that carries the current place across a redirect."""
    fields = current_place_fields(params)
    return "&" + urllib.parse.urlencode(fields) if fields else ""


def parse_current_place(params):
    """Validated current place ({place, lat, lon, timezone}), or None if it was left blank."""
    fields = current_place_fields(params)
    if not fields:
        return None
    loc = {k[len("cur_"):]: v for k, v in fields.items()}
    _validate_location(loc, "current place")
    return loc


def build_chart(rec):
    year, month, day = map(int, rec["date"].split("-"))
    hour, minute, second = map(int, rec["time"].split(":"))
    tz_offset = utc_offset_hours(rec["timezone"], year, month, day, hour, minute, second)
    data = calculate_kundli(year, month, day, hour, minute, second, rec["lat"], rec["lon"], tz_offset)
    data["birth_info"]["tz"] = format_offset(tz_offset)
    return render_chart_fragment(data, name=rec["name"], place=rec["place"])


def build_transit_chart(loc, now=None):
    """
    Transit (gochar) chart: planet positions at `now` (default: this moment), with the
    lagna rising at `loc` ({place, lat, lon, timezone}).
    """
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(loc["timezone"]))
    tz_offset = local.utcoffset().total_seconds() / 3600.0
    data = calculate_kundli(local.year, local.month, local.day, local.hour, local.minute, local.second,
                            loc["lat"], loc["lon"], tz_offset)
    data["birth_info"]["tz"] = format_offset(tz_offset)
    return render_chart_fragment(data, place=loc["place"], title="गोचर कुंडली (Transit Chart)")


def build_transit_for(rec, params):
    """Transit chart for the current place in `params`, falling back to the birth place. May raise ValueError."""
    return build_transit_chart(parse_current_place(params) or rec)
