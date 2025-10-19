# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Admin/Vendor Service Dockerfile - SPEC-100 Compliant
# Handles vendor administration and staff management

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY services/admin-vendor-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory
COPY shared/ /app/shared/

# Copy service code
COPY services/admin-vendor-service/ /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_ROLE=admin-vendor
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run the service
CMD ["python", "main.py"]
