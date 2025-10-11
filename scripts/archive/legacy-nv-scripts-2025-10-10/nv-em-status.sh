#!/usr/bin/env bash
# Check eM sidecar status
CONTAINER_NAME="${EM_CONTAINER_NAME:-nv-em}"
HOST_PORT="${EM_PORT:-7070}"

if container list | awk '{print $NF}' | grep -qx "$CONTAINER_NAME"; then
  echo "eM: container running ($CONTAINER_NAME)"
else
  echo "eM: not running"
  exit 1
fi

if curl -fsS "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; then
  echo "eM: health OK at /health"
else
  echo "eM: health check failed"
  exit 1
fi
