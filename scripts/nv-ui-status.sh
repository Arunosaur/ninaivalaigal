#!/usr/bin/env bash
set -euo pipefail
NAME="${UI_CONTAINER_NAME:-nv-ui}"
PORT="${UI_PORT:-8080}"

if container list | awk '{print $NF}' | grep -qx "$NAME"; then
  echo "ui: container running ($NAME)"
else
  echo "ui: not running"
  exit 1
fi

if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then
  echo "ui: health OK at /health"
else
  echo "ui: health check failed"
  exit 1
fi
