#!/usr/bin/env bash
set -euo pipefail

# Use environment variables from GitHub Actions or defaults
: "${PGBOUNCER_IMAGE:=nina-pgbouncer:arm64}"
: "${PGBOUNCER_PORT:=6432}"
: "${POSTGRES_PORT:=5433}"
: "${POSTGRES_USER:=postgres}"
: "${POSTGRES_PASSWORD:=test123}"
: "${POSTGRES_DB:=testdb}"
: "${GITHUB_WORKSPACE:=$(pwd)}"

echo "[info] Starting PgBouncer with:"
echo "  Image: ${PGBOUNCER_IMAGE}"
echo "  Port: ${PGBOUNCER_PORT}"
echo "  DB: ${POSTGRES_USER}@localhost:${POSTGRES_PORT}/${POSTGRES_DB}"

CFG_DIR="$GITHUB_WORKSPACE/.runner/pgbouncer"
LOG_DIR="$GITHUB_WORKSPACE/.runner/logs"
mkdir -p "$CFG_DIR" "$LOG_DIR"

# Create PgBouncer configuration
cat > "$CFG_DIR/pgbouncer.ini" <<EOF
[databases]
* = host=host.lima.internal port=${POSTGRES_PORT} dbname=${POSTGRES_DB}

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = any
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
ignore_startup_parameters = extra_float_digits
EOF

# Create empty userlist (not needed with auth_type=trust)
: > "$CFG_DIR/userlist.txt"

echo "[info] Starting PgBouncer container..."
container run -d --name nv-pgbouncer \
  -p "${PGBOUNCER_PORT}:6432" \
  --volume "$CFG_DIR:/etc/pgbouncer" \
  --volume "$LOG_DIR:/var/log/pgbouncer" \
  "${PGBOUNCER_IMAGE}"

echo "[info] Waiting for PgBouncer to become healthy..."
for i in $(seq 1 30); do
  if psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@127.0.0.1:${PGBOUNCER_PORT}/${POSTGRES_DB}" -c 'SHOW VERSION;' >/dev/null 2>&1; then
    echo "[info] PgBouncer is healthy!"
    exit 0
  fi
  echo "[info] Attempt $i/30: PgBouncer not ready yet..."
  sleep 2
done

echo "[error] PgBouncer failed to become healthy after 60 seconds" >&2
echo "[error] Container logs:" >&2
container logs nv-pgbouncer || true
exit 1
