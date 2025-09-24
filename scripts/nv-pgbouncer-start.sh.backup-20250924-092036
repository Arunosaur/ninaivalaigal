#!/bin/bash
set -euo pipefail

PGBOUNCER_CONTAINER_NAME=nv-pgbouncer
PGBOUNCER_PORT=6432
PGBOUNCER_IMAGE=nina-pgbouncer:arm64

echo "=== Starting PgBouncer ==="

# Get database container IP for networking
echo "[pgbouncer] Getting database container IP..."
DB_IP=$(container inspect nv-db | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "[pgbouncer] Database IP: $DB_IP"

# Get current SCRAM password from database
echo "[pgbouncer] Getting SCRAM password from database..."
SCRAM_PASSWORD=$(container exec nv-db psql -U nina -d nina -t -c "SELECT rolpassword FROM pg_authid WHERE rolname = 'nina';" | tr -d ' ')
echo "[pgbouncer] SCRAM password retrieved"

# Start PgBouncer container
container run -d \
  --name "$PGBOUNCER_CONTAINER_NAME" \
  -p "$PGBOUNCER_PORT:6432" \
  -e DB_HOST="$DB_IP" \
  -e SCRAM_PASSWORD="$SCRAM_PASSWORD" \
  "$PGBOUNCER_IMAGE"

# Wait for container to start
timeout=60
while [ $timeout -gt 0 ]; do
  echo "[pgbouncer] Waiting for container to start..."
  sleep 2

  # Check if container is running using grep instead of --format
  if container inspect "$PGBOUNCER_CONTAINER_NAME" | grep -q '"status":"running"'; then
    echo "[pgbouncer] Container is running."
    break
  fi

  timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
  echo "PgBouncer start timed out"
  exit 1
fi

# Optional: Add health check here (e.g., ping localhost:6432 inside container)
echo "[pgbouncer] PgBouncer started successfully."
exit 0
