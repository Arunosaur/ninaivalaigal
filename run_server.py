# run_server.py
import os
import sys

import structlog
import uvicorn
from fastapi import FastAPI

# Ensure current directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ✅ Configure structlog properly
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

# ✅ Import the FastAPI app safely
try:
    from main import app
except ImportError as e:
    logger.error("Failed to import app", error=str(e))
    sys.exit(1)

if not isinstance(app, FastAPI):
    logger.error("Imported app is not a FastAPI instance")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting Uvicorn server", host="0.0.0.0", port=8000)
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        )
    except Exception as e:
        logger.error("Uvicorn failed to start", error=str(e))
        sys.exit(1)
