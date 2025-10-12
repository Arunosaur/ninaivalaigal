#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# v3.1: adds Docker-daemon detection, BuildKit disable, live build output

set -euo pipefail
export DOCKER_BUILDKIT=0   # always use stable legacy builder

IMAGE_TAG="nina-api:arm64"
DOCKERFILE="containers/api/Dockerfile"
CONTAINER_NAME="ninaivalaigal-dev-api"
APP_DIR="/app"
CONTAINER_RUN_SERVER="${APP_DIR}/run_server.py"
LOCAL_RUN_SERVER="./run_server.py"
PY_PATH="/app:/app/server"
HEALTH_URL="http://localhost:13390/health"
PGBOUNCER_PORT=6452
REDIS_PORT=6399
LOG_TAIL=120

# ---------- sanity checks ----------
echo "🔍 Checking Docker daemon..."
if ! timeout 5 docker version >/dev/null 2>&1; then
  echo "❌ Docker daemon unresponsive. Please run:"
  echo "   sudo pkill -9 -f docker"
  echo "   sudo rm -f /var/run/docker.sock"
  echo "   open /Applications/Docker.app"
  echo "   Then wait 30s and rerun this script."
  exit 1
fi
echo "✅ Docker daemon ready."
echo

# ---------- verify local fix ----------
if [[ ! -f "$LOCAL_RUN_SERVER" ]]; then
  echo "❌ $LOCAL_RUN_SERVER not found (run from repo root)."
  exit 1
fi
if ! grep -q 'sys\.path\.insert(0,.*"/app/server")' "$LOCAL_RUN_SERVER"; then
  echo "❌ Local run_server.py missing sys.path.insert fix."
  exit 1
fi
echo "✅ Local run_server.py has sys.path fix."
echo

# ---------- build ----------
echo "🏗️  Building image (legacy builder, live logs)..."
docker build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" . || {
  echo "❌ Docker build failed."; exit 1;
}
echo "✅ Build complete."
echo

echo "🔎 Verifying image contains sys.path fix..."
docker run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'" || {
  echo "❌ Image verification failed."; exit 1;
}
echo "✅ Image verification passed."
echo

# ---------- run ----------
docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

docker run -d --name "$CONTAINER_NAME" \
  -p 13390:8000 \
  -e PYTHONPATH="$PY_PATH" \
  -e "NINAIVALAIGAL_DATABASE_URL=postgresql://nina:dev_password_change_in_production@127.0.0.1:${PGBOUNCER_PORT}/ninaivalaigal_dev" \
  -e "DATABASE_URL=postgresql://nina:dev_password_change_in_production@127.0.0.1:${PGBOUNCER_PORT}/ninaivalaigal_dev" \
  -e "REDIS_HOST=127.0.0.1" \
  -e "REDIS_PORT=${REDIS_PORT}" \
  -e "REDIS_PASSWORD=dev_redis_password" \
  -e "NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production" \
  -e "ENVIRONMENT=dev" \
  -e "LOG_LEVEL=info" \
  "$IMAGE_TAG" >/dev/null  # pragma: allowlist secret

sleep 3
echo "📋 Initial logs:"
docker logs --tail 20 "$CONTAINER_NAME" || true
echo

# ---------- connectivity ----------
check_port() {
  if nc -z localhost "$1" >/dev/null 2>&1; then
    echo "✅ Port $1 ($2) reachable"
    return 0
  else
    echo "⚠️  Port $1 ($2) unreachable - is stack running?"
    return 1
  fi
}
echo "🔌 Checking stack connectivity..."
check_port "$PGBOUNCER_PORT" "PgBouncer"
check_port "$REDIS_PORT" "Redis"
echo

# ---------- health ----------
echo "🩺 Checking API health..."
for i in {1..15}; do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    echo "✅ API healthy ($HEALTH_URL)"
    echo ""
    echo "🎉 Full API integration complete!"
    echo "   • Build:      Docker ✅"
    echo "   • Runtime:    Docker ✅"
    echo "   • Health:     http://localhost:13390/health ✅"
    echo "   • API Docs:   http://localhost:13390/docs ✅"
    echo "   • PgBouncer:  localhost:6452 ✅"
    echo "   • Redis:      localhost:6399 ✅"
    exit 0
  fi
  sleep 2
done

echo "⚠️  API health failed — showing last logs:"
docker logs --tail "$LOG_TAIL" "$CONTAINER_NAME"
echo ""
echo "💡 Debug suggestions:"
echo "   1. Check if PgBouncer/Redis are running"
echo "   2. Review logs above for import errors"
echo "   3. Test manually: curl -v $HEALTH_URL"
exit 2
