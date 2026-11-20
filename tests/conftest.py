import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import calculate
from app.source import load_sample


@pytest.fixture
def dirty():
    return load_sample("dirty")


@pytest.fixture
def clean():
    return load_sample("clean")


@pytest.fixture
def stages(dirty):
    return calculate(dirty)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("SERIAL_LEDGER_DB", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as test_client:
        yield test_client
