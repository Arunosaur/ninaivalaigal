#!/usr/bin/env bash
# Start ninaivalaigal FastAPI server on Mac Studio via Apple Container CLI
# Connects to existing database (prefer PgBouncer).

set -euo pipefail

# -------- settings (env overrides allowed) --------
CONTAINER_NAME="${API_CONTAINER_NAME:-nv-api}"
HOST_PORT="${API_PORT:-13370}"              # host -> container 8000
# IMPORTANT: DB_HOST should be your Mac Studio LAN/Tailscale IP or an alias that points to the host.
HOST_IP_DEFAULT="$(ipconfig getifaddr en0 2>/dev/null || true)"
DB_HOST="${POSTGRES_HOST:-${HOST_IP_DEFAULT:-127.0.0.1}}"
DB_PORT="${PGBOUNCER_PORT:-6432}"           # prefer PgBouncer; fall back to direct DB
DB_NAME="${POSTGRES_DB:-nina}"
DB_USER="${POSTGRES_USER:-nina}"
DB_PASS="${POSTGRES_PASSWORD:-change_me_securely}"
JWT_SECRET="${NINAIVALAIGAL_JWT_SECRET:-dev-secret-change-in-production}"
WAIT_SEC="${WAIT_SEC:-90}"
API_RELOAD="${API_RELOAD:-true}"            # set false in prod
# --------------------------------------------------

log()  { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need() { command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  fi
}

ensure_container_system() {
  container system status >/dev/null 2>&1 || container system start
}

stop_existing() {
  # Exact name match on the last column
  if container list | awk '{print $NF}' | grep -qx "$CONTAINER_NAME"; then
    warn "Container '$CONTAINER_NAME' exists. Stopping & removing…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

check_db() {
  log "Checking DB reachability (prefer PgBouncer ${DB_HOST}:${DB_PORT})…"
  if nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; then
    log "PgBouncer reachable."
  else
    local direct_port="${POSTGRES_PORT:-5433}"
    if nc -z "$DB_HOST" "$direct_port" >/dev/null 2>&1; then
      warn "PgBouncer not reachable; falling back to direct DB on ${direct_port}."
      DB_PORT="$direct_port"
    else
      die "DB not reachable at ${DB_HOST}:{${DB_PORT},${direct_port}}. Start DB/PgBouncer first."
    fi
  fi

  # If psql is available, do a real check
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="$DB_PASS" psql \
      "host=${DB_HOST} port=${DB_PORT} user=${DB_USER} dbname=${DB_NAME}" \
      -c "select 1" >/dev/null
  fi
}

prepare_context() {
  local ctx="/tmp/ninaivalaigal-api-$CONTAINER_NAME"
  rm -rf "$ctx" && mkdir -p "$ctx"

  [ -d "server" ] || die "Run from project root; 'server/' not found."
  cp -r server "$ctx/"

  # optional requirements
  [ -f "requirements.txt" ] && cp requirements.txt "$ctx/"

  # Dockerfile (installs curl for HEALTHCHECK)
  cat > "$ctx/Dockerfile" <<'EOF'
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt* ./
RUN pip install --no-cache-dir "psycopg[binary]" sqlalchemy alembic fastapi "uvicorn[standard]" httpx \
 && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

COPY server/ ./server/
ENV PYTHONPATH=/app/server

# health endpoint path must exist in your app
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# allow toggling reload via env
ENV API_RELOAD=${API_RELOAD:-false}
CMD ["bash","-lc","exec uvicorn server.main:app --host 0.0.0.0 --port 8000 $( [ \"$API_RELOAD\" = \"true\" ] && echo --reload )"]
EOF
  echo "$ctx"
}

build_image() {
  local ctx="$1"
  local tag="ninaivalaigal-api:latest"
  log "Building API image (${tag})…"
  container build -t "$tag" -f "$ctx/Dockerfile" "$ctx"
  echo "$tag"
}

run_api() {
  local ctx tag db_url
  ctx="$(prepare_context)"
  tag="$(build_image "$ctx")"
  db_url="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

  log "Starting API container '$CONTAINER_NAME' on ${HOST_PORT}…"
  container run --detach --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:8000" \
    --env "DATABASE_URL=${db_url}" \
    --env "NINAIVALAIGAL_JWT_SECRET=${JWT_SECRET}" \
    --env "API_RELOAD=${API_RELOAD}" \
    "$tag"

  rm -rf "$ctx"
}

migrate() {
  log "Running alembic migrations inside container…"
  # If your alembic lives in server/, this will work; adjust path if needed.
  container exec "$CONTAINER_NAME" bash -lc "alembic upgrade head" || \
    warn "alembic not available or not configured; skipped."
}

wait_ready() {
  log "Waiting for API health (timeout ${WAIT_SEC}s)…"
  local t=0
  until curl -fsS "http://127.0.0.1:${HOST_PORT}/health" >/dev/null 2>&1; do
    sleep 2; t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 60 || true
      die "API did not become ready within ${WAIT_SEC}s."
    fi
  done
  log "API is healthy."
}

summary() {
  cat <<EOF

✅ ninaivalaigal API is up.

Endpoints:
  Health:        http://localhost:${HOST_PORT}/health
  Docs:          http://localhost:${HOST_PORT}/docs

Runtime env:
  DATABASE_URL=postgresql://${DB_USER}:***@${DB_HOST}:${DB_PORT}/${DB_NAME}
  NINAIVALAIGAL_JWT_SECRET=***

Useful:
  container logs -f ${CONTAINER_NAME}
  container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

EOF
}

main() {
  need container
  need curl
  ensure_container_system

  port_in_use "$HOST_PORT" && die "Host port ${HOST_PORT} in use."
  stop_existing
  check_db
  run_api
  migrate
  wait_ready
  summary
}
main "$@"
