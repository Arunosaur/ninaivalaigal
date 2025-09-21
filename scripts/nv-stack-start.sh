#!/usr/bin/env bash
# Orchestrate ninaivalaigal stack (DB -> PgBouncer -> API) on Mac Studio via Apple `container`

set -euo pipefail

DB_ONLY=false
SKIP_API=false
SKIP_PGB=false
WITH_MEM0=false
SKIP_MEM0=false
SKIP_UI=false
WITH_UI=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --db-only) DB_ONLY=true ;;
    --skip-api) SKIP_API=true ;;
    --skip-pgbouncer|--skip-pgb) SKIP_PGB=true ;;
    --with-mem0) WITH_MEM0=true ;;
    --skip-mem0) SKIP_MEM0=true ;;
    --skip-ui) SKIP_UI=true ;;
    --with-ui) WITH_UI=true ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SCRIPTS="${ROOT}/scripts"

log(){ printf "\033[1;36m[stack]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

command -v container >/dev/null 2>&1 || die "Missing 'container' CLI"

# Resolve host IP (LAN/Tailscale) for container->host reachability if not provided
HOST_IP_DEFAULT="$(ipconfig getifaddr en0 2>/dev/null || true)"
export POSTGRES_HOST="${POSTGRES_HOST:-${HOST_IP_DEFAULT:-127.0.0.1}}"
log "Using POSTGRES_HOST=${POSTGRES_HOST}"

# 1) DB
log "Starting DB…"
bash "${SCRIPTS}/nv-db-start.sh"

# stop early if db-only
if $DB_ONLY; then
  log "DB only requested. Done."
  exit 0
fi

# 2) Redis (SPEC-033: Critical for performance and intelligence features)
log "Starting Redis…"
if container list | grep -q "nv-redis.*running"; then
  log "Redis already running, skipping start."
else
  # Clean up any stopped Redis container first
  container stop nv-redis >/dev/null 2>&1 || true
  container delete nv-redis >/dev/null 2>&1 || true

  container run -d --name nv-redis -p 6379:6379 \
    -e REDIS_PASSWORD=nina_redis_dev_password \
    -v nv_redis_data:/data \
    redis:7-alpine redis-server --requirepass nina_redis_dev_password --maxmemory 256mb --maxmemory-policy allkeys-lru
  log "Redis started successfully."
fi

# 3) PgBouncer
if ! $SKIP_PGB; then
  log "Starting PgBouncer…"
  bash "${SCRIPTS}/nv-pgbouncer-start.sh"
else
  log "Skipping PgBouncer per flag."
fi

# Decide whether mem0 should be started:
# - Start if user passed --with-mem0
# - Or if MEMORY_PROVIDER=http (default path for your choice)
START_MEM0=false
if $WITH_MEM0; then
  START_MEM0=true
elif [[ "${MEMORY_PROVIDER:-}" == "http" && $SKIP_MEM0 == false ]]; then
  START_MEM0=true
fi

# 4) mem0 (if requested)
if $START_MEM0; then
  log "Starting mem0 sidecar…"
  bash "${SCRIPTS}/nv-mem0-start.sh"
else
  log "Skipping mem0 (provider=${MEMORY_PROVIDER:-unset}, flags: with=${WITH_MEM0}, skip=${SKIP_MEM0})."
fi

# 5) API
if ! $SKIP_API; then
  log "Starting API…"
  # ensure API can reach host PgBouncer/DB; pass explicit host ip
  POSTGRES_HOST="${POSTGRES_HOST}" bash "${SCRIPTS}/nv-api-start.sh"
else
  log "Skipping API per flag."
fi

# 6) UI (if requested or in production mode)
START_UI=false
if $WITH_UI; then
  START_UI=true
elif [[ "${NODE_ENV:-}" == "production" && $SKIP_UI == false ]]; then
  START_UI=true
fi

if $START_UI; then
  log "Starting UI…"
  bash "${SCRIPTS}/nv-ui-start.sh"
else
  log "Skipping UI (flags: with=${WITH_UI}, skip=${SKIP_UI})."
fi

log "Stack start complete."
bash "${SCRIPTS}/nv-stack-status.sh" || true
