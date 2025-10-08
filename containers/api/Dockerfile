FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir "psycopg[binary]" sqlalchemy alembic fastapi "uvicorn[standard]" httpx PyJWT email-validator python-multipart bcrypt psutil prometheus-client uvloop httptools structlog && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/ ./server/
COPY frontend/ ./frontend/
COPY run_server.py ./
COPY eM.py ./
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Set Python path to include both /app and /app/server for imports
ENV PYTHONPATH=/app:/app/server

# Create non-root user for security
RUN useradd --system --no-create-home --shell /bin/false apiuser && \
    chown -R apiuser:apiuser /app

USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Use run_server.py for proper initialization (same as Docker)
CMD ["python", "run_server.py"]
