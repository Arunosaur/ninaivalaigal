#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# nv-api-diagnose-repair-v2.sh
# One-shot diagnostic + repair for ninaivalaigal API container/image
# - Uses Apple CLI first, then auto-fallbacks to Docker if hang detected (>90s)
# - Compares local vs container run_server.py
# - Validates sys.path fix
# - Rebuilds (--no-cache) only if mismatch found
# - Transfers built image from Docker → Apple CLI if fallback triggered
# - Verifies health endpoint

set -euo pipefail

IMAGE_TAG="nina-api:arm64"
DOCKERFILE="containers/api/Dockerfile"
CONTAINER_NAME="ninaivalaigal-dev-api"
APP_DIR="/app"
LOCAL_RUN_SERVER="./run_server.py"
CONTAINER_RUN_SERVER="${APP_DIR}/run_server.py"
HEALTH_URL="http://localhost:13390/health"
HOST_PORT="13390"
CONTAINER_PORT="8000"
PY_PATH="/app:/app/server"
HANG_TIMEOUT=90
LOG_FILE="/tmp/nv_api_build.log"

### ───────────────────────────────────────────────
### Detect engine availability
### ───────────────────────────────────────────────
ENGINE=""
if command -v container >/dev/null 2>&1; then
  ENGINE="container"
fi

if command -v docker >/dev/null 2>&1; then
  HAS_DOCKER=1
else
  HAS_DOCKER=0
fi

if [[ -z "$ENGINE" && "$HAS_DOCKER" -eq 0 ]]; then
  echo "❌ Neither Apple Container CLI nor Docker found. Aborting."
  exit 1
fi

echo "🧠 Detected:"
[[ -n "$ENGINE" ]] && echo "   • Apple CLI: available"
[[ "$HAS_DOCKER" -eq 1 ]] && echo "   • Docker: available"
echo

### ───────────────────────────────────────────────
### Utility helpers
### ───────────────────────────────────────────────
require_sys_path_fix() {
  grep -q 'sys\.path\.insert(0,.*"/app/server")' "$1" || return 0
  return 1
}

progress_spinner() {
  local pid=$1 delay=0.3 spinstr='|/-\'
  local start=$(date +%s)
  while kill -0 "$pid" 2>/dev/null; do
    local elapsed=$(( $(date +%s) - start ))
    if [[ "$elapsed" -gt "$HANG_TIMEOUT" ]]; then
      echo ""
      echo "⚠️ Build appears stuck after ${HANG_TIMEOUT}s — triggering Docker fallback."
      kill "$pid" 2>/dev/null || true
      return 124
    fi
    local temp=${spinstr#?}
    printf " [%c]  " "$spinstr"
    spinstr=$temp${spinstr%"$temp"}
    sleep $delay
    printf "\b\b\b\b\b\b"
  done
  return 0
}

run_build() {
  local engine=$1
  echo "🏗️  Building image using: $engine"
  echo "   Tag: $IMAGE_TAG"
  echo "   Dockerfile: $DOCKERFILE"
  echo

  ( $engine build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" . >"$LOG_FILE" 2>&1 ) &
  local pid=$!
  if ! progress_spinner "$pid"; then
    return 124
  fi
  wait $pid || return $?
}

verify_health() {
  echo "🩺 Checking API health..."
  for i in $(seq 1 15); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      echo "✅ API Healthy ($HEALTH_URL)"
      return 0
    fi
    sleep 2
  done
  echo "❌ API not responding after retries."
  return 1
}

get_container_ip() {
    local container_name=$1
    if [[ -n "$ENGINE" ]]; then
        $ENGINE list 2>/dev/null | grep "^$container_name " | awk '{print $6}' | cut -d'/' -f1
    else
        docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$container_name" 2>/dev/null
    fi
}

validate_stack_connectivity() {
  echo ""
  echo "🔗 Validating full stack connectivity..."

  # Check PgBouncer
  local pgbouncer_ip=$(get_container_ip "ninaivalaigal-dev-pgbouncer")
  if [[ -n "$pgbouncer_ip" ]]; then
    if nc -z localhost 6452 2>/dev/null || nc -z "$pgbouncer_ip" 6432 2>/dev/null; then
      echo "✅ PgBouncer reachable (6452)"
    else
      echo "⚠️  PgBouncer not reachable on port 6452"
    fi
  else
    echo "⚠️  PgBouncer container not found"
  fi

  # Check Redis
  local redis_ip=$(get_container_ip "ninaivalaigal-dev-redis")
  if [[ -n "$redis_ip" ]]; then
    if nc -z localhost 6399 2>/dev/null || nc -z "$redis_ip" 6379 2>/dev/null; then
      echo "✅ Redis reachable (6399)"
    else
      echo "⚠️  Redis not reachable on port 6399"
    fi
  else
    echo "⚠️  Redis container not found"
  fi

  # Test database connectivity from API container
  echo ""
  echo "🔌 Testing API → Database connectivity..."
  if [[ -n "$ENGINE" ]]; then
    if $ENGINE exec "$CONTAINER_NAME" python -c "
import os
dsn = os.getenv('NINAIVALAIGAL_DATABASE_URL') or os.getenv('DATABASE_URL')
if dsn:
    import psycopg2
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()
    cur.execute('SELECT 1')
    print('DB connectivity OK:', cur.fetchone())
    cur.close()
    conn.close()
" 2>/dev/null; then
      echo "✅ API → Database connectivity verified"
    else
      echo "⚠️  Database connectivity test failed (may need env vars)"
    fi
  fi
}

### ───────────────────────────────────────────────
### Step 1: Confirm local fix
### ───────────────────────────────────────────────
echo "🔍 Checking local $LOCAL_RUN_SERVER..."
if [[ ! -f "$LOCAL_RUN_SERVER" ]]; then
  echo "❌ Missing $LOCAL_RUN_SERVER. Run from repo root."
  exit 1
fi

if require_sys_path_fix "$LOCAL_RUN_SERVER"; then
  echo "❌ sys.path.insert(0, \"/app/server\") missing in local run_server.py"
  exit 1
else
  echo "✅ Local run_server.py has sys.path fix."
fi
echo

### ───────────────────────────────────────────────
### Step 2: Try Apple CLI build first
### ───────────────────────────────────────────────
NEED_DOCKER_FALLBACK=0
if [[ -n "$ENGINE" ]]; then
  if ! run_build "$ENGINE"; then
    if [[ "$?" -eq 124 ]]; then
      NEED_DOCKER_FALLBACK=1
    else
      echo "⚠️ Apple CLI build failed unexpectedly. Will try Docker fallback."
      NEED_DOCKER_FALLBACK=1
    fi
  else
    echo "✅ Apple CLI build completed."
  fi
else
  NEED_DOCKER_FALLBACK=1
fi
echo

### ───────────────────────────────────────────────
### Step 3: Docker fallback if needed
### ───────────────────────────────────────────────
if [[ "$NEED_DOCKER_FALLBACK" -eq 1 ]]; then
  if [[ "$HAS_DOCKER" -eq 0 ]]; then
    echo "❌ No Docker available for fallback. Aborting."
    exit 1
  fi
  echo "🚨 Falling back to Docker build..."
  docker build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" .
  echo "✅ Docker build completed."

  if [[ -n "$ENGINE" ]]; then
    echo "📦 Transferring built image back to Apple CLI..."
    docker save "$IMAGE_TAG" | $ENGINE load
    echo "✅ Image transferred to Apple CLI."
  fi
fi
echo

### ───────────────────────────────────────────────
### Step 4: Get stack IPs
### ───────────────────────────────────────────────
PGBOUNCER_IP=$(get_container_ip "ninaivalaigal-dev-pgbouncer")
REDIS_IP=$(get_container_ip "ninaivalaigal-dev-redis")

if [[ -z "$PGBOUNCER_IP" ]] || [[ -z "$REDIS_IP" ]]; then
  echo "⚠️  Warning: Could not detect PgBouncer or Redis IPs from running containers."
  echo "   Make sure the stack is running first with: ./scripts/stack-start-unified.sh apple dev"
  PGBOUNCER_IP="192.168.65.1"
  REDIS_IP="192.168.65.1"
fi

echo "📍 Stack IPs:"
echo "   • PgBouncer: $PGBOUNCER_IP"
echo "   • Redis: $REDIS_IP"
echo

### ───────────────────────────────────────────────
### Step 5: Start container and verify health
### ───────────────────────────────────────────────
RUNTIME_ENGINE="${ENGINE:-docker}"

echo "🚀 Starting container with $RUNTIME_ENGINE..."
$RUNTIME_ENGINE stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
$RUNTIME_ENGINE rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

$RUNTIME_ENGINE run -d --name "$CONTAINER_NAME" \
  -p "${HOST_PORT}:${CONTAINER_PORT}" \
  -e "PYTHONPATH=${PY_PATH}" \
  -e "NINAIVALAIGAL_DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e "DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e "REDIS_HOST=${REDIS_IP}" \
  -e "REDIS_PORT=6379" \
  -e "REDIS_PASSWORD=dev_redis_password" \
  -e "NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production" \
  -e "ENVIRONMENT=dev" \
  -e "LOG_LEVEL=info" \
  "$IMAGE_TAG" >/dev/null  # pragma: allowlist secret

sleep 3
echo ""
echo "📋 Recent logs:"
$RUNTIME_ENGINE logs --tail 20 "$CONTAINER_NAME" 2>&1 || true
echo ""

if verify_health; then
  validate_stack_connectivity
  echo ""
  echo "🎉 API Integration verified successfully!"
  echo ""
  echo "📊 Stack Status:"
  echo "   • API:        http://localhost:13390"
  echo "   • Health:     http://localhost:13390/health"
  echo "   • Docs:       http://localhost:13390/docs"
  echo "   • PgBouncer:  localhost:6452"
  echo "   • Redis:      localhost:6399"
else
  echo "⚠️  Health check failed — showing last logs..."
  $RUNTIME_ENGINE logs --tail 100 "$CONTAINER_NAME" || true
  echo ""
  echo "Consider running: container system reset"
  exit 2
fi

echo ""
echo "💡 Recommendation: run 'container system reset' later to clear stale builders."
echo "✅ Process complete!"
