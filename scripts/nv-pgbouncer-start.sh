#!/usr/bin/env bash
set -euo pipefail

: "${NV_PGBOUNCER_IMAGE:=nina-pgbouncer:arm64}"
: "${PGBOUNCER_PORT:=6432}"
: "${PG_PORT:=5433}"
: "${PG_USER:=postgres}"
: "${PG_PASSWORD:=test123}"
: "${PG_DB:=testdb}"
: "${GITHUB_WORKSPACE:=$(pwd)}"

CFG_DIR="$GITHUB_WORKSPACE/.runner/pgbouncer"
LOG_DIR="$GITHUB_WORKSPACE/.runner/logs"
mkdir -p "$CFG_DIR" "$LOG_DIR"

cat > "$CFG_DIR/pgbouncer.ini" <<'EOF'
[databases]
testdb = host=host.lima.internal port=5433 dbname=testdb user=postgres

[pgbouncer]
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile  = /var/run/pgbouncer/pgbouncer.pid
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = trust
admin_users = postgres
pool_mode = transaction
EOF
: > "$CFG_DIR/userlist.txt"

container run -d --name nv-pgbouncer \
  -p "${PGBOUNCER_PORT}:6432" \
  --volume "$CFG_DIR:/etc/pgbouncer" \
  --volume "$LOG_DIR:/var/log/pgbouncer" \
  "${NV_PGBOUNCER_IMAGE}"

# health
for i in $(seq 1 30); do
  if psql "postgresql://${PG_USER}:${PG_PASSWORD}@127.0.0.1:${PGBOUNCER_PORT}/${PG_DB}" -c 'SHOW VERSION;' >/dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done
echo "PgBouncer failed to become healthy" >&2
exit 1
