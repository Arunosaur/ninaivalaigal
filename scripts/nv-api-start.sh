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

# Decide DB endpoint: prefer PgBouncer if reachable
DB_HOST="$DB_FALLBACK_HOST"
DB_PORT="$DB_FALLBACK_PORT"
if (echo | nc -z "$PGBOUNCER_HOST" "$PGBOUNCER_PORT") >/dev/null 2>&1; then
  DB_HOST="$PGBOUNCER_HOST"
  DB_PORT="$PGBOUNCER_PORT"
  echo "[api] Using PgBouncer at ${DB_HOST}:${DB_PORT}"
else
  echo "[api] PgBouncer not reachable; using direct DB at ${DB_FALLBACK_HOST}:${DB_FALLBACK_PORT}"
fi

# Compose DATABASE_URL (adjust if your app expects a different scheme)
DATABASE_URL="postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

# Clean any old container
container rm -f "$NAME" >/dev/null 2>&1 || true

# Start the API
set -x
container run -d --name "$NAME" \
  -p "${HOST_HTTP_PORT}:${CONTAINER_HTTP_PORT}" \
  -e DATABASE_URL="${DATABASE_URL}" \
  "$IMAGE"
set +x

# Quick sanity: did it start at all? (check via logs)
sleep 2
if ! container logs "$NAME" >/dev/null 2>&1; then
  echo "[api][fail] container did not start (no logs available)"
  exit 2
fi

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
