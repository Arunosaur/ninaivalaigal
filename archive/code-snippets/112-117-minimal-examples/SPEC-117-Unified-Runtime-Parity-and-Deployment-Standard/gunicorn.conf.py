"""Gunicorn configuration for SPEC-117 runtime parity."""

# gunicorn.conf.py
bind = "0.0.0.0:8000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 2
graceful_timeout = 30
timeout = 60
accesslog = "-"
errorlog = "-"
