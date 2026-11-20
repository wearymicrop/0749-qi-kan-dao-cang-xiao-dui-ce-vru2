import json
import sqlite3
from contextlib import closing

from app.config import database_path
from app.errors import LedgerError
from app.manifest import canonical


def connect():
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    try:
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, source TEXT NOT NULL, document TEXT NOT NULL)")
    except BaseException:
        db.close()
        raise
    return db


def archive(document, source):
    with closing(connect()) as db, db:
        inserted = db.execute("INSERT INTO runs VALUES (?, ?, ?) ON CONFLICT(id) DO NOTHING",
                              (document["id"], canonical(source), canonical(document))).rowcount
        stored = db.execute("SELECT document FROM runs WHERE id = ?", (document["id"],)).fetchone()[0]
    return {**json.loads(stored), "reused": inserted == 0}


def get_run(run_id):
    with closing(connect()) as db:
        row = db.execute("SELECT document, source FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        raise LedgerError("RUN_NOT_FOUND", "未找到该归档", 404)
    return json.loads(row[0]), json.loads(row[1])
