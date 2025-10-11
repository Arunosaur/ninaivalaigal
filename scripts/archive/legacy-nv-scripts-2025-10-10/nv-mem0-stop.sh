#!/usr/bin/env bash
set -euo pipefail
CONTAINER_NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
container stop "$CONTAINER_NAME" || true
container delete "$CONTAINER_NAME" || true
echo "[mem0] Stopped $CONTAINER_NAME"
