import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone

# Saved kundlis hold only the birth inputs; the chart is recomputed on view.
FIELDS = ("name", "date", "time", "place", "lat", "lon", "timezone")


class TableKundliStore:
    """Azure Table Storage backend (uses the Function App's storage account)."""

    PARTITION = "kundli"

    def __init__(self, connection_string, table_name="Kundlis"):
        from azure.data.tables import TableServiceClient

        service = TableServiceClient.from_connection_string(connection_string)
        self._table = service.create_table_if_not_exists(table_name)

    def list(self):
        rows = self._table.query_entities(f"PartitionKey eq '{self.PARTITION}'", select=["RowKey", "name", "date", "place"])
        items = [{"id": r["RowKey"], "name": r["name"], "date": r["date"], "place": r.get("place", "")} for r in rows]
        return sorted(items, key=lambda k: k["name"].lower())

    def get(self, kundli_id):
        from azure.core.exceptions import ResourceNotFoundError

        try:
            r = self._table.get_entity(self.PARTITION, kundli_id)
        except ResourceNotFoundError:
            return None
        return {"id": kundli_id, **{f: r.get(f) for f in FIELDS}}

    def add(self, record):
        kundli_id = uuid.uuid4().hex
        self._table.create_entity({
            "PartitionKey": self.PARTITION,
            "RowKey": kundli_id,
            "created": datetime.now(timezone.utc).isoformat(),
            **{f: record[f] for f in FIELDS},
        })
        return kundli_id

    def delete(self, kundli_id):
        self._table.delete_entity(self.PARTITION, kundli_id)


class SqliteKundliStore:
    """SQLite backend for the self-hosted (gunicorn + Caddy) deployment."""

    def __init__(self, path):
        self._path = path
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS kundlis ("
                "id TEXT PRIMARY KEY, name TEXT NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL, "
                "place TEXT, lat REAL NOT NULL, lon REAL NOT NULL, timezone TEXT NOT NULL, created TEXT NOT NULL)"
            )

    def _connect(self):
        db = sqlite3.connect(self._path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def list(self):
        with self._connect() as db:
            rows = db.execute("SELECT id, name, date, place FROM kundlis ORDER BY name COLLATE NOCASE").fetchall()
        return [{"id": r["id"], "name": r["name"], "date": r["date"], "place": r["place"] or ""} for r in rows]

    def get(self, kundli_id):
        with self._connect() as db:
            r = db.execute("SELECT * FROM kundlis WHERE id = ?", (kundli_id,)).fetchone()
        return {"id": kundli_id, **{f: r[f] for f in FIELDS}} if r else None

    def add(self, record):
        kundli_id = uuid.uuid4().hex
        with self._connect() as db:
            db.execute(
                f"INSERT INTO kundlis (id, {', '.join(FIELDS)}, created) VALUES (?, {', '.join('?' * len(FIELDS))}, ?)",
                (kundli_id, *(record[f] for f in FIELDS), datetime.now(timezone.utc).isoformat()),
            )
        return kundli_id

    def delete(self, kundli_id):
        with self._connect() as db:
            db.execute("DELETE FROM kundlis WHERE id = ?", (kundli_id,))


class FileKundliStore:
    """JSON-file backend for local development without Azurite."""

    def __init__(self, path):
        self._path = path
        self._lock = threading.Lock()

    def _load(self):
        if not os.path.exists(self._path):
            return {}
        with open(self._path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def list(self):
        items = [{"id": k, "name": v["name"], "date": v["date"], "place": v.get("place", "")} for k, v in self._load().items()]
        return sorted(items, key=lambda k: k["name"].lower())

    def get(self, kundli_id):
        rec = self._load().get(kundli_id)
        return {"id": kundli_id, **rec} if rec else None

    def add(self, record):
        kundli_id = uuid.uuid4().hex
        with self._lock:
            data = self._load()
            data[kundli_id] = {f: record[f] for f in FIELDS}
            self._save(data)
        return kundli_id

    def delete(self, kundli_id):
        with self._lock:
            data = self._load()
            data.pop(kundli_id, None)
            self._save(data)


def get_store():
    """
    KUNDLI_DB=<path.sqlite> -> SQLite; KUNDLI_LOCAL_STORE=<path.json> -> local file;
    otherwise Azure Table Storage via KUNDLI_STORAGE_CONNECTION (falls back to the
    Function App's AzureWebJobsStorage).
    """
    db_path = os.environ.get("KUNDLI_DB")
    if db_path:
        return SqliteKundliStore(db_path)
    local_path = os.environ.get("KUNDLI_LOCAL_STORE")
    if local_path:
        return FileKundliStore(local_path)
    conn = os.environ.get("KUNDLI_STORAGE_CONNECTION") or os.environ["AzureWebJobsStorage"]
    return TableKundliStore(conn)
