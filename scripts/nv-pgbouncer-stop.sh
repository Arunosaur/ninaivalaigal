#!/usr/bin/env bash
set -euo pipefail
NAME="${1:-nv-pgbouncer}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
# Cleanup config directory
rm -rf "/tmp/pgbouncer-$NAME" 2>/dev/null || true
echo "Stopped and removed PgBouncer container: $NAME"
