# Kundli Generator (Python)

A web page that asks for **name, date, time and birth place**. It generates a North Indian
style kundli (Lahiri ayanamsa, whole-sign houses) and saves it so you can reopen it later
from a dropdown.

| File | Purpose |
|---|---|
| `app.py` | Flask app for self-hosting (gunicorn on OCI / any Linux server) |
| `function_app.py` | The same routes as an Azure Functions app (Python v2 model) |
| `kundli_service.py` | Form validation and chart building, shared by both apps |
| `CreateBirthChart.py` | Calculation (`calculate_kundli`) and chart HTML. Still works as a CLI script |
| `pages.py` | Main page: form, saved-kundli dropdown, place search |
| `geo.py` | Place lookup (Open-Meteo, no API key) and historical UTC offset (handles DST) |
| `kundli_store.py` | Storage: SQLite (self-hosted), Azure Table Storage, or a local JSON file |
| `deploy/` | systemd service (and an optional Caddy site block) for the self-hosted setup |
| `dasha.py` | Vimshottari dasha (not wired into the web app yet) |

Routes: `GET /` (page, `?id=` shows a saved kundli), `POST /kundli` (generate, and optionally save),
`POST /kundli/{id}/delete`, `GET /api/places?q=` (place search).

Below the birth chart, a **transit (gochar) chart** shows the planets as of the moment the page is
loaded, with the lagna rising at the optional **current place** (the birth place if left blank). The
current place isn't saved with the kundli: it travels in the URL (`cur_place`, `cur_lat`, `cur_lon`,
`cur_timezone`) and the browser remembers the last one you picked. Reload the page to refresh the transit.

Only the birth inputs are stored. The chart is recomputed each time you view it.

## Run locally (Azure Functions)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy local.settings.example.json local.settings.json   # stores kundlis in kundlis.json
func start
```

Open http://localhost:7071/.

To test against Table Storage locally, run [Azurite](https://learn.microsoft.com/azure/storage/common/storage-use-azurite)
and remove `KUNDLI_LOCAL_STORE` from `local.settings.json`.

## Deploy on an OCI Ubuntu instance

gunicorn runs the Flask app on port 8000 as a systemd service. You open it at
`http://<server-public-ip>:8000`. Saved kundlis live in a SQLite file at `/var/lib/kundli/kundli.db`.

The steps assume the user `ubuntu` and a clone at `/home/ubuntu/Kundli`. If yours differ, edit
`deploy/kundli.service`.

**1. Install Python tools and get the code:**

```bash
sudo apt update && sudo apt install -y python3-venv python3-dev build-essential git
cd ~ && git clone https://github.com/neelambar/Kundli.git && cd Kundli
python3 -m venv .venv
.venv/bin/pip install -r requirements-server.txt
```

`build-essential` and `python3-dev` are only needed if `pyswisseph` has to compile (e.g. on an Ampere/ARM instance).

**2. Quick check:** run `.venv/bin/gunicorn --bind 127.0.0.1:8000 app:app`,
then in a second SSH session run `curl -s localhost:8000/healthz`. It should print `ok`. Stop it with Ctrl+C, then delete the test `kundli.db` it created.

**3. Run it as a service** (starts on boot and restarts if it crashes):

```bash
sudo cp deploy/kundli.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now kundli
systemctl status kundli
```

**4. Open port 8000.** OCI blocks it in **two** places, and both must allow it:
- OCI console → your instance → subnet → Security List → add an ingress rule: source `0.0.0.0/0`, TCP, port `8000`.
- On the instance (OCI's Ubuntu images also block ports with iptables):
  ```bash
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
  sudo netfilter-persistent save
  ```

Then open `http://<server-public-ip>:8000`.

**Optional: a domain with HTTPS.** If you later want `https://kundli.yourdomain.com`, use Caddy in front of
the app. Caddy handles HTTPS and forwards requests to port 8000. See `deploy/Caddyfile.example`, change
`--bind 0.0.0.0:8000` to `127.0.0.1:8000` in the service file, and open ports 80/443 instead of 8000.

**Update** after pushing changes to GitHub:

```bash
~/Kundli/deploy/update.sh
```

It pulls, installs requirements, restarts the service and checks that it answers (printing recent
logs if it doesn't). It's the same as running
`cd ~/Kundli && git pull && .venv/bin/pip install -r requirements-server.txt && sudo systemctl restart kundli`.

**Logs:** `journalctl -u kundli -f`

**Back up** the saved kundlis: `sqlite3 /var/lib/kundli/kundli.db ".backup ~/kundli-backup-$(date +%F).db"`
(install the CLI with `sudo apt install sqlite3`).

**Access:** there's no login and it's plain HTTP, so anyone who can reach the URL can view and add kundlis.
To limit that, set the Security List rule's source to your own IP (e.g. `203.0.113.5/32`) instead of `0.0.0.0/0`.

## Deploy to Azure

Prerequisites: Azure CLI (`az login`) and Azure Functions Core Tools v4.

```powershell
$RG="kundli-rg"; $LOC="centralindia"; $ST="kundlistore$(Get-Random -Max 99999)"; $APP="kundli-app-$(Get-Random -Max 99999)"

az group create -n $RG -l $LOC
az storage account create -n $ST -g $RG -l $LOC --sku Standard_LRS
az functionapp create -n $APP -g $RG --storage-account $ST `
  --consumption-plan-location $LOC --os-type Linux `
  --runtime python --runtime-version 3.11 --functions-version 4

# Serve our page at "/" instead of the default Functions welcome page
az functionapp config appsettings set -n $APP -g $RG --settings AzureWebJobsDisableHomepage=true

func azure functionapp publish $APP
```

The app is then at `https://<APP>.azurewebsites.net/`. Kundlis are stored in the `Kundlis` table
of the Function App's storage account (`AzureWebJobsStorage`). To use a different account, set the
`KUNDLI_STORAGE_CONNECTION` app setting.

**Access:** the functions are anonymous, so anyone with the URL can view and add kundlis. To make the
app private, turn on App Service Authentication (Easy Auth) for the Function App in the portal.
