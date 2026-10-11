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