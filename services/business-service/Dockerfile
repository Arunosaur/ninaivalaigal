# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Business Service Dockerfile - SPEC-100 Compliant
# Handles billing, analytics, and business intelligence

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared directory
COPY ../../shared /app/shared

# Copy service code
COPY . /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVICE_ROLE=business-service
ENV PORT=8002

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health')"

# Run the service
CMD ["python", "main.py"]
