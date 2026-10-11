import html

from CreateBirthChart import CHART_CSS

PAGE_CSS = """
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f5f5f5;
        margin: 0;
        padding: 20px 16px;
        color: #333;
    }
    .container {
        max-width: 800px;
        margin: 0 auto 20px auto;
        background: #ffffff;
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        box-sizing: border-box;
    }
    .app-title { text-align: center; color: #8b0000; margin: 0 0 18px 0; }
    .saved-bar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .saved-bar select { flex: 1; min-width: 200px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .grid .full { grid-column: 1 / -1; }
    @media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
    label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #5a1a1a; }
    input, select, button {
        font: inherit;
        padding: 8px 10px;
        border: 1px solid #ccc;
        border-radius: 5px;
        width: 100%;
        box-sizing: border-box;
        background: #fff;
    }
    button {
        background: #8b0000; color: #fff; border: none; cursor: pointer; width: auto; padding: 9px 18px;
    }
    button.secondary { background: #fff; color: #8b0000; border: 1px solid #8b0000; }
    .actions { display: flex; gap: 12px; align-items: center; margin-top: 16px; flex-wrap: wrap; }
    .actions label { display: inline; font-weight: normal; }
    .actions input[type=checkbox] { width: auto; }
    .hint { font-size: 12px; color: #777; margin-top: 4px; }
    .error { background: #fde8e8; color: #8b0000; padding: 10px; border-radius: 5px; margin-bottom: 14px; }
    details { margin-top: 12px; }
    summary { cursor: pointer; font-size: 13px; color: #8b0000; }
    .chart-actions { display: flex; justify-content: flex-end; margin-bottom: 8px; }
"""

PAGE_JS = """
const placeInput = document.getElementById('place');
const matches = document.getElementById('place-matches');
const lat = document.getElementById('lat'), lon = document.getElementById('lon'), tz = document.getElementById('timezone');
let results = [];

document.getElementById('find-place').addEventListener('click', async () => {
    const q = placeInput.value.trim();
    if (q.length < 2) return;
    matches.innerHTML = '<option>Searching…</option>';
    matches.hidden = false;
    try {
        const resp = await fetch('/api/places?q=' + encodeURIComponent(q));
        results = await resp.json();
    } catch (e) { results = []; }
    if (!results.length) { matches.innerHTML = '<option>No matches found</option>'; return; }
    matches.innerHTML = results.map((p, i) =>
        `<option value="${i}">${p.label.replace(/</g, '&lt;')} (${p.lat.toFixed(2)}, ${p.lon.toFixed(2)})</option>`).join('');
    pick(0);
});
matches.addEventListener('change', () => pick(+matches.value));
function pick(i) {
    const p = results[i];
    if (!p) return;
    placeInput.value = p.label;
    lat.value = p.lat; lon.value = p.lon; tz.value = p.timezone;
}
placeInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); document.getElementById('find-place').click(); }
});

document.getElementById('saved').addEventListener('change', e => {
    if (e.target.value) location.href = '/?id=' + encodeURIComponent(e.target.value);
});
"""


def render_page(saved, selected_id=None, chart_html="", form=None, error=""):
    esc = html.escape
    form = form or {}
    v = lambda k: esc(str(form.get(k, "")), quote=True)

    options = '<option value="">— Select a saved kundli —</option>' + "".join(
        f'<option value="{esc(k["id"])}"{" selected" if k["id"] == selected_id else ""}>'
        f'{esc(k["name"])} — {esc(k["date"])}{" — " + esc(k["place"]) if k.get("place") else ""}</option>'
        for k in saved
    )

    chart_block = ""
    if chart_html:
        delete_form = ""
        if selected_id:
            delete_form = f"""
        <form class="chart-actions" method="post" action="/kundli/{esc(selected_id)}/delete"
              onsubmit="return confirm('Delete this kundli?');">
            <button type="submit" class="secondary">Delete</button>
        </form>"""
        chart_block = f'<div class="container">{delete_form}{chart_html}</div>'

    return f"""<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kundli Generator</title>
<style>{PAGE_CSS}{CHART_CSS}</style>
</head>
<body>

<div class="container">
    <h1 class="app-title">जन्म कुंडली (Kundli Generator)</h1>

    <label for="saved">Saved kundlis</label>
    <div class="saved-bar">
        <select id="saved">{options}</select>
        <a href="/"><button type="button" class="secondary">New</button></a>
    </div>
</div>

<div class="container">
    {f'<div class="error">{esc(error)}</div>' if error else ''}
    <form method="post" action="/kundli">
        <div class="grid">
            <div class="full">
                <label for="name">Name</label>
                <input id="name" name="name" required maxlength="100" value="{v('name')}">
            </div>
            <div>
                <label for="date">Date of birth</label>
                <input id="date" name="date" type="date" required min="1800-01-01" max="2100-12-31" value="{v('date')}">
            </div>
            <div>
                <label for="time">Time of birth (local, 24h)</label>
                <input id="time" name="time" type="time" step="1" required value="{v('time')}">
            </div>
            <div class="full">
                <label for="place">Birth place</label>
                <div class="saved-bar">
                    <input id="place" name="place" required maxlength="200" placeholder="e.g. Garhakota" value="{v('place')}">
                    <button type="button" id="find-place" class="secondary">Find</button>
                </div>
                <select id="place-matches" hidden style="margin-top:8px"></select>
                <div class="hint">Click Find and pick the right match — it fills latitude, longitude and timezone.</div>
            </div>
        </div>
        <details{' open' if error else ''}>
            <summary>Coordinates &amp; timezone</summary>
            <div class="grid" style="margin-top:10px">
                <div>
                    <label for="lat">Latitude (N +, S −)</label>
                    <input id="lat" name="lat" type="number" step="any" min="-90" max="90" required value="{v('lat')}">
                </div>
                <div>
                    <label for="lon">Longitude (E +, W −)</label>
                    <input id="lon" name="lon" type="number" step="any" min="-180" max="180" required value="{v('lon')}">
                </div>
                <div class="full">
                    <label for="timezone">Timezone (IANA name)</label>
                    <input id="timezone" name="timezone" required placeholder="Asia/Kolkata" value="{v('timezone') or 'Asia/Kolkata'}">
                </div>
            </div>
        </details>
        <div class="actions">
            <button type="submit">Generate Kundli</button>
            <input type="checkbox" id="save" name="save" checked>
            <label for="save">Save to list</label>
        </div>
    </form>
</div>

{chart_block}

<script>{PAGE_JS}</script>
</body>
</html>
"""
