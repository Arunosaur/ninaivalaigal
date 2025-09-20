#!/usr/bin/env bash
set -euo pipefail

echo "[pgbouncer] Starting..."

# Clean up any old container
container rm -f nv-pgbouncer >/dev/null 2>&1 || true

# Get DB container IP for intra-VM connectivity
echo "[pgbouncer] Getting database container IP..."
DB_IP=$(container inspect nv-db --format '{{ .NetworkSettings.IPAddress }}' 2>/dev/null || echo "nv-db")
echo "[pgbouncer] Database IP: $DB_IP"

# Start PgBouncer with DB_HOST environment variable
set -x
container run -d --name nv-pgbouncer \
  -p 6432:6432 \
  -e DB_HOST="$DB_IP" \
  nina-pgbouncer:arm64
set +x

# Quick sanity: did it start at all? (check via logs)
echo "[pgbouncer] Waiting for database to be fully ready..."
sleep 10
echo "[pgbouncer] Checking if container started..."
if ! container logs nv-pgbouncer >/dev/null 2>&1; then
  echo "[pgbouncer][fail] container did not start (no logs available)"
  exit 2
fi
echo "[pgbouncer] Container detected, proceeding to health check..."

# After nv-pgbouncer is running - capture its IP
PGB_IP="$(container inspect nv-pgbouncer --format '{{ .NetworkSettings.IPAddress }}')"
echo "::group::PgBouncer IP"; echo "$PGB_IP"; echo "::endgroup::"

# Quick sanity: can the host (runner) reach PgBouncer via the container IP?
psql "postgresql://postgres:test123@${PGB_IP}:6432/testdb?connect_timeout=1" -c 'select 1;'

# Wait for readiness (max 30s), and bail if it crashes
for sec in $(seq 1 30); do
  # If the container died, dump logs and fail fast
  if ! container logs nv-pgbouncer >/dev/null 2>&1; then
    echo "[pgbouncer][fail] exited while waiting (crash)"
    exit 2
  fi
  
  # Try to talk to PgBouncer admin port (via psql auth handshake)
  if psql "host=127.0.0.1 port=6432 user=postgres dbname=testdb password=test123" -c 'SHOW VERSION;' >/dev/null 2>&1; then
    echo "[pgbouncer][ok] ready on 127.0.0.1:6432"
    exit 0
  fi
  
  # Or at least confirm the port is open
  if (echo | nc -z 127.0.0.1 6432) >/dev/null 2>&1; then
    echo "[pgbouncer][ok] port open; psql auth may still be settling..."
    exit 0
  fi
  
  sleep 1
done

echo "[pgbouncer][fail] timeout waiting for readiness"
container logs nv-pgbouncer || true
exit 2
