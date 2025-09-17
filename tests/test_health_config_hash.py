from fastapi import FastAPI
from fastapi.testclient import TestClient
from server.health.config_hash_guard import router, compute_hash

def test_health_config_hash_endpoint_exposes_hash(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "s1")
    monkeypatch.setenv("UPLOAD_LIMIT", "10MB")
    monkeypatch.setenv("REDIS_URL", "memory://")

    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)

    r = c.get("/healthz/config")
    assert r.status_code == 200
    h = r.json().get("security_config_hash")
    assert h == compute_hash()
    assert len(h) == 64
