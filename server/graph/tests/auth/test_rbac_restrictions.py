def test_access_forbidden_role(client, user_with_invalid_role):
    token = user_with_invalid_role["access_token"]
    response = client.post("/admin/only", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
