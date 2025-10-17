FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/core-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities first (needed by the service)
COPY shared/ /app/shared/

# Copy service code
COPY services/core-api/ /app/

# Set Python path to include shared
ENV PYTHONPATH=/app:/app/shared

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run the application
CMD ["python", "main_with_auth.py"]
