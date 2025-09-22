#!/usr/bin/env bash
# Validation wrapper: start DB → run tests → stop DB
# Usage: ./nv-test-db.sh [pytest-args...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log() { printf "\033[1;34m[test]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

cleanup() {
  log "Cleaning up database..."
  "$SCRIPT_DIR/nv-db-stop.sh" >/dev/null 2>&1 || true
}

trap cleanup EXIT

main() {
  log "Starting database for testing..."
  "$SCRIPT_DIR/nv-db-start.sh"

  log "Waiting for database to be fully ready..."
  sleep 5

  log "Running tests..."
  cd "$PROJECT_ROOT"

  # Set up environment for tests
  export PYTHONPATH="$PROJECT_ROOT/server:$PYTHONPATH"
  export DATABASE_URL="postgresql://nina:change_me_securely@localhost:5433/nina"

  # Run pytest with any passed arguments
  if [ $# -eq 0 ]; then
    # Default test suite
    pytest -v tests/ || die "Tests failed"
  else
    # Run with custom arguments
    pytest "$@" || die "Tests failed"
  fi

  log "Tests completed successfully!"
}

main "$@"
