#!/usr/bin/env bash
# Pulls the latest code on the server, installs dependencies and restarts the service.
# Usage: ~/Kundli/deploy/update.sh
set -euo pipefail

cd "$(dirname "$0")/.."

git pull --ff-only
.venv/bin/pip install -q -r requirements-server.txt
sudo systemctl restart kundli

# Give gunicorn a moment to start, then confirm it's answering
for _ in 1 2 3 4 5; do
    if curl -fs localhost:8000/healthz >/dev/null; then
        echo "Updated to $(git log -1 --format='%h %s') — service is up."
        exit 0
    fi
    sleep 1
done

echo "Service did not respond on port 8000. Recent logs:" >&2
journalctl -u kundli -n 30 --no-pager >&2
exit 1
