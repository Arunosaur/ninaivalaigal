# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
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

# --- Persistence ---
DATA_FILE = "mem0_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    # Default data structure
    return {"memories": [], "recording_context": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- Application ---
app = FastAPI()

data = load_data()
memories = data["memories"]
# This is a global state, there is only one active recording context at a time
recording_context = data["recording_context"]

@app.get("/")
def read_root():
    return {"message": "mem0-server is running"}

@app.post("/memory")
def create_memory(entry: MemoryEntry):
    # We only save the memory if its context matches the active recording context
    if entry.context == recording_context:
        memories.append(entry.dict())
        save_data({"memories": memories, "recording_context": recording_context})
        return {"message": "Memory entry recorded."}
    else:
        return {"message": "Memory entry ignored. Context does not match recording context."}

@app.get("/memory")
def get_memory(context: str):
    return [m['payload'] for m in memories if m['context'] == context]

@app.post("/context/start")
def start_recording(context: str):
    global recording_context
    recording_context = context
    save_data({"memories": memories, "recording_context": recording_context})
    return {"message": f"Now recording to context: {context}"}

@app.post("/context/stop")
def stop_recording():
    global recording_context
    recording_context = None
    save_data({"memories": memories, "recording_context": recording_context})
    return {"message": "Recording stopped."}

@app.get("/context/active")
def get_active_recording_context():
    return {"recording_context": recording_context}

