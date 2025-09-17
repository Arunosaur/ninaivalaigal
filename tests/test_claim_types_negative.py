def test_invalid_claims(client, make_jwt):
    token = make_jwt(claims={"org_id": 123, "roles": "viewer"})
    resp = client.get("/secure-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
