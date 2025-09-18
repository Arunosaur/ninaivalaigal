FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir "psycopg[binary]" sqlalchemy alembic fastapi "uvicorn[standard]" httpx PyJWT email-validator python-multipart bcrypt psutil && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server/ ./server/
COPY frontend/ ./frontend/

# Set Python path and working directory
ENV PYTHONPATH=/app
WORKDIR /app/server

# Create non-root user for security
RUN useradd --system --no-create-home --shell /bin/false apiuser && \
    chown -R apiuser:apiuser /app

USER apiuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start command with conditional reload
CMD ["bash", "-c", "exec uvicorn main:app --host 0.0.0.0 --port 8000 $([ \"${API_RELOAD:-false}\" = \"true\" ] && echo --reload)"]
