from fastapi import FastAPI, Body
from typing import Optional, List, Dict, Any

try:
    # example; adapt to your actual mem0 usage
    from mem0 import MemoryClient  # or MemoryStore depending on API
except Exception:  # pragma: no cover
    MemoryClient = object  # stub to avoid import errors during scaffolding

app = FastAPI()
client = MemoryClient() if isinstance(MemoryClient, type) else None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/remember")
def remember(text: str = Body(..., embed=True), metadata: Optional[Dict[str, Any]] = None):
    # TODO: wire org/team/user scoping in headers or body as you choose
    # return client.add(text=text, metadata=metadata)
    return {"ok": True, "id": "mem_123"}  # stub until wired

@app.get("/recall")
def recall(q: str, k: int = 5):
    # return client.search(query=q, k=k)
    return {"ok": True, "items": []}  # stub until wired

@app.delete("/memories/{mid}")
def delete(mid: str):
    # client.delete(id=mid)
    return {"ok": True, "deleted": mid}
