# syntax=docker/dockerfile:1
# SPDX-License-Identifier: Elastic-2.0
# Business Service Dockerfile - SPEC-100 compliant container image

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for build/runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared contracts first for better caching
COPY shared/contracts /app/shared/contracts
RUN pip install --no-cache-dir -e /app/shared/contracts

# Install service dependencies
COPY services/business-service/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared libs and service code
COPY shared/ /app/shared/
COPY services/business-service/ /app/

# Create non-root user aligned with containerization standard
RUN addgroup --system nina && adduser --system --ingroup nina nina

ENV SERVICE_ROLE=business-service \
    PORT=13391 \
    PYTHONPATH=/app:/app/shared/contracts

# Expose canonical port from config/ports.nv.yaml
EXPOSE 13391

# Health check using Python stdlib (no extra deps required)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:13391/health')"

USER nina

CMD ["python", "main.py"]
