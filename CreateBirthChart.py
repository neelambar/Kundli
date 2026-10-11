import os
import swisseph as swe

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================

# Hindi translations for Rashis and Planets
RASHI_NAMES_HI = {
    1: "मेष", 2: "वृषभ", 3: "मिथुन", 4: "कर्क",
    5: "सिंह", 6: "कन्या", 7: "तुला", 8: "वृश्चिक",
    9: "धनु", 10: "मकर", 11: "कुंभ", 12: "मीन"
}

PLANET_NAMES_HI = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहू",
    "Ketu": "केतु"
}

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


def calculate_kundli(year, month, day, hour, minute, second, lat, lon, tz_offset):
    """
    Calculates Lagna, Planetary Sidereal positions, Rashi numbers, and House mapping.
    tz_offset: Timezone offset from UTC in hours (e.g., +5.5 for IST).
    """
    # 1. Convert local birth time to UTC decimal hours
    local_decimal_hours = hour + (minute / 60.0) + (second / 3600.0)
    utc_decimal_hours = local_decimal_hours - tz_offset
    
    # 2. Calculate Julian Day number (in UTC)
    jd = swe.julday(year, month, day, utc_decimal_hours)

    # 3. Set Sidereal Mode to Lahiri Ayanamsa (Chitra Paksha)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    # 4. Calculate Lagna (Ascendant)
    # Using 'W' (Whole Sign) system so House 1 spans the full Lagna Rashi
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SIDEREAL)
    lagna_longitude = ascmc[0]
    lagna_rashi_num = int(lagna_longitude // 30) + 1  # 1-indexed (1=Aries, 2=Taurus...)

    # 5. Map Houses to Rashis (Counter-Clockwise in North Indian Style)
    # House 1 = Lagna Rashi, House 2 = Next Rashi, ..., House 12 = Previous Rashi
    house_to_rashi = {}
    for h in range(1, 13):
        r_num = ((lagna_rashi_num + h - 2) % 12) + 1
        house_to_rashi[h] = r_num

    # 6. Calculate Graha Positions
    planet_details = []
    house_planets = {h: [] for h in range(1, 13)}
    
    # Add Ascendant/Lagna first
    house_planets[1].append("लग्न")

    for name, p_id in PLANET_IDS.items():
        res, _ = swe.calc_ut(jd, p_id, swe.FLG_SIDEREAL)
        lon_deg = res[0]
        rashi_num = int(lon_deg // 30) + 1
        rem_deg = lon_deg % 30
        
        # Determine House (1 to 12) based on Lagna Rashi
        house_num = ((rashi_num - lagna_rashi_num) % 12) + 1
        house_planets[house_num].append(PLANET_NAMES_HI[name])
        
        planet_details.append({
            "name": PLANET_NAMES_HI[name],
            "rashi": RASHI_NAMES_HI[rashi_num],
            "deg": f"{rem_deg:05.2f}°",
            "house": house_num
        })

    # Ketu is 180° opposite Rahu
    rahu_lon = [p for p in planet_details if p["name"] == "राहू"][0]
    rahu_res, _ = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
    ketu_deg = (rahu_res[0] + 180.0) % 360.0
    ketu_rashi_num = int(ketu_deg // 30) + 1
    ketu_house = ((ketu_rashi_num - lagna_rashi_num) % 12) + 1
    house_planets[ketu_house].append("केतु")
    
    planet_details.append({
        "name": "केतु",
        "rashi": RASHI_NAMES_HI[ketu_rashi_num],
        "deg": f"{(ketu_deg % 30):05.2f}°",
        "house": ketu_house
    })

    swe.close()

    return {
        "birth_info": {
            "date": f"{day:02d}.{month:02d}.{year}",
            "time": f"{hour:02d}:{minute:02d}:{second:02d}",
            "lat": lat,
            "lon": lon,
            "ayanamsa": f"{ayanamsa:.4f}°"
        },
        "lagna_rashi": RASHI_NAMES_HI[lagna_rashi_num],
        "lagna_deg": f"{(lagna_longitude % 30):05.2f}°",
        "house_to_rashi": house_to_rashi,
        "house_planets": house_planets,
        "planet_details": planet_details
    }


def generate_html_chart(data, output_file="Kundli_Chart.html"):
    """
    Renders the North Indian Diamond Chart in HTML/CSS with counter-clockwise house layout.
    """
    house_planets = data["house_planets"]
    house_to_rashi = data["house_to_rashi"]
    info = data["birth_info"]

    html_content = f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<title>जन्म कुंडली - उत्तर भारतीय शैली</title>
<style>
    body {{
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f5f5f5;
        padding: 20px;
        color: #333;
    }}
    .container {{
        max-width: 800px;
        margin: 0 auto;
        background: #ffffff;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    h1, h2 {{
        text-align: center;
        color: #8b0000;
        margin-bottom: 5px;
    }}
    .info-bar {{
        display: flex;
        justify-content: space-around;
        background: #fffdf5;
        border: 1px solid #e0d0b0;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 20px;
        font-size: 14px;
    }}
    
    /* North Indian Diamond Layout */
    .kundli-box {{
        position: relative;
        width: 480px;
        height: 480px;
        border: 3px solid #8b0000;
        background-color: #fffdf5;
        margin: 0 auto 30px auto;
        box-sizing: border-box;
    }}
    .lines {{
        position: absolute;
        top: 0; left: 0;
        width: 100%; height: 100%;
        pointer-events: none;
    }}
    .house {{
        position: absolute;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        box-sizing: border-box;
        padding: 2px;
    }}
    .rashi-num {{
        font-size: 13px;
        font-weight: bold;
        color: #b30000;
    }}
    .planets {{
        font-size: 12px;
        font-weight: bold;
        color: #1a1a1a;
        margin-top: 2px;
        line-height: 1.2;
    }}

    /* House CSS Coordinates (Counter-Clockwise) */
    .h1  {{ top: 10%; left: 35%; width: 30%; height: 30%; }}
    .h2  {{ top: 2%;  left: 10%; width: 30%; height: 20%; }}
    .h3  {{ top: 15%; left: 2%;  width: 25%; height: 25%; }}
    .h4  {{ top: 35%; left: 10%; width: 30%; height: 30%; }}
    .h5  {{ top: 60%; left: 2%;  width: 25%; height: 25%; }}
    .h6  {{ top: 78%; left: 10%; width: 30%; height: 20%; }}
    .h7  {{ top: 60%; left: 35%; width: 30%; height: 30%; }}
    .h8  {{ top: 78%; left: 60%; width: 30%; height: 20%; }}
    .h9  {{ top: 60%; left: 73%; width: 25%; height: 25%; }}
    .h10 {{ top: 35%; left: 60%; width: 30%; height: 30%; }}
    .h11 {{ top: 15%; left: 73%; width: 25%; height: 25%; }}
    .h12 {{ top: 2%;  left: 60%; width: 30%; height: 20%; }}

    /* Table styling */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }}
    th, td {{
        border: 1px solid #ddd;
        padding: 8px 12px;
        text-align: center;
    }}
    th {{
        background-color: #8b0000;
        color: white;
    }}
    tr:nth-child(even) {{ background-color: #f9f9f9; }}
</style>
</head>
<body>

<div class="container">
    <h1>जन्म कुंडली (Kundli Chart)</h1>
    <h2>उत्तर भारतीय शैली (North Indian Style)</h2>
    
    <div class="info-bar">
        <div><b>दिनांक:</b> {info['date']}</div>
        <div><b>समय:</b> {info['time']}</div>
        <div><b>स्थान:</b> {info['lat']}° N, {info['lon']}° E</div>
        <div><b>लाहिड़ी अयनांश:</b> {info['ayanamsa']}</div>
    </div>

    <!-- North Indian Diamond Canvas -->
    <div class="kundli-box">
        <svg class="lines" viewBox="0 0 100 100" preserveAspectRatio="none">
            <line x1="0" y1="0" x2="100" y2="100" stroke="#8b0000" stroke-width="1.5"/>
            <line x1="100" y1="0" x2="0" y2="100" stroke="#8b0000" stroke-width="1.5"/>
            <line x1="50" y1="0" x2="0" y2="50" stroke="#8b0000" stroke-width="1.5"/>
            <line x1="0" y1="50" x2="50" y2="100" stroke="#8b0000" stroke-width="1.5"/>
            <line x1="50" y1="100" x2="100" y2="50" stroke="#8b0000" stroke-width="1.5"/>
            <line x1="100" y1="50" x2="50" y2="0" stroke="#8b0000" stroke-width="1.5"/>
        </svg>
"""

    # Populate 12 Houses (H1 = Top Center, H2 = Left, Counter-Clockwise)
    for h in range(1, 13):
        r_num = house_to_rashi[h]
        planets_str = ", ".join(house_planets[h])
        html_content += f"""
        <div class="house h{h}">
            <span class="rashi-num">{r_num}</span>
            <span class="planets">{planets_str}</span>
        </div>"""

    html_content += f"""
    </div>

    <h2>ग्रह स्थिति (Planetary Positions)</h2>
    <table>
        <thead>
            <tr>
                <th>ग्रह (Planet)</th>
                <th>राशि (Rashi)</th>
                <th>अंश (Degree)</th>
                <th>भाव (House)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b>लग्न (Ascendant)</b></td>
                <td>{data['lagna_rashi']}</td>
                <td>{data['lagna_deg']}</td>
                <td>1st House</td>
            </tr>
"""

    for p in data["planet_details"]:
        html_content += f"""
            <tr>
                <td><b>{p['name']}</b></td>
                <td>{p['rashi']}</td>
                <td>{p['deg']}</td>
                <td>{p['house']} House</td>
            </tr>"""

    html_content += """
        </tbody>
    </table>
</div>

</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"\n[+] Kundli generated successfully!")
    print(f"[+] Saved output file to: {os.path.abspath(output_file)}")


# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Input Birth Details
    birth_year = 1984
    birth_month = 2
    birth_day = 25
    
    birth_hour = 00       # 24-hour format
    birth_minute = 30
    birth_second = 0
    
    # Location: Garhakota, Madhya Pradesh, India
    latitude = 23.7801    # North
    longitude = 78.9620   # East
    timezone_offset = 5.5 # IST (+5:30 UTC)

    # 1. Run Calculations
    kundli_data = calculate_kundli(
        year=birth_year,
        month=birth_month,
        day=birth_day,
        hour=birth_hour,
        minute=birth_minute,
        second=birth_second,
        lat=latitude,
        lon=longitude,
        tz_offset=timezone_offset
    )

    # 2. Generate HTML File
    generate_html_chart(kundli_data, output_file="Garhakota_Kundli.html")