import hashlib
import json
import os

from fastapi import APIRouter

router = APIRouter()

SECURITY_CONFIG = {
    "JWT_SECRET": os.getenv("JWT_SECRET", "dev-secret"),
    "UPLOAD_LIMIT": os.getenv("UPLOAD_LIMIT", "10MB"),
    "REDIS_URL": os.getenv("REDIS_URL", "memory://")
}

def compute_hash():
    return hashlib.sha256(json.dumps(SECURITY_CONFIG, sort_keys=True).encode()).hexdigest()

@router.get("/healthz/config")
async def health_config():
    return {"security_config_hash": compute_hash()}
