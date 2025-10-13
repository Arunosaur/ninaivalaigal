#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# nv-api-diagnose-repair.sh
# One-shot diagnostic + repair for ninaivalaigal API container/image
# - Compares local vs container run_server.py
# - Rebuilds (--no-cache) ONLY if mismatch found
# - Validates `sys.path.insert(0, "/app/server")`
# - Relaunches API with proper PYTHONPATH=/app:/app/server
# - Tests health endpoint
# - Shows logs if it fails

set -euo pipefail

### ─────────────────────────────────────────────────────────────────────────────
### Config (adjust if you need different ports/tags)
### ─────────────────────────────────────────────────────────────────────────────
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
# Optional: if you keep env in a file e.g. containers/api/dev.env, set ENV_FILE path (leave blank to skip)
ENV_FILE=""

### ─────────────────────────────────────────────────────────────────────────────
### Pick container engine: Apple "container" CLI preferred, fallback to docker
### ─────────────────────────────────────────────────────────────────────────────
ENGINE=""
if command -v container >/dev/null 2>&1; then
  ENGINE="container"
elif command -v docker >/dev/null 2>&1; then
  ENGINE="docker"
else
  echo "❌ Neither 'container' (Apple Container CLI) nor 'docker' found in PATH."
  exit 1
fi

echo "🛠️  Using engine: $ENGINE"
echo "📦 Image: $IMAGE_TAG"
echo "🧾 Dockerfile: $DOCKERFILE"
echo "🚢 Container: $CONTAINER_NAME"
echo

### ─────────────────────────────────────────────────────────────────────────────
### Helpers
### ─────────────────────────────────────────────────────────────────────────────
exists_image() {
  $ENGINE images --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | grep -q "^${IMAGE_TAG}$" || \
  $ENGINE image list 2>/dev/null | grep -q "^${IMAGE_TAG}" || return 1
}

running_container() {
  $ENGINE ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$" || \
  $ENGINE list 2>/dev/null | grep -q "^${CONTAINER_NAME}.*running" || return 1
}

stopped_container() {
  $ENGINE ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$" || \
  $ENGINE list -a 2>/dev/null | grep -q "^${CONTAINER_NAME}" || return 1
}

require_sys_path_fix() {
  # returns 0 if the file DOES NOT contain the required insert line (thus fix required)
  # returns 1 if present (no fix required)
  grep -q 'sys\.path\.insert(0,.*"/app/server")' "$1" || return 0
  return 1
}

### ─────────────────────────────────────────────────────────────────────────────
### 1) Validate local run_server.py exists and contains the fix
### ─────────────────────────────────────────────────────────────────────────────
if [[ ! -f "$LOCAL_RUN_SERVER" ]]; then
  echo "❌ Local $LOCAL_RUN_SERVER not found. Run from repo root or adjust LOCAL_RUN_SERVER."
  exit 1
fi

echo "🔎 Checking local $LOCAL_RUN_SERVER for sys.path fix…"
if require_sys_path_fix "$LOCAL_RUN_SERVER"; then
  echo "❌ Local $LOCAL_RUN_SERVER is missing: sys.path.insert(0, \"/app/server\")"
  echo "   Please add the line before running this script."
  exit 1
else
  echo "✅ Local run_server.py includes sys.path fix."
fi
echo

### ─────────────────────────────────────────────────────────────────────────────
### 2) Inspect current container/image run_server.py (if available)
### ─────────────────────────────────────────────────────────────────────────────
NEED_REBUILD=0
CONTEXT="(no container/image yet)"

if running_container; then
  echo "🔎 Reading run_server.py from running container…"
  if ! $ENGINE exec "$CONTAINER_NAME" sh -c "test -f '$CONTAINER_RUN_SERVER'" 2>/dev/null; then
    echo "⚠️  $CONTAINER_RUN_SERVER not found in running container. Will rebuild."
    NEED_REBUILD=1
  else
    # Compare content checksums (fast) and ensure fix present
    CONTAINER_SHA="$($ENGINE exec "$CONTAINER_NAME" sh -c "sha256sum '$CONTAINER_RUN_SERVER' 2>/dev/null | awk '{print \$1}'" || true)"
    LOCAL_SHA="$(sha256sum "$LOCAL_RUN_SERVER" | awk '{print $1}')"
    CONTEXT="(running container)"

    if [[ -z "$CONTAINER_SHA" ]]; then
      echo "⚠️  Could not compute container SHA. Will rebuild."
      NEED_REBUILD=1
    elif [[ "$CONTAINER_SHA" != "$LOCAL_SHA" ]]; then
      echo "❗ Mismatch: container run_server.py != local. Rebuild required."
      NEED_REBUILD=1
    else
      echo "✅ Container run_server.py matches local file."
      # Still validate the sys.path within the container file
      if ! $ENGINE exec "$CONTAINER_NAME" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'" 2>/dev/null; then
        echo "❌ Container file lacks sys.path fix. Rebuild required."
        NEED_REBUILD=1
      fi
    fi
  fi

elif exists_image; then
  echo "🔎 No running container. Checking image contents…"
  CONTEXT="(image check)"
  # Run a throwaway container to read file
  if $ENGINE run --rm "$IMAGE_TAG" sh -c "test -f '$CONTAINER_RUN_SERVER'" 2>/dev/null; then
    IMAGE_SHA="$($ENGINE run --rm "$IMAGE_TAG" sh -c "sha256sum '$CONTAINER_RUN_SERVER' | awk '{print \$1}'")"
    LOCAL_SHA="$(sha256sum "$LOCAL_RUN_SERVER" | awk '{print $1}')"
    if [[ "$IMAGE_SHA" != "$LOCAL_SHA" ]]; then
      echo "❗ Mismatch: image run_server.py != local. Rebuild required."
      NEED_REBUILD=1
    else
      echo "✅ Image run_server.py matches local."
      if ! $ENGINE run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'" 2>/dev/null; then
        echo "❌ Image file lacks sys.path fix. Rebuild required."
        NEED_REBUILD=1
      fi
    fi
  else
    echo "⚠️  $CONTAINER_RUN_SERVER not found in image. Rebuild required."
    NEED_REBUILD=1
  fi
else
  echo "ℹ️  Image not present yet. First build is required."
  NEED_REBUILD=1
fi
echo

### ─────────────────────────────────────────────────────────────────────────────
### 3) Rebuild image (no-cache) ONLY if needed
### ─────────────────────────────────────────────────────────────────────────────
if [[ "$NEED_REBUILD" -eq 1 ]]; then
  echo "🏗️  Rebuilding image (no cache) because of $CONTEXT discrepancy…"
  echo "⏰ This may take 2-3 minutes..."
  $ENGINE build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" .
  echo "✅ Rebuild complete."

  echo "🔎 Verifying image now contains sys.path fix…"
  if ! $ENGINE run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'" 2>/dev/null; then
    echo "❌ After rebuild, the image still lacks the sys.path fix. Please check COPY step in $DOCKERFILE."
    exit 1
  fi
  echo "✅ Image verified with sys.path fix."
else
  echo "⏭️  Rebuild not required. Container/image already matches local with fix."
fi
echo

### ─────────────────────────────────────────────────────────────────────────────
### 4) Get PgBouncer and Redis IPs from running stack
### ─────────────────────────────────────────────────────────────────────────────
get_container_ip() {
    local container_name=$1
    $ENGINE list 2>/dev/null | grep "^$container_name " | awk '{print $6}' | cut -d'/' -f1
}

PGBOUNCER_IP=$(get_container_ip "ninaivalaigal-dev-pgbouncer")
REDIS_IP=$(get_container_ip "ninaivalaigal-dev-redis")

if [[ -z "$PGBOUNCER_IP" ]] || [[ -z "$REDIS_IP" ]]; then
  echo "⚠️  Warning: Could not detect PgBouncer or Redis IPs from running containers."
  echo "   Make sure the stack is running first with: ./scripts/stack-start-unified.sh apple dev"
  echo "   Continuing anyway with placeholder values..."
  PGBOUNCER_IP="192.168.65.1"
  REDIS_IP="192.168.65.1"
fi

echo "📍 PgBouncer IP: $PGBOUNCER_IP"
echo "📍 Redis IP: $REDIS_IP"
echo

### ─────────────────────────────────────────────────────────────────────────────
### 5) Relaunch API with PYTHONPATH=/app:/app/server
### ─────────────────────────────────────────────────────────────────────────────
echo "🧹 Cleaning old container (if any)…"
if running_container; then
  $ENGINE stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi
if stopped_container; then
  $ENGINE rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

RUN_CMD=("$ENGINE" run -d
  "--name" "$CONTAINER_NAME"
  "-p" "${HOST_PORT}:${CONTAINER_PORT}"
  "-e" "PYTHONPATH=${PY_PATH}"
  "-e" "NINAIVALAIGAL_DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
  "-e" "DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev"  # pragma: allowlist secret
  "-e" "REDIS_HOST=${REDIS_IP}"
  "-e" "REDIS_PORT=6379"
  "-e" "REDIS_PASSWORD=dev_redis_password"  # pragma: allowlist secret
  "-e" "NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production"  # pragma: allowlist secret
  "-e" "ENVIRONMENT=dev"
  "-e" "LOG_LEVEL=info"
  "-e" "ENABLE_DEBUG=true"
)

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
  RUN_CMD+=("--env-file" "$ENV_FILE")
fi

RUN_CMD+=("$IMAGE_TAG")

echo "▶️  Starting container with PYTHONPATH=${PY_PATH} …"
"${RUN_CMD[@]}" >/dev/null

echo "⏳ Waiting for startup…"
sleep 5

### ─────────────────────────────────────────────────────────────────────────────
### 6) Health probe (up to ~30s)
### ─────────────────────────────────────────────────────────────────────────────
echo "🩺 Probing health: $HEALTH_URL"
ATTEMPTS=15
OK=0
for i in $(seq 1 "$ATTEMPTS"); do
  if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
    OK=1
    break
  fi
  sleep 2
done

if [[ "$OK" -eq 1 ]]; then
  echo "✅ Health check passed: $HEALTH_URL"
  echo ""
  echo "🎉 API integration complete!"
  echo "   API:        http://localhost:13390"
  echo "   Health:     http://localhost:13390/health"
  echo "   Docs:       http://localhost:13390/docs"
  exit 0
fi

### ─────────────────────────────────────────────────────────────────────────────
### 7) Failure: show diagnostics
### ─────────────────────────────────────────────────────────────────────────────
echo "❌ Health check failed."
echo
echo "─── Container status ───"
$ENGINE list -a | grep "${CONTAINER_NAME}" || $ENGINE ps -a --filter "name=${CONTAINER_NAME}"
echo
echo "─── Last 100 logs ───"
$ENGINE logs --tail 100 "$CONTAINER_NAME" 2>&1 || true
echo
echo "─── Container run_server.py (head -20) ───"
$ENGINE exec "$CONTAINER_NAME" sh -c "head -20 '$CONTAINER_RUN_SERVER' || echo 'missing'" 2>&1 || true
echo
echo "Hint: if the app needs DB/Redis env vars, set ENV_FILE in this script."
exit 2
