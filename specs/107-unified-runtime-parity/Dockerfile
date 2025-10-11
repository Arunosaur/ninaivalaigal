# Multi-stage Dockerfile for Ninaivalaigal API
# SPEC-107: Unified Runtime Parity & Deployment Standard

FROM python:3.11-slim as builder

WORKDIR /app

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip wheel -r requirements.txt -w /wheels

FROM python:3.11-slim

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels

# Install from wheels
RUN pip install /wheels/*

# Copy application code
COPY . .

# Run with gunicorn + uvicorn workers
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn.conf.py"]
