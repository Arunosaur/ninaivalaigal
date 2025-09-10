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
        # Always save the memory to the specified context
        # The shell wrapper already ensures it only sends when context is active
        memory_id = db.add_memory(
            context=entry.context,
            memory_type=entry.payload.type,
            source=entry.payload.source,
            data=entry.payload.data
        )
        return {"message": "Memory entry recorded.", "id": memory_id}
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
def stop_recording(context: str = None):
    try:
        # TODO: Add user authentication to get actual user_id
        if context:
            # Stop specific context
            db.stop_specific_context(context, user_id=None)
            return {"message": f"Recording stopped for context: {context}"}
        else:
            # Stop only the currently active context, not all contexts
            active_context = db.get_active_context(user_id=None)
            if active_context:
                db.stop_specific_context(active_context, user_id=None)
                return {"message": f"Recording stopped for active context: {active_context}"}
            else:
                return {"message": "No active context to stop."}
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

@app.delete("/context/{context_name}")
def delete_context(context_name: str):
    try:
        # TODO: Add user authentication to get actual user_id
        db.delete_context(context_name, user_id=None)
        return {"message": f"Context '{context_name}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

