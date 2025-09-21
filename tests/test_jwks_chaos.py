
def test_jwks_failure(monkeypatch, client):
    # Simulate JWKS offline by monkeypatching fetch
    from server.security import jwks_utils
    monkeypatch.setattr(jwks_utils, "fetch_keys", lambda: (_ for _ in ()).throw(Exception("JWKS offline")))
    resp = client.get("/secure-endpoint")
    assert resp.status_code == 401
