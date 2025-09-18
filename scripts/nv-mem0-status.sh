#!/usr/bin/env bash
set -euo pipefail
NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
PORT="${MEM0_PORT:-7070}"

if container list | awk '{print $NF}' | grep -qx "$NAME"; then
  echo "mem0: container running ($NAME)"
else
  echo "mem0: not running"
  exit 1
fi

if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "mem0: health OK at /health"
else
  echo "mem0: health check failed"
  exit 1
fi
