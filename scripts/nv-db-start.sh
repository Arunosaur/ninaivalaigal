#!/usr/bin/env bash
# Start ninaivalaigal Postgres on Mac Studio via Apple Container CLI
# Fixed for actual Apple Container CLI syntax

set -euo pipefail

# -------- settings (env overrides allowed) --------
CONTAINER_NAME="${CONTAINER_NAME:-nv-db}"
IMAGE="${IMAGE:-pgvector/pgvector:pg15}"  # Use pgvector image by default
HOST_PORT="${HOST_PORT:-5433}"           # host -> container 5432
DB_NAME="${POSTGRES_DB:-nina}"
DB_USER="${POSTGRES_USER:-nina}"
DB_PASS="${POSTGRES_PASSWORD:-change_me_securely}"
DATA_DIR="${DB_VOLUME:-$HOME/ninaivalaigal/volumes/db}"  # Use home directory
WAIT_SEC="${WAIT_SEC:-90}"
# --------------------------------------------------

log()  { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

ensure_bin() {
  command -v "$1" >/dev/null 2>&1 || die "Missing '$1'. Install and retry."
}

port_in_use() {
  # returns 0 if in use
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  fi
}

maybe_pull() {
  # Pull image using Apple Container CLI syntax
  if container images list | grep -q "$(echo "$IMAGE" | sed 's/:.*//')" ; then
    log "Image cache present; skipping pull."
  else
    log "Pulling image: $IMAGE"
    container images pull "$IMAGE" || warn "Pull failed, will try to run anyway"
  fi
}

ensure_container_system() {
  if ! container system status >/dev/null 2>&1; then
    log "Starting container system…"
    container system start
  fi
}

ensure_volume() {
  if [ ! -d "$DATA_DIR" ]; then
    log "Creating data dir: $DATA_DIR"
    mkdir -p "$DATA_DIR"
    log "Created: $DATA_DIR"
  fi
}

stop_existing() {
  # Check if container exists using Apple Container CLI syntax
  if container list | grep -q "$CONTAINER_NAME"; then
    warn "Container '$CONTAINER_NAME' exists. Stopping & removing…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

run_db() {
  log "Starting Postgres container '$CONTAINER_NAME' on host port ${HOST_PORT}…"
  # Note: Volume mounting has permission issues, running without persistent volume for now
  container run --detach --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:5432" \
    --env "POSTGRES_USER=${DB_USER}" \
    --env "POSTGRES_PASSWORD=${DB_PASS}" \
    --env "POSTGRES_DB=${DB_NAME}" \
    "$IMAGE"
}

wait_ready() {
  log "Waiting for Postgres to accept connections (timeout ${WAIT_SEC}s)…"
  local t=0
  until container exec "$CONTAINER_NAME" \
           pg_isready -h 127.0.0.1 -p 5432 -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1
  do
    sleep 2
    t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 50 || true
      die "Postgres did not become ready within ${WAIT_SEC}s."
    fi
  done
  log "Postgres is ready."
}

ensure_pgvector() {
  log "Ensuring pgvector extension…"
  container exec "$CONTAINER_NAME" \
    psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
    -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null || warn "pgvector setup failed"
  log "pgvector extension checked."
}

connection_summary() {
  cat <<EOF

✅ Postgres + pgvector is up via Apple Container CLI.

Connect from this host:
  container exec ${CONTAINER_NAME} psql -U ${DB_USER} -d ${DB_NAME}

Use in apps:
  DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:${HOST_PORT}/${DB_NAME}

Container logs:
  container logs ${CONTAINER_NAME}

Stop:
  container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

EOF
}

main() {
  ensure_bin container
  ensure_container_system

  if port_in_use "$HOST_PORT"; then
    die "Host port ${HOST_PORT} is already in use. Choose another HOST_PORT or stop the conflicting service."
  fi

  ensure_volume
  maybe_pull
  stop_existing
  run_db
  wait_ready
  ensure_pgvector
  connection_summary
}

main "$@"
