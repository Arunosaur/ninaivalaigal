# run_server.py - Hardened Uvicorn configuration for production stability
import os
import sys

import structlog
import uvicorn

# Ensure current directory and server directory are on sys.path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)
sys.path.insert(0, "/app/server")  # Absolute container path for module imports
sys.path.insert(0, os.path.join(app_dir, "server"))  # Fallback for local development

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

if __name__ == "__main__":
    logger.info("Starting API server with hardened Uvicorn config")

    # Determine workers based on environment
    # Dev/Test: 1 worker for stability
    # Production: 2-4 workers for concurrency
    environment = os.getenv("ENVIRONMENT", "development")
    workers = 1 if environment in ["development", "test"] else 2

    logger.info(f"Environment: {environment}, Workers: {workers}")

    uvicorn.run(
        "server.main:app",  # explicit import path
        host="0.0.0.0",  # internal container port (map via docker-compose)
        port=8000,
        workers=workers,  # 1 for dev/test, 2 for production
        loop="uvloop",  # faster async loop
        http="httptools",  # robust HTTP parser
        lifespan="on",  # ensure startup/shutdown events run
        timeout_keep_alive=30,  # prevent premature connection drops
        log_level="info",
        reload=False,  # keep false for container builds
    )
