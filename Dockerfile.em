# syntax=docker/dockerfile:1
FROM python:3.11-slim@sha256:2ec5a4a5c3e919570f57675471f081d6299668d909feabd8d4803c6c61af666c

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install eM (enhanced memory) and FastAPI
RUN pip install --no-cache-dir "mem0ai" fastapi uvicorn[standard] pydantic

# Copy sidecar app
COPY sidecar/ ./sidecar/

EXPOSE 7070

CMD ["uvicorn", "sidecar.main:app", "--host", "0.0.0.0", "--port", "7070"]
