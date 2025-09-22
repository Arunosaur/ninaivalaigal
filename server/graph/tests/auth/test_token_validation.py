def test_token_auth(client, valid_token):
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/memory/health", headers=headers)
    assert response.status_code == 200
