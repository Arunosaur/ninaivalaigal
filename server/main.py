# main.py

from fastapi import FastAPI
from pydantic import BaseModel
import json
import os

# --- Data Models ---
class MemoryPayload(BaseModel):
    type: str
    source: str
    data: dict

class MemoryEntry(BaseModel):
    context: str
    payload: MemoryPayload

class ContextSwitch(BaseModel):
    client_id: str
    context: str

# --- Persistence ---
DATA_FILE = "mem0_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"memories": [], "active_contexts": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Application ---
PORT = int(os.getenv("MEM0_PORT", 13370))
app = FastAPI()

data = load_data()
memories = data["memories"]
active_contexts = data["active_contexts"]

# --- Entry point for running standalone ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT)

@app.get("/")
def read_root():
    return {"message": "mem0-server is running"}

@app.post("/memory")
def create_memory(entry: MemoryEntry):
    memories.append(entry.dict())
    save_data({"memories": memories, "active_contexts": active_contexts})
    return {"message": "Memory entry created successfully"}

@app.get("/memory")
def get_memory(context: str):
    return [m['payload'] for m in memories if m['context'] == context]

@app.post("/context")
def switch_context(switch: ContextSwitch):
    active_contexts[switch.client_id] = switch.context
    save_data({"memories": memories, "active_contexts": active_contexts})
    return {"message": f"Client {switch.client_id} switched to context {switch.context}"}

