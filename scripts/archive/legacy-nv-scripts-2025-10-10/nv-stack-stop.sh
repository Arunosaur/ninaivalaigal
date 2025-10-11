#!/usr/bin/env bash
# Stop ninaivalaigal stack (API -> PgBouncer -> DB) to drain gracefully

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SCRIPTS="${ROOT}/scripts"

log(){ printf "\033[1;36m[stack]\033[0m %s\n" "$*"; }

# UI first (user-facing)
log "Stopping UI…"
bash "${SCRIPTS}/nv-ui-stop.sh" || true

# API next (drain)
log "Stopping API…"
bash "${SCRIPTS}/nv-api-stop.sh" || true

# mem0 next
log "Stopping mem0…"
bash "${SCRIPTS}/nv-mem0-stop.sh" || true

# PgBouncer
log "Stopping PgBouncer…"
bash "${SCRIPTS}/nv-pgbouncer-stop.sh" || true

# Redis (SPEC-033)
log "Stopping Redis…"
container stop nv-redis >/dev/null 2>&1 || true
container delete nv-redis >/dev/null 2>&1 || true

# DB last
log "Stopping DB…"
bash "${SCRIPTS}/nv-db-stop.sh" || {
  container stop nv-db >/dev/null 2>&1 || true
  container delete nv-db >/dev/null 2>&1 || true
}

log "Stack stop complete."
