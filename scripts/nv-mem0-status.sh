#!/usr/bin/env bash
set -euo pipefail
CONTAINER_NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
echo "[mem0] Checking status..."
container list | grep "$CONTAINER_NAME" || echo "Not running"
curl -sf http://127.0.0.1:${MEM0_PORT:-7070}/health || echo "Unhealthy"
