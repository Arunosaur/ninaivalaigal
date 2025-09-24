#!/usr/bin/env bash
# Stop eM sidecar
set -euo pipefail

CONTAINER_NAME="${EM_CONTAINER_NAME:-nv-em}"

log(){ printf "\033[1;35m[eM]\033[0m %s\n" "$*"; }

container stop "$CONTAINER_NAME" || true
container delete "$CONTAINER_NAME" || true
log "Stopped $CONTAINER_NAME"
