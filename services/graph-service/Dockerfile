# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Graph/AI Service Dockerfile - SPEC-100 + SPEC-062 Compliant
# Handles graph intelligence, AI reasoning, and heavy compute

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/graph-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory
COPY shared/ /app/shared/

# Copy service code
COPY services/graph-service/ /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_ROLE=graph-service
ENV PORT=8000

# GraphOps defaults (SPEC-062)
ENV GRAPH_DB_HOST=localhost
ENV GRAPH_DB_PORT=5433
ENV GRAPH_DB_NAME=graph_db
ENV GRAPH_DB_USER=graphops
ENV GRAPH_DB_PASSWORD=graphops_password
ENV GRAPH_REDIS_HOST=localhost
ENV GRAPH_REDIS_PORT=6380

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the service
CMD ["python", "main.py"]
