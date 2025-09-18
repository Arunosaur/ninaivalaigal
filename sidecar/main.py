from fastapi import FastAPI
from mem0 import MemoryStore

app = FastAPI()
store = MemoryStore()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/store")
def store_memory(item: dict):
    return store.add(item)

@app.get("/recall/{query}")
def recall(query: str):
    return store.search(query)
