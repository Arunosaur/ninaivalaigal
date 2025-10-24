FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy shared contracts FIRST (SPEC-100 Task #79)
COPY shared/contracts /app/shared/contracts

# Install shared contracts package
RUN pip install --no-cache-dir -e /app/shared/contracts

# Copy requirements and install Python dependencies
COPY services/core-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (directly to /app, not ./core-api/)
COPY services/core-api/ .
COPY config/mem0.config.json .

# Copy graphops_client Python package
COPY python-clients/graphops/graphops_client /app/graphops_client

# Set Python path to include all modules
ENV PYTHONPATH=/app:/app/shared/contracts:/app/graphops_client

# Create non-root user
RUN useradd -m -u 1000 mem0user && chown -R mem0user:mem0user /app
USER mem0user

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
