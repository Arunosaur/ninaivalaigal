#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-nv-db}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
echo "Stopped and removed container: $NAME"
