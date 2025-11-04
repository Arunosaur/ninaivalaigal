# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libc6-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy shared contracts FIRST (SPEC-100 Task #79)
COPY shared/contracts /app/shared/contracts
RUN pip install --no-cache-dir -e /app/shared/contracts

COPY services/graph-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/graph-service/ /app/

ENV PYTHONUNBUFFERED=1
ENV SERVICE_ROLE=graph-service
ENV PORT=8000
ENV PYTHONPATH=/app:/app/shared/contracts

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["python", "main.py"]
