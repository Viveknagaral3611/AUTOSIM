"""Local run persistence, with one SQLite connection per operation."""

import json
from pathlib import Path
import sqlite3


class RunStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT, payload TEXT)")

    def save(self, run):
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO runs VALUES (?, ?, ?)",
                       (run["id"], run["created_at"], json.dumps(run, allow_nan=False)))

    def get(self, run_id):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM runs WHERE id = ?", (run_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def recent(self):
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT payload FROM runs ORDER BY created_at DESC, id DESC LIMIT 20").fetchall()
        return [{key: run[key] for key in ("id", "created_at", "status", "adapter", "mission", "metrics")}
                for run in (json.loads(row[0]) for row in rows)]
