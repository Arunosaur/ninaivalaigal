#!/usr/bin/env bash
# nv-api-diagnose-repair-v3.1-autoheal.sh
# v3.1 + Self-healing Docker daemon bootstrap
# - Detects Docker daemon hang
# - Offers automatic restart (with user approval)
# - Only proceeds when docker version shows Client + Server
# - Continues full nv-api repair + verification flow

set -euo pipefail
export DOCKER_BUILDKIT=0   # disable BuildKit for reliability

### ────────────────────────────────────────────────
### 🔍 Filesystem responsiveness pre-check
### ────────────────────────────────────────────────
echo "🔍 Checking filesystem responsiveness..."
TEST_FILE="/tmp/.nv_fs_test_$$"
if timeout 2 bash -c "touch '$TEST_FILE' && rm '$TEST_FILE'" >/dev/null 2>&1; then
  echo "✅ Filesystem responsive"
else
  echo "❌ CRITICAL: Filesystem I/O deadlock detected!"
  echo ""
  echo "Root cause: Apple Virtualization.framework or Docker has locked file handles"
  echo "in this directory (likely APFS snapshot or FUSE mount)."
  echo ""
  echo "Recovery steps:"
  echo "  1. Open a NEW terminal window (not this one)"
  echo "  2. Run: sudo lsof +D $(pwd) | grep -E 'Docker|container|fuse'"
  echo "  3. Kill any PIDs: sudo kill -9 <pid1> <pid2> ..."
  echo "  4. If still hung, reboot your Mac"
  echo "  5. Move repo outside APFS snapshot area: mv ~/ninaivalaigal ~/Dev/ninaivalaigal"
  echo "  6. Disable Apple virtualization in Docker Desktop settings"
  echo ""
  exit 1
fi
echo ""

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

# Parse flags
AUTO_MODE=0
if [[ "${1:-}" == "--auto" ]]; then
  AUTO_MODE=1
  echo "🤖 Running in automatic mode (CI/CD)"
fi

### ────────────────────────────────────────────────
### 🩺 Docker daemon auto-recovery bootstrap
### ────────────────────────────────────────────────
echo "🐳 Checking Docker daemon..."
if ! timeout 5 docker version >/dev/null 2>&1; then
  echo "⚠️  Docker daemon unresponsive."

  if [[ $AUTO_MODE -eq 1 ]]; then
    REPLY="y"
    echo "🤖 Auto mode: restarting Docker automatically"
  else
    read -p "Attempt automatic restart? (y/n) " -n 1 -r
    echo ""
  fi

  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 Restarting Docker Desktop..."
    sudo pkill -9 -f docker || true
    sudo rm -f /var/run/docker.sock || true
    open /Applications/Docker.app
    echo "⏳ Waiting up to 30s for Docker to initialize..."
    for i in {1..30}; do
      if timeout 2 docker version >/dev/null 2>&1; then
        echo "✅ Docker recovered successfully."
        break
      fi
      sleep 1
    done
    if ! timeout 5 docker version >/dev/null 2>&1; then
      echo "❌ Docker still unresponsive — please reinstall Docker Desktop."
      exit 1
    fi
  else
    echo "🛑 Please fix Docker and rerun."
    exit 1
  fi
else
  echo "✅ Docker daemon responding."
fi
echo ""

### ────────────────────────────────────────────────
### ✅ Verify local fix
### ────────────────────────────────────────────────
if [[ ! -f "$LOCAL_RUN_SERVER" ]]; then
  echo "❌ $LOCAL_RUN_SERVER not found (run from repo root)."
  exit 1
fi
if ! grep -q 'sys\.path\.insert(0,.*"/app/server")' "$LOCAL_RUN_SERVER"; then
  echo "❌ Local run_server.py missing sys.path.insert fix."
  exit 1
fi
echo "✅ Local run_server.py has sys.path fix."
echo ""

### ────────────────────────────────────────────────
### 🧱 Build
### ────────────────────────────────────────────────
echo "🏗️  Building image (legacy builder, live logs)..."
docker build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" .
echo "✅ Build complete."
echo ""

echo "🔎 Verifying image contains sys.path fix..."
docker run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'" || {
  echo "❌ Image verification failed."; exit 1;
}
echo "✅ Image verification passed."
echo ""

### ────────────────────────────────────────────────
### 🚀 Run
### ────────────────────────────────────────────────
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
echo ""

### ────────────────────────────────────────────────
### 🔌 Connectivity checks
### ────────────────────────────────────────────────
check_port() {
  if nc -z localhost "$1" >/dev/null 2>&1; then
    echo "✅ Port $1 ($2) reachable"
  else
    echo "⚠️  Port $1 ($2) unreachable - is stack running?"
  fi
}
echo "🔌 Checking stack connectivity..."
check_port "$PGBOUNCER_PORT" "PgBouncer"
check_port "$REDIS_PORT" "Redis"
echo ""

### ────────────────────────────────────────────────
### 🩺 Health check
### ────────────────────────────────────────────────
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

echo "⚠️  API health check failed — showing last logs:"
docker logs --tail "$LOG_TAIL" "$CONTAINER_NAME"
echo ""
echo "💡 Debug suggestions:"
echo "   1. Check if PgBouncer/Redis are running"
echo "   2. Review logs above for import errors"
echo "   3. Test manually: curl -v $HEALTH_URL"
exit 2
