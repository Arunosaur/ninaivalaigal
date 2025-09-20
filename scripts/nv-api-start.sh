#!/usr/bin/env bash
set -euo pipefail

echo "[api] Starting nv-api…"

# ---- Config (override via env if you want) -------------------------------
IMAGE="${IMAGE:-nina-api:arm64}"          # make sure this image is built/tagged
NAME="${NAME:-nv-api}"
HOST_HTTP_PORT="${HOST_HTTP_PORT:-13370}" # host port for the API
CONTAINER_HTTP_PORT="${CONTAINER_HTTP_PORT:-8000}"   # port the app listens on
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-test123}"
DB_NAME="${DB_NAME:-testdb}"
PGBOUNCER_HOST="${PGBOUNCER_HOST:-127.0.0.1}"
PGBOUNCER_PORT="${PGBOUNCER_PORT:-6432}"
DB_FALLBACK_HOST="${DB_FALLBACK_HOST:-127.0.0.1}"
DB_FALLBACK_PORT="${DB_FALLBACK_PORT:-5433}"
READY_PATH="${READY_PATH:-/health}"       # nv-api exposes /health
READY_TIMEOUT="${READY_TIMEOUT:-45}"      # seconds
# -------------------------------------------------------------------------

# Get PgBouncer container IP for intra-VM connectivity
echo "[api] Getting PgBouncer container IP..."
# Wait for PgBouncer container to be ready
sleep 2

# Get PgBouncer container IP using Apple Container CLI compatible method
PGB_IP=$(container inspect nv-pgbouncer | jq -r '.[0].NetworkSettings.IPAddress')
echo "[api] PgBouncer IP: $PGB_IP"

# Set both environment variables to be extra safe
DBURL="postgresql://postgres:test123@${PGB_IP}:6432/testdb"

echo "[api] Using PgBouncer at ${PGB_IP}:6432"

# Clean any old container
container rm -f "$NAME" >/dev/null 2>&1 || true

# Start the API
set -x
container run -d --name "$NAME" \
  -p "${HOST_HTTP_PORT}:${CONTAINER_HTTP_PORT}" \
  -e NINAIVALAIGAL_DATABASE_URL="${DBURL}" \
  -e DATABASE_URL="${DBURL}" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \
  "$IMAGE"
set +x

# Quick sanity: did it start at all? (check via logs)
sleep 2
if ! container logs "$NAME" >/dev/null 2>&1; then
  echo "[api][fail] container did not start (no logs available)"
  exit 2
fi

# Show exactly what the API container sees
container exec nv-api sh -lc 'echo "DB_URL=$NINAIVALAIGAL_DATABASE_URL"; env | grep "NINAIVALAIGAL_DATABASE_URL\|DATABASE_URL"'

# Try a live connection from inside the API container to prove routing
container exec nv-api sh -lc "python -c <<'PY'
import os, psycopg2
dsn = os.getenv('NINAIVALAIGAL_DATABASE_URL') or os.getenv('DATABASE_URL')
print('Connecting to:', dsn)
conn = psycopg2.connect(dsn)
cur = conn.cursor(); cur.execute('select version()'); print(cur.fetchone())
cur.close(); conn.close()
print('DB connectivity OK.')
PY"

# Wait for readiness on /health (or your READY_PATH)
API_URL="http://localhost:${HOST_HTTP_PORT}${READY_PATH}"

for sec in $(seq 1 "${READY_TIMEOUT}"); do
  # If the container died, show logs and bail
  if ! container logs "$NAME" >/dev/null 2>&1; then
    echo "[api][fail] container exited while waiting"
    exit 2
  fi

  # Consider 'healthy' when the endpoint returns 2xx
  if curl -fsS "$API_URL" >/dev/null 2>&1; then
    echo "[api][ok] ready at ${API_URL}"
    exit 0
  fi

  sleep 1
done

echo "[api][fail] timeout waiting for ${API_URL}"
container logs "$NAME" || true
exit 2
