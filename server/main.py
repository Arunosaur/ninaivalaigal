# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import os
from database import DatabaseManager
import json as json_lib

# --- Data Models ---
class MemoryPayload(BaseModel):
    type: str
    source: str
    data: dict

class MemoryEntry(BaseModel):
    context: str
    payload: MemoryPayload

# --- Configuration ---
def load_config():
    config_path = "mem0.config.json"
    default_config = {
        "storage": {
            "database_url": "sqlite:///./mem0.db"
        }
    }
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json_lib.load(f)
                if "storage" in user_config and "database_url" in user_config["storage"]:
                    return user_config["storage"]["database_url"]
        return default_config["storage"]["database_url"]
    except Exception:
        return default_config["storage"]["database_url"]

# --- Database Setup ---
database_url = load_config()
db = DatabaseManager(database_url)

# Migrate existing JSON data if it exists
db.migrate_from_json()

# --- Application ---
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "mem0-server is running"}

@app.post("/memory")
def create_memory(entry: MemoryEntry):
    try:
        active_context = db.get_active_context()
        # We only save the memory if its context matches the active recording context
        if entry.context == active_context:
            memory_id = db.add_memory(
                context=entry.context,
                memory_type=entry.payload.type,
                source=entry.payload.source,
                data=entry.payload.data
            )
            return {"message": "Memory entry recorded.", "id": memory_id}
        else:
            return {"message": "Memory entry ignored. Context does not match recording context."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/memory")
def get_memory(context: str):
    try:
        memories = db.get_memories(context)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/context/start")
def start_recording(context: str):
    try:
        db.set_active_context(context)
        return {"message": f"Now recording to context: {context}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/context/stop")
def stop_recording():
    try:
        db.clear_active_context()
        return {"message": "Recording stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/context/active")
def get_active_recording_context():
    try:
        active_context = db.get_active_context()
        return {"recording_context": active_context}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/contexts")
def get_all_contexts():
    try:
        contexts = db.get_all_contexts()
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

