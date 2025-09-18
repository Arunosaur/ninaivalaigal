#!/usr/bin/env bash
# Start ninaivalaigal PgBouncer on Mac Studio via Apple Container CLI
# Connects to existing PostgreSQL database container

set -euo pipefail

# -------- settings (env overrides allowed) --------
CONTAINER_NAME="${PGBOUNCER_CONTAINER_NAME:-nv-pgbouncer}"
IMAGE="${PGBOUNCER_IMAGE:-pgbouncer/pgbouncer:latest}"
HOST_PORT="${PGBOUNCER_PORT:-6432}"        # host -> container 5432
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5433}"
DB_NAME="${POSTGRES_DB:-nina}"
DB_USER="${POSTGRES_USER:-nina}"
DB_PASS="${POSTGRES_PASSWORD:-change_me_securely}"
WAIT_SEC="${WAIT_SEC:-30}"
# --------------------------------------------------

log()  { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

ensure_bin() {
  command -v "$1" >/dev/null 2>&1 || die "Missing '$1'. Install and retry."
}

port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  fi
}

maybe_pull() {
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

check_database() {
  log "Checking database connectivity..."
  if ! nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1; then
    die "Database not reachable at $DB_HOST:$DB_PORT. Start database first with: ./nv-db-start.sh"
  fi
  log "Database is reachable at $DB_HOST:$DB_PORT"
}

stop_existing() {
  if container list | grep -q "$CONTAINER_NAME"; then
    warn "Container '$CONTAINER_NAME' exists. Stopping & removing…"
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

create_pgbouncer_config() {
  local config_dir="/tmp/pgbouncer-$CONTAINER_NAME"
  mkdir -p "$config_dir"
  
  # Create pgbouncer.ini
  cat > "$config_dir/pgbouncer.ini" <<EOF
[databases]
$DB_NAME = host=$DB_HOST port=$DB_PORT dbname=$DB_NAME

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 5432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
reserve_pool_size = 5
reserve_pool_timeout = 5
max_db_connections = 50
max_user_connections = 50
server_reset_query = DISCARD ALL
ignore_startup_parameters = extra_float_digits
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
EOF

  # Create userlist.txt with MD5 password
  # Note: In production, use proper password hashing
  cat > "$config_dir/userlist.txt" <<EOF
"$DB_USER" "md5$(echo -n "${DB_PASS}${DB_USER}" | md5sum | cut -d' ' -f1)"
EOF

  echo "$config_dir"
}

run_pgbouncer() {
  local config_dir
  config_dir=$(create_pgbouncer_config)
  
  log "Starting PgBouncer container '$CONTAINER_NAME' on host port ${HOST_PORT}…"
  container run --detach --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:5432" \
    --volume "${config_dir}:/etc/pgbouncer" \
    --env "DATABASES_HOST=${DB_HOST}" \
    --env "DATABASES_PORT=${DB_PORT}" \
    --env "DATABASES_NAME=${DB_NAME}" \
    --env "DATABASES_USER=${DB_USER}" \
    --env "DATABASES_PASSWORD=${DB_PASS}" \
    "$IMAGE"
}

wait_ready() {
  log "Waiting for PgBouncer to accept connections (timeout ${WAIT_SEC}s)…"
  local t=0
  until nc -z 127.0.0.1 "$HOST_PORT" >/dev/null 2>&1; do
    sleep 2
    t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 20 || true
      die "PgBouncer did not become ready within ${WAIT_SEC}s."
    fi
  done
  log "PgBouncer is ready."
}

test_connection() {
  log "Testing PgBouncer connection..."
  # Test via container exec if psql is available in the image
  if container exec "$CONTAINER_NAME" which psql >/dev/null 2>&1; then
    container exec "$CONTAINER_NAME" psql -h 127.0.0.1 -p 5432 -U "$DB_USER" -d "$DB_NAME" -c "SELECT 'PgBouncer connection test successful';" >/dev/null
    log "PgBouncer connection test successful"
  else
    log "PgBouncer is listening (psql not available in container for testing)"
  fi
}

connection_summary() {
  cat <<EOF

✅ PgBouncer is up via Apple Container CLI.

Connect through PgBouncer:
  psql "postgresql://${DB_USER}:${DB_PASS}@localhost:${HOST_PORT}/${DB_NAME}"

Use in apps (via PgBouncer):
  DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:${HOST_PORT}/${DB_NAME}

Direct database (bypass PgBouncer):
  DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:${DB_PORT}/${DB_NAME}

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
    die "Host port ${HOST_PORT} is already in use. Choose another PGBOUNCER_PORT or stop the conflicting service."
  fi

  check_database
  maybe_pull
  stop_existing
  run_pgbouncer
  wait_ready
  test_connection
  connection_summary
}

main "$@"
