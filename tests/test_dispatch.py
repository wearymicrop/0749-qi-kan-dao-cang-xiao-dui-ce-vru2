import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.config import database_path
from app.main import app
from app.manifest import canonical
from app.modules.m7_dispatch.service import dispatch


def test_archive_and_rerun_keep_digest_and_first_result(client):
    # TRAP-12
    first = client.post("/api/runs", json={"sample": "dirty"}).json()
    again = client.post(f"/api/runs/{first['id']}/rerun").json()
    assert first["reused"] is False and again == {**first, "reused": True}


def test_archive_survives_new_connection(client):
    first = client.post("/api/runs", json={"sample": "clean"}).json()
    with TestClient(app) as independent:
        obtained = independent.get(f"/api/runs/{first['id']}").json()
    assert obtained == {key: value for key, value in first.items() if key != "reused"}


def test_attachment_contains_original_snapshot_and_claims(client, dirty):
    run = client.post("/api/runs", json={"sample": "dirty"}).json()
    result = client.get(f"/api/runs/{run['id']}/export")
    assert 'attachment; filename="serial-' in result.headers["content-disposition"]
    assert result.json()["source"] == dirty
    assert result.json()["result"]["balance"]["totals"]["disputed"] == 3


def test_manifest_hashes_exact_canonical_input(client, clean):
    manifest = client.post("/api/runs", json={"data": clean}).json()["manifest"]
    assert manifest["input_sha256"] == hashlib.sha256(canonical(clean).encode()).hexdigest()
    assert manifest["records"] == 10


def test_invalid_source_cannot_leave_partial_archive(client, clean):
    client.get("/api/health")
    response = client.post("/api/runs", json={"data": {**clean, "titles": []}})
    assert response.status_code == 422
    with sqlite3.connect(database_path()) as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0


def test_concurrent_retries_have_one_row(client, dirty):
    with ThreadPoolExecutor(max_workers=4) as workers:
        result = list(workers.map(lambda _: dispatch(dirty, "dirty"), range(4)))
    assert sum(not r["reused"] for r in result) == 1
    assert len({r["id"] for r in result}) == 1
    with sqlite3.connect(database_path()) as db:
        assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1


def test_missing_and_unspecified_source_errors(client):
    assert client.get("/api/runs/unknown").json()["code"] == "RUN_NOT_FOUND"
    assert client.post("/api/runs", json={}).json()["code"] == "CHOOSE_SOURCE"
    assert client.post("/api/runs", json={"sample": "absent"}).status_code == 404
