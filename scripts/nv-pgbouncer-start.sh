#!/usr/bin/env bash
# Start ninaivalaigal PgBouncer on Mac Studio via Apple Container CLI

set -euo pipefail

# -------- settings (env overrides allowed) --------
CONTAINER_NAME="${PGBOUNCER_CONTAINER_NAME:-nv-pgbouncer}"
IMAGE="${PGBOUNCER_IMAGE:-bitnami/pgbouncer:1.22.1}"
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

need() { command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
  else
    nc -z 127.0.0.1 "$1" >/dev/null 2>&1
  fi
}

maybe_pull() {
  if ! container image list | grep -q "$IMAGE"; then
    log "Pulling PgBouncer image: $IMAGE"
    container pull "$IMAGE" || die "Failed to pull $IMAGE"
  else
    log "Image $IMAGE already available"
  fi
}


ensure_container_system() {
  container system status >/dev/null 2>&1 || container system start
}

check_database() {
  log "Checking database reachability at $DB_HOST:$DB_PORT..."
  nc -z "$DB_HOST" "$DB_PORT" >/dev/null 2>&1 || \
    die "DB not reachable. Start DB first: ./scripts/nv-db-start.sh"
}

stop_existing() {
  # exact match on NAME column
  if container list | awk 'NR>1 {print $1}' | grep -qx "$CONTAINER_NAME"; then
    warn "Container '$CONTAINER_NAME' exists. Stopping & removing..."
    container stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    container delete "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi
}

# portable md5(password+username) for PgBouncer userlist
pgb_md5() {
  local s="$1"
  if command -v md5 >/dev/null 2>&1; then
    md5 -q <<<"$s"
  elif command -v openssl >/dev/null 2>&1; then
    printf "%s" "$s" | openssl md5 | awk '{print $2}'
  else
    die "Need 'md5' (macOS) or 'openssl' for PgBouncer MD5."
  fi
}

create_pgbouncer_config() {
  local config_dir="/tmp/pgbouncer-$CONTAINER_NAME"
  mkdir -p "$config_dir"

  # Create pgbouncer.ini
  cat > "$config_dir/pgbouncer.ini" <<EOF
[databases]
$DB_NAME = host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password=$DB_PASS

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

  # Create userlist.txt with MD5(password+username)
  local hex; hex="$(pgb_md5 "${DB_PASS}${DB_USER}")"
  printf '"%s" "md5%s"\n' "$DB_USER" "$hex" > "$config_dir/userlist.txt"

  echo "$config_dir"
}

run_pgbouncer() {
  local cfg; cfg="$(create_pgbouncer_config)"
  log "Starting PgBouncer '$CONTAINER_NAME' on host port ${HOST_PORT}..."
  container run --detach --name "$CONTAINER_NAME" \
    --publish "${HOST_PORT}:5432" \
    --volume "${cfg}:/opt/bitnami/pgbouncer/conf" \
    "$IMAGE"
}

wait_ready() {
  log "Waiting for PgBouncer (timeout ${WAIT_SEC}s)..."
  local t=0
  until nc -z 127.0.0.1 "$HOST_PORT" >/dev/null 2>&1; do
    sleep 2; t=$((t+2))
    if [ "$t" -ge "$WAIT_SEC" ]; then
      container logs "$CONTAINER_NAME" | tail -n 40 || true
      die "PgBouncer not ready in ${WAIT_SEC}s."
    fi
  done
  log "PgBouncer is ready."
}

test_connection() {
  log "Testing PgBouncer auth..."
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="$DB_PASS" psql \
      "postgresql://$DB_USER@127.0.0.1:${HOST_PORT}/$DB_NAME" \
      -c "select 1" >/dev/null && log "Auth OK."
  else
    warn "psql not installed on host; skipped auth test."
  fi
}

summary() {
  cat <<EOF

✅ PgBouncer up via Apple 'container'.

Connect:
  psql "postgresql://${DB_USER}:${DB_PASS}@localhost:${HOST_PORT}/${DB_NAME}"

Apps:
  DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:${HOST_PORT}/${DB_NAME}

Direct DB:
  DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:${DB_PORT}/${DB_NAME}

Logs:
  container logs -f ${CONTAINER_NAME}

Stop:
  container stop ${CONTAINER_NAME} && container delete ${CONTAINER_NAME}

EOF
}

main() {
  need container
  need nc
  ensure_container_system

  port_in_use "$HOST_PORT" && die "Host port ${HOST_PORT} is busy."
  check_database
  maybe_pull
  stop_existing
  run_pgbouncer
  wait_ready
  test_connection
  summary
}
main "$@"
