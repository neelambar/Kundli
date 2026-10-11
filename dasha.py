import datetime
import swisseph as swe

# ==========================================
# VIMSHOTTARI DASHA CONSTANTS
# ==========================================

# 27 Nakshatras with their ruling planets
NAKSHATRAS = [
    ("Ashwini", "Ketu"), ("Bharani", "Venus"), ("Krittika", "Sun"),
    ("Rohini", "Moon"), ("Mrigashira", "Mars"), ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"), ("Pushya", "Saturn"), ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"), ("Purva Phalguni", "Venus"), ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"), ("Chitra", "Mars"), ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"), ("Anuradha", "Saturn"), ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"), ("Purva Ashadha", "Venus"), ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"), ("Dhanishta", "Mars"), ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"), ("Uttara Bhadrapada", "Saturn"), ("Revati", "Mercury")
]

# Total years assigned to each planet in the 120-year cycle
DASHA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17
}

# The sequence of planets in Vimshottari cycle
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

PLANET_NAMES_HI = {
    "Ketu": "केतु", "Venus": "शुक्र", "Sun": "सूर्य", "Moon": "चन्द्र",
    "Mars": "मंगल", "Rahu": "राहू", "Jupiter": "गुरु", "Saturn": "शनि", "Mercury": "बुध"
}


def calculate_vimshottari_dasha(year, month, day, hour, minute, second, tz_offset):
    """
    Calculates Moon Nakshatra, Pada, Dasha Balance at birth, and Mahadasha Timeline.
    """
    # 1. Convert local birth time to UTC Julian Day
    local_decimal_hours = hour + (minute / 60.0) + (second / 3600.0)
    utc_decimal_hours = local_decimal_hours - tz_offset
    jd = swe.julday(year, month, day, utc_decimal_hours)

    # 2. Set Sidereal Lahiri Ayanamsa
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # 3. Get Sidereal position of Moon
    moon_res, _ = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
    moon_long = moon_res[0]  # 0° to 360°

    # 4. Nakshatra Calculations
    # Each Nakshatra = 13° 20' = 13.3333333°
    nak_span = 360.0 / 27.0
    nak_index = int(moon_long // nak_span)
    nak_name, ruler = NAKSHATRAS[nak_index]

    # Degree traversed inside current Nakshatra
    deg_in_nak = moon_long % nak_span
    
    # Pada calculation (4 Padas per Nakshatra, 3° 20' each)
    pada = int(deg_in_nak // (nak_span / 4.0)) + 1

    # 5. Dasha Balance Calculation
    # Fraction of Nakshatra remaining = fraction of total dasha period remaining
    fraction_remaining = (nak_span - deg_in_nak) / nak_span
    total_dasha_years = DASHA_YEARS[ruler]
    
    balance_years_decimal = total_dasha_years * fraction_remaining
    b_years = int(balance_years_decimal)
    b_months = int((balance_years_decimal - b_years) * 12)
    b_days = int((((balance_years_decimal - b_years) * 12) - b_months) * 30.4375)

    # 6. Generate Timeline of Mahadashas
    birth_date = datetime.date(year, month, day)
    
    # Start date calculation using balance duration
    # Approximate balance end date
    balance_days_total = int(balance_years_decimal * 365.25)
    first_dasha_end_date = birth_date + datetime.timedelta(days=balance_days_total)

    timeline = []
    
    # First Dasha (Balance at birth)
    timeline.append({
        "planet": ruler,
        "planet_hi": PLANET_NAMES_HI[ruler],
        "start_date": birth_date.strftime("%d-%m-%Y"),
        "end_date": first_dasha_end_date.strftime("%d-%m-%Y"),
        "is_balance": True,
        "duration": f"{b_years}Y {b_months}M {b_days}D"
    })

    # Remaining Dashas in sequence
    current_start_date = first_dasha_end_date
    start_idx = (DASHA_ORDER.index(ruler) + 1) % 9

    for i in range(8):
        curr_planet = DASHA_ORDER[(start_idx + i) % 9]
        d_years = DASHA_YEARS[curr_planet]
        
        # Calculate end date
        curr_end_date = datetime.date(
            current_start_date.year + d_years,
            current_start_date.month,
            current_start_date.day
        )
        
        timeline.append({
            "planet": curr_planet,
            "planet_hi": PLANET_NAMES_HI[curr_planet],
            "start_date": current_start_date.strftime("%d-%m-%Y"),
            "end_date": curr_end_date.strftime("%d-%m-%Y"),
            "is_balance": False,
            "duration": f"{d_years} Years"
        })
        current_start_date = curr_end_date

    swe.close()

    return {
        "moon_longitude": f"{moon_long:.4f}°",
        "nakshatra": nak_name,
        "pada": pada,
        "first_dasha_ruler": ruler,
        "balance_str": f"{b_years} वर्ष, {b_months} माह, {b_days} दिन",
        "timeline": timeline
    }


# ==========================================
# EXECUTION FOR GARHAKOTA CHART (24.02.1984 12:00 IST)
# ==========================================
if __name__ == "__main__":
    dasha_data = calculate_vimshottari_dasha(
        year=1984, month=2, day=25,
        hour=00, minute=30, second=0,
        tz_offset=5.5
    )

    print("--- Vimshottari Dasha Details ---")
    print(f"Moon Sidereal Longitude : {dasha_data['moon_longitude']}")
    print(f"Nakshatra               : {dasha_data['nakshatra']} (Pada {dasha_data['pada']})")
    print(f"Janma Dasha Ruler       : {dasha_data['first_dasha_ruler']}")
    print(f"Dasha Balance at Birth  : {dasha_data['balance_str']}")
    
    print("\n--- Mahadasha Timeline ---")
    print(f"{'Planet (ग्रह)':<18} | {'Start Date':<12} | {'End Date':<12} | {'Duration'}")
    print("-" * 60)
    for entry in dasha_data["timeline"]:
        p_str = f"{entry['planet']} ({entry['planet_hi']})"
        print(f"{p_str:<18} | {entry['start_date']} | {entry['end_date']} | {entry['duration']}")