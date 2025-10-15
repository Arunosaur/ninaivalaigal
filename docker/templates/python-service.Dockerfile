# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

# Multi-stage Dockerfile for Python microservices
# Used by: core-api, memory-service, graph-ai-service
#
# Build: docker build -f docker/templates/python-service.Dockerfile -t service-name:tag .
# Run: docker run -p 8000:8000 service-name:tag

ARG PYTHON_VERSION=3.11
ARG ALPINE_VERSION=3.18

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} AS builder

LABEL stage=builder

WORKDIR /build

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

# Metadata
LABEL maintainer="platform@medhasys.com" \
      version="1.0.0" \
      description="Python microservice base image" \
      org.opencontainers.image.source="https://github.com/Arunosaur/ninaivalaigal"

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache \
    postgresql-libs \
    libffi \
    openssl \
    ca-certificates

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser ./server /app/server
COPY --chown=appuser:appuser ./shared /app/shared
COPY --chown=appuser:appuser ./python-clients /app/python-clients

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
