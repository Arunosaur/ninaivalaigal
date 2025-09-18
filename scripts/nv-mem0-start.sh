#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
IMAGE="${MEM0_IMAGE:-ninaivalaigal-mem0:latest}"
HOST_PORT="${MEM0_PORT:-7070}"

log() { echo "[mem0] $*"; }

if container list | grep -q "$CONTAINER_NAME"; then
  log "Stopping existing mem0 container..."
  container stop "$CONTAINER_NAME" || true
  container delete "$CONTAINER_NAME" || true
fi

log "Building mem0 sidecar image..."
container build -t "$IMAGE" -f Dockerfile.mem0 .

log "Starting mem0 sidecar..."
container run --detach --name "$CONTAINER_NAME" \
  --publish "${HOST_PORT}:7070" \
  "$IMAGE"

log "Mem0 sidecar running at http://127.0.0.1:${HOST_PORT}/health"
