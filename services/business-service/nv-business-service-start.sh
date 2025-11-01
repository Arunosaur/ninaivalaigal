#!/usr/bin/env bash
# Backwards-compatible wrapper to the canonical start script.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

exec "$PROJECT_ROOT/scripts/nv-business-service-start.sh" "$@"
