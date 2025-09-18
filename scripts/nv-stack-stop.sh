#!/usr/bin/env bash
# Stop ninaivalaigal stack (API -> PgBouncer -> DB) to drain gracefully

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SCRIPTS="${ROOT}/scripts"

log(){ printf "\033[1;36m[stack]\033[0m %s\n" "$*"; }

# Stop API first
log "Stopping API…"
bash "${SCRIPTS}/nv-api-stop.sh" || true

# Then Mem0 (if running)
log "Stopping Mem0…"
if [[ -x "${SCRIPTS}/nv-mem0-stop.sh" ]]; then
  bash "${SCRIPTS}/nv-mem0-stop.sh" || true
else
  container stop nv-mem0 >/dev/null 2>&1 || true
  container delete nv-mem0 >/dev/null 2>&1 || true
fi

# Then PgBouncer
log "Stopping PgBouncer…"
bash "${SCRIPTS}/nv-pgbouncer-stop.sh" || true

# Finally DB
log "Stopping DB…"
bash "${SCRIPTS}/nv-db-stop.sh" || {
  # fallback if you only have nv-db-start.sh today
  container stop nv-db >/dev/null 2>&1 || true
  container delete nv-db >/dev/null 2>&1 || true
}

log "Stack stop complete."
