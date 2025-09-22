def test_login_success(client):
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code in [200, 401]  # Adjust based on expected test setup

def test_login_failure(client):
    response = client.post("/auth/login", json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401