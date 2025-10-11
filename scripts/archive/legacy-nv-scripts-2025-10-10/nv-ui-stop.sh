#!/usr/bin/env bash
set -euo pipefail
NAME="${UI_CONTAINER_NAME:-nv-ui}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
echo "Stopped and removed $NAME"
