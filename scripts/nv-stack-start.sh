#!/usr/bin/env bash
# Orchestrate ninaivalaigal stack (DB -> PgBouncer -> API) on Mac Studio via Apple `container`

set -euo pipefail

# flags
DB_ONLY=false
SKIP_API=false
SKIP_PGB=false
SKIP_MEM0=false
MEM0_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-only) DB_ONLY=true ;;
    --skip-api) SKIP_API=true ;;
    --skip-pgbouncer|--skip-pgb) SKIP_PGB=true ;;
    --skip-mem0) SKIP_MEM0=true ;;
    --mem0-only) MEM0_ONLY=true; SKIP_API=true ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SCRIPTS="${ROOT}/scripts"

log(){ printf "\033[1;36m[stack]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

need container
need nc
need bash
command -v psql >/dev/null 2>&1 || true
command -v curl >/dev/null 2>&1 || true

# Resolve host IP (LAN / Tailscale). You can override via POSTGRES_HOST env.
HOST_IP_DEFAULT="$(ipconfig getifaddr en0 2>/dev/null || true)"
if [[ -z "${POSTGRES_HOST:-}" ]]; then
  export POSTGRES_HOST="${HOST_IP_DEFAULT:-127.0.0.1}"
fi

log "Using POSTGRES_HOST=${POSTGRES_HOST}"

# 1) DB
log "Starting DB…"
bash "${SCRIPTS}/nv-db-start.sh"

# stop early if db-only
if $DB_ONLY; then
  log "DB only requested. Done."
  exit 0
fi

# 2) PgBouncer
if ! $SKIP_PGB; then
  log "Starting PgBouncer…"
  bash "${SCRIPTS}/nv-pgbouncer-start.sh"
else
  log "Skipping PgBouncer per flag."
fi

# 3) Mem0 (if http provider or explicitly requested)
if ! $SKIP_MEM0 && [[ "${MEMORY_PROVIDER:-}" == "http" || "$MEM0_ONLY" == "true" ]]; then
  log "Starting Mem0 sidecar…"
  if [[ -x "${SCRIPTS}/nv-mem0-start.sh" ]]; then
    bash "${SCRIPTS}/nv-mem0-start.sh"
  else
    log "nv-mem0-start.sh not found; ensure mem0 is running at ${MEMORY_HTTP_BASE:-http://127.0.0.1:7070}"
  fi
elif $SKIP_MEM0; then
  log "Skipping Mem0 per flag."
elif [[ "${MEMORY_PROVIDER:-}" != "http" ]]; then
  log "Skipping Mem0 (MEMORY_PROVIDER=${MEMORY_PROVIDER:-native})"
fi

# stop early if mem0-only
if $MEM0_ONLY; then
  log "Mem0-only requested. Done."
  exit 0
fi

# 4) API
if ! $SKIP_API; then
  log "Starting API…"
  # ensure API can reach host PgBouncer/DB; pass explicit host ip
  POSTGRES_HOST="${POSTGRES_HOST}" bash "${SCRIPTS}/nv-api-start.sh"
else
  log "Skipping API per flag."
fi

log "Stack start complete."
bash "${SCRIPTS}/nv-stack-status.sh" || true
