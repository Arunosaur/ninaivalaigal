#!/usr/bin/env bash
set -euo pipefail

echo "[redis] Starting nv-redis…"

# Clean up any stopped Redis container first
container stop nv-redis >/dev/null 2>&1 || true
container delete nv-redis >/dev/null 2>&1 || true

# Start Redis container
container run -d --name nv-redis -p 6379:6379 \
  -e REDIS_PASSWORD=nina_redis_dev_password \
  -v nv_redis_data:/data \
  redis:7-alpine redis-server --requirepass nina_redis_dev_password --maxmemory 256mb --maxmemory-policy allkeys-lru

echo "[redis] Redis started successfully."

# Wait a moment for Redis to be ready
sleep 2

# Test Redis connectivity
if redis-cli -h localhost -p 6379 -a nina_redis_dev_password ping >/dev/null 2>&1; then
  echo "[redis][ok] Redis is responding to PING"
else
  echo "[redis][warning] Redis may not be fully ready yet"
fi
