"""Gunicorn Configuration for Ninaivalaigal API
SPEC-107: Unified Runtime Parity & Deployment Standard
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"

# Worker processes
worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
loglevel = os.getenv("LOG_LEVEL", "info")

# Reload on code changes (development only)
reload = os.getenv("ENV") == "dev"
