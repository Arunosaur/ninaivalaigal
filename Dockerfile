FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY server/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install PostgreSQL adapter
RUN pip install psycopg2-binary

# Copy application code
COPY . /app

# Expose port
EXPOSE 13370

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:13370/health || exit 1

# Start command
CMD ["python", "server/main.py"]
