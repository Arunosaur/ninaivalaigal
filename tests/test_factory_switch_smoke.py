import os, importlib, pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def restore_env():
    o = os.environ.copy()
    yield
    os.environ.clear(); os.environ.update(o)

def build():
    app = FastAPI()
    mod = importlib.import_module("server.app.app_factory_patch")
    mod.wire_memory_store(app)
    return app

def test_inmemory_default(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = build()
    c = TestClient(app)
    assert c.get("/healthz/memory").json()["backend"].lower().startswith("inmemory")

def test_postgres_when_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL","postgresql://postgres:postgres@localhost:5432/postgres")
    app = build()
    c = TestClient(app)
    assert "postgres" in c.get("/healthz/memory").json()["backend"].lower()
