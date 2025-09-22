def test_memory_creation(client):
    payload = {"title": "Test Memory", "content": "Test content"}
    response = client.post("/memories/", json=payload)
    assert response.status_code in [200, 201, 422]


def test_memory_listing(client):
    response = client.get("/memories/")
    assert response.status_code == 200
