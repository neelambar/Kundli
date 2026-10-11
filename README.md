# Kundli Generator (Python)

A web page that asks for **name, date, time and birth place**. It generates a North Indian
style kundli (Lahiri ayanamsa, whole-sign houses) and saves it so you can reopen it later
from a dropdown.

| File | Purpose |
|---|---|
| `app.py` | Flask app for self-hosting (gunicorn + Caddy on OCI / any Linux server) |
| `function_app.py` | The same routes as an Azure Functions app (Python v2 model) |
| `kundli_service.py` | Form validation and chart building, shared by both apps |
| `CreateBirthChart.py` | Calculation (`calculate_kundli`) and chart HTML. Still works as a CLI script |
| `pages.py` | Main page: form, saved-kundli dropdown, place search |
| `geo.py` | Place lookup (Open-Meteo, no API key) and historical UTC offset (handles DST) |
| `kundli_store.py` | Storage: SQLite (self-hosted), Azure Table Storage, or a local JSON file |
| `deploy/` | systemd service and Caddy site block for the self-hosted setup |
| `dasha.py` | Vimshottari dasha (not wired into the web app yet) |

Routes: `GET /` (page, `?id=` shows a saved kundli), `POST /kundli` (generate, and optionally save),
`POST /kundli/{id}/delete`, `GET /api/places?q=` (place search).

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

## Deploy on an OCI Ubuntu instance (gunicorn + Caddy)

gunicorn runs the Flask app on `127.0.0.1:8000` as a systemd service. Your existing Caddy serves it
publicly and handles HTTPS. Saved kundlis live in a SQLite file at `/var/lib/kundli/kundli.db`.

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

**4. Add the site to Caddy:** copy the block from `deploy/Caddyfile.example` into `/etc/caddy/Caddyfile`
with your domain, then:

```bash
caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

The domain's DNS A record must point at the instance's public IP. Caddy then gets the HTTPS certificate on its own.

**5. Ports:** only Caddy's ports need to be open. Port 8000 stays on localhost. If Caddy already serves
other sites on 80/443, nothing changes. Otherwise open them in **both** places, because OCI's Ubuntu
images also block them in iptables:
- OCI console → subnet Security List: ingress TCP 80 and 443 from `0.0.0.0/0`.
- On the instance:
  ```bash
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
  sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
  sudo netfilter-persistent save
  ```

**Update** after pushing changes to GitHub:

```bash
cd ~/Kundli && git pull && .venv/bin/pip install -r requirements-server.txt && sudo systemctl restart kundli
```

**Logs:** `journalctl -u kundli -f`

**Back up** the saved kundlis: `sqlite3 /var/lib/kundli/kundli.db ".backup ~/kundli-backup-$(date +%F).db"`
(install the CLI with `sudo apt install sqlite3`).

**Access:** there's no login, so anyone who can reach the URL can view and add kundlis. To restrict it,
add `basic_auth` to the site block in Caddy (generate the hash with `caddy hash-password`).

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
