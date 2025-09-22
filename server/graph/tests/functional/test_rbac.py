def test_rbac_access_denied(client):
    response = client.get("/admin/protected")
    assert response.status_code in [401, 403]