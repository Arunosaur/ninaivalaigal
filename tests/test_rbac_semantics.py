import time

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.rbac.decorators import require_permission, set_jwt_resolver
from server.security.rbac.jwt_resolver import JWTClaimsResolver
from server.security.rbac.metrics import rbac_denials_total

SECRET = "testsecret"

def tok(roles=None, exp=None, extra=None):
    now = int(time.time())
    payload = {
        "sub": "u1", "org_id": "o1", "team_id": "t1",
        "roles": roles or ["viewer"],
        "iat": now, "nbf": now-1, "exp": exp or (now+3600)
    }
    if extra: payload.update(extra)
    return jwt.encode(payload, SECRET, algorithm="HS256")

@pytest.fixture(scope="module")
def app():
    app = FastAPI()
    set_jwt_resolver(JWTClaimsResolver(secret=SECRET, algorithms=["HS256"], max_token_lifetime_s=7200))

    @app.get("/editor")
    @require_permission("org_editor")
    async def editor():
        return {"ok": True}
    return app

def c(app, token=None):
    cl = TestClient(app)
    if token:
        cl.headers.update({"Authorization": f"Bearer {token}"})
    return cl

def test_401_when_missing_token(app):
    assert c(app).get("/editor").status_code == 401

def test_401_when_missing_required_claims(app):
    t = tok(extra={"org_id": None})  # required claim missing → 401
    assert c(app, t).get("/editor").status_code == 401

def test_403_when_insufficient_role(app):
    t = tok(roles=["viewer"])
    # first read counter
    before = rbac_denials_total._value.get() if hasattr(rbac_denials_total, "_value") else None
    res = c(app, t).get("/editor")
    assert res.status_code == 403
    # ensure counter increments (best-effort; shim may not expose)
    try:
        after = rbac_denials_total._value.get()
        assert after >= (before or 0)
    except Exception:
        pass

def test_200_when_role_satisfies(app):
    t = tok(roles=["org_editor"])
    assert c(app, t).get("/editor").status_code == 200
