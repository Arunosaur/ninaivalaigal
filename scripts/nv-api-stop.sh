#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-nv-api}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
# Cleanup any built images (optional - comment out to keep images cached)
# container images delete "ninaivalaigal-api:latest" >/dev/null 2>&1 || true
echo "Stopped and removed API container: $NAME"
