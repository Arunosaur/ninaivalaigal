#!/usr/bin/env bash
set -euo pipefail

echo "[pgbouncer] Starting..."

# Clean up any old container
container rm -f nv-pgbouncer >/dev/null 2>&1 || true

# Start (detached)
container run -d --name nv-pgbouncer \
  -p 6432:6432 \
  nina-pgbouncer:arm64

# Quick sanity: did it start at all? (check via logs)
sleep 2
echo "[pgbouncer] Checking if container started..."
if ! container logs nv-pgbouncer >/dev/null 2>&1; then
  echo "[pgbouncer][fail] container did not start (no logs available)"
  exit 2
fi
echo "[pgbouncer] Container detected, proceeding to health check..."

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
