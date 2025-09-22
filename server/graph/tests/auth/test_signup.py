def test_signup(client):
    response = client.post(
        "/auth/signup", json={"username": "testuser", "password": "StrongPass123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
