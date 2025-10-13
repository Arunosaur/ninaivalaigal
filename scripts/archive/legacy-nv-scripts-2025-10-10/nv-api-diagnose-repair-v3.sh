#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# nv-api-diagnose-repair-v3.sh
# Build (Docker by default) → optional image transfer → run → full-stack validation
# - Rebuilds ONLY if the image's /app/run_server.py mismatches local or lacks sys.path fix
# - Docker is the reliable builder; Apple CLI used only for runtime (optional)
# - Validates PgBouncer:6452, Redis:6399, API /health:13390
# - Prints focused logs on failure

set -euo pipefail

### ───────────────────────────── Config ─────────────────────────────
IMAGE_TAG="nina-api:arm64"
DOCKERFILE="containers/api/Dockerfile"
LOCAL_RUN_SERVER="./run_server.py"
APP_DIR="/app"
CONTAINER_RUN_SERVER="${APP_DIR}/run_server.py"

# Runtime preference: 1 = use Apple CLI for running (if available), 0 = run with Docker
PREFER_APPLE_RUNTIME=1

# Ports / health
HOST_PORT_API=13390
CONTAINER_PORT_API=8000
HEALTH_URL="http://localhost:${HOST_PORT_API}/health"
PGBOUNCER_HOST="127.0.0.1"; PGBOUNCER_PORT=6452
REDIS_HOST="127.0.0.1";     REDIS_PORT=6399

# Env
PY_PATH="/app:/app/server"
ENV_FILE=""   # e.g., containers/api/dev.env

CONTAINER_NAME="ninaivalaigal-dev-api"
LOG_TAIL=150

### ─────────────────────── Engine detection ────────────────────────
have() { command -v "$1" >/dev/null 2>&1; }

if ! have docker; then echo "❌ Docker not found. Please install/start Docker."; exit 1; fi
APPLE_CLI_AVAILABLE=0
if have container; then APPLE_CLI_AVAILABLE=1; fi

RUN_ENGINE="docker"
if [[ "$PREFER_APPLE_RUNTIME" -eq 1 && "$APPLE_CLI_AVAILABLE" -eq 1 ]]; then
  RUN_ENGINE="container"
fi

echo "🧠 Engines:"
echo "  • Docker (build): ✅"
echo "  • Apple CLI (runtime optional): $([[ $APPLE_CLI_AVAILABLE -eq 1 ]] && echo ✅ || echo ❌)"
echo "🚢 Runtime engine: $RUN_ENGINE"
echo

### ─────────────────────── Helper functions ────────────────────────
require_sys_path_fix_local() {
  grep -q 'sys\.path\.insert(0,.*"/app/server")' "$LOCAL_RUN_SERVER"
}
docker_image_exists() {
  docker image ls --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_TAG}$"
}
image_has_fix_and_matches_local() {
  # returns 0 if image matches local and contains the fix
  local local_sha image_sha
  local_sha="$(sha256sum "$LOCAL_RUN_SERVER" | awk '{print $1}')"
  image_sha="$(docker run --rm "$IMAGE_TAG" sh -c "sha256sum '$CONTAINER_RUN_SERVER' 2>/dev/null | awk '{print \$1}'" || true)"
  [[ -n "$image_sha" && "$image_sha" == "$local_sha" ]] || return 1
  docker run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'"
}
stop_rm() {
  local eng=$1 name=$2
  $eng stop "$name" >/dev/null 2>&1 || true
  $eng rm   "$name" >/dev/null 2>&1 || true
}
tcp_check() {
  local host=$1 port=$2 label=$3 attempts=${4:-10}
  for i in $(seq 1 "$attempts"); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "✅ $label reachable at $host:$port"
      return 0
    fi
    sleep 1
  done
  echo "❌ $label not reachable at $host:$port"
  return 1
}
verify_health() {
  echo "🩺 Probing API: $HEALTH_URL"
  for i in $(seq 1 15); do
    if curl -fsS "$HEALTH_URL" >/dev/null 2>&1; then
      echo "✅ API healthy"
      return 0
    fi
    sleep 2
  done
  echo "❌ API health check failed"
  return 1
}

### ───────────────────────── Preflight ────────────────────────────
if [[ ! -f "$LOCAL_RUN_SERVER" ]]; then
  echo "❌ $LOCAL_RUN_SERVER not found (run from repo root or adjust path)."; exit 1
fi
if ! require_sys_path_fix_local; then
  echo "❌ Local run_server.py missing: sys.path.insert(0, \"/app/server\")"; exit 1
fi
echo "✅ Local run_server.py has sys.path fix."
echo

### ───────────────────────── Build (Docker) ────────────────────────
NEED_REBUILD=1
if docker_image_exists; then
  if image_has_fix_and_matches_local; then
    echo "⏭️  Rebuild not required (image matches local and has sys.path fix)."
    NEED_REBUILD=0
  else
    echo "🔁 Image mismatch or missing fix → rebuild needed."
  fi
else
  echo "ℹ️  Image not present → build required."
fi

if [[ "$NEED_REBUILD" -eq 1 ]]; then
  echo "🏗️  Building with Docker (no-cache)…"
  docker build --no-cache -t "$IMAGE_TAG" -f "$DOCKERFILE" .
  echo "✅ Docker build complete."
  echo "🔎 Verifying image contains sys.path fix…"
  docker run --rm "$IMAGE_TAG" sh -c "grep -q 'sys\.path\.insert(0,.*\"/app/server\")' '$CONTAINER_RUN_SERVER'"
  echo "✅ Verification passed."
fi
echo

### ───────────── Optional: transfer image → Apple CLI ─────────────
if [[ "$RUN_ENGINE" == "container" ]]; then
  echo "📦 Transferring image to Apple CLI runtime…"
  docker save "$IMAGE_TAG" | container load
  echo "✅ Image available for Apple CLI."
fi
echo

### ───────────────────────── Run container ────────────────────────
echo "🚀 Starting API with $RUN_ENGINE …"
stop_rm "$RUN_ENGINE" "$CONTAINER_NAME"

RUN_ARGS=("$RUN_ENGINE" run -d --name "$CONTAINER_NAME" \
  -p "${HOST_PORT_API}:${CONTAINER_PORT_API}" \
  -e "PYTHONPATH=${PY_PATH}" \
  -e "NINAIVALAIGAL_DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_HOST}:${PGBOUNCER_PORT}/ninaivalaigal_dev" \
  -e "DATABASE_URL=postgresql://nina:dev_password_change_in_production@${PGBOUNCER_HOST}:${PGBOUNCER_PORT}/ninaivalaigal_dev" \
  -e "REDIS_HOST=${REDIS_HOST}" \
  -e "REDIS_PORT=${REDIS_PORT}" \
  -e "REDIS_PASSWORD=dev_redis_password" \
  -e "NINAIVALAIGAL_JWT_SECRET=dev_jwt_secret_change_in_production" \
  -e "ENVIRONMENT=dev" \
  -e "LOG_LEVEL=info")

if [[ -n "$ENV_FILE" && -f "$ENV_FILE" ]]; then
  RUN_ARGS+=("--env-file" "$ENV_FILE")
fi
RUN_ARGS+=("$IMAGE_TAG")

"${RUN_ARGS[@]}" >/dev/null  # pragma: allowlist secret

sleep 3
$RUN_ENGINE logs --tail 25 "$CONTAINER_NAME" || true
echo

### ─────────────────── Connectivity validation ────────────────────
echo "🔌 Validating dependent services…"
tcp_check "$PGBOUNCER_HOST" "$PGBOUNCER_PORT" "PgBouncer"
tcp_check "$REDIS_HOST"     "$REDIS_PORT"     "Redis"
echo

### ─────────────────────── API health check ───────────────────────
if verify_health; then
  echo
  echo "🎉 Full-stack verification succeeded!"
  echo "   • Build: Docker ✅"
  echo "   • Runtime: $RUN_ENGINE ✅"
  echo "   • PgBouncer/Redis: checked ✅"
  echo ""
  echo "📊 API Endpoints:"
  echo "   • Health:  $HEALTH_URL"
  echo "   • Docs:    http://localhost:${HOST_PORT_API}/docs"
  echo "   • API:     http://localhost:${HOST_PORT_API}"
  [[ "$RUN_ENGINE" == "container" ]] && echo "💡 Consider: 'container system reset' later to avoid builder quirks."
  exit 0
fi

### ─────────────────── Failure: focused diagnostics ───────────────
echo
echo "⚠️  Showing last $LOG_TAIL lines of API logs:"
$RUN_ENGINE logs --tail "$LOG_TAIL" "$CONTAINER_NAME" || true
echo
echo "🧾 Container run_server.py (head -40):"
$RUN_ENGINE exec "$CONTAINER_NAME" sh -c "head -40 '$CONTAINER_RUN_SERVER' || echo 'missing'" || true
echo
echo "❌ Verification failed. Review logs above. If Apple CLI is flaky, set PREFER_APPLE_RUNTIME=0 to run via Docker."
exit 2
