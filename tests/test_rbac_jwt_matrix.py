import time

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.rbac.decorators import require_permission, set_jwt_resolver
from server.security.rbac.jwt_resolver import JWTClaimsResolver

SECRET = "testsecret"

def make_token(sub="u1", org="o1", team="t1", roles=None, exp=None):
    now = int(time.time())
    payload = {"sub": sub, "org_id": org, "team_id": team,
               "roles": roles or ["team_admin"], "iat": now, "nbf": now-1, "exp": exp or (now+3600)}
    return jwt.encode(payload, SECRET, algorithm="HS256")

@pytest.fixture(scope="module")
def app():
    app = FastAPI()
    set_jwt_resolver(JWTClaimsResolver(secret=SECRET, algorithms=["HS256"]))

    @app.get("/secure")
    @require_permission("org_editor")
    async def secure_endpoint():
        return {"ok": True}
    return app

def client_with_token(app, token):
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {token}"})
    return c

def test_allow_via_inheritance(app):
    t = make_token(roles=["team_admin"])  # expands to org_editor
    c = client_with_token(app, t)
    assert c.get("/secure").status_code == 200

def test_deny_when_no_role(app):
    t = make_token(roles=["viewer"])  # no org_editor
    c = client_with_token(app, t)
    assert c.get("/secure").status_code == 403

def test_expired_token_denied(app):
    t = make_token(exp=int(time.time()) - 10)
    c = client_with_token(app, t)
    assert c.get("/secure").status_code in (401, 403)

def test_malformed_token_denied(app):
    c = TestClient(app)
    c.headers.update({"Authorization": "Bearer not-a-jwt"})
    r = c.get("/secure")
    assert r.status_code in (401, 403)
