from fastapi.testclient import TestClient
from fastapi import FastAPI
from server.memory.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_write_and_query():
    response = client.post("/memory/write", json={"content":"hello","scope":"personal"})
    assert response.status_code == 200
