#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Start the Business Service via Apple Container CLI following the containerization standard.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_ROOT="${PROJECT_ROOT}/services/business-service"

log() { printf '\033[1;36m[business]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[business]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[business]\033[0m %s\n' "$*"; }

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        err "Missing required command: $1"
        exit 1
    fi
}

detect_host_ip() {
    for iface in en0 en1; do
        if ipconfig getifaddr "$iface" >/dev/null 2>&1; then
            ipconfig getifaddr "$iface"
            return
        fi
    done
    echo "127.0.0.1"
}

require_cmd docker
require_cmd container

if [ -f "${PROJECT_ROOT}/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "${PROJECT_ROOT}/.env.dev"
fi

NINA_ENV="${NINA_ENV:-dev}"
IMAGE_NAME="${IMAGE_NAME:-ninaivalaigal-business-service:arm64}"
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-business-service"
CONTAINER_PORT=13391
HOST_PORT="${BUSINESS_HOST_PORT:-13391}"

HOST_IP=$(detect_host_ip)

log "Starting Business Service"
log "Environment: ${NINA_ENV}"
log "Image:       ${IMAGE_NAME}"
log "Container:   ${CONTAINER_NAME}"
log "Host port:   ${HOST_PORT} -> container ${CONTAINER_PORT}"
log "Public URL:  http://${HOST_IP}:${HOST_PORT}/health"

PGBOUNCER_CONTAINER="${PGBOUNCER_TX_CONTAINER:-ninaivalaigal-${NINA_ENV}-pgbouncer-tx}"
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
SKIP_DB=false

if [ -z "$PGBOUNCER_IP" ] || [ "$PGBOUNCER_IP" = "null" ]; then
    warn "PgBouncer transaction container not detected; continuing with BUSINESS_SERVICE_SKIP_DB=true"
    SKIP_DB=true
else
    log "PgBouncer-TX: ${PGBOUNCER_IP}:6432"
    DATABASE_URL="postgresql://${NINA_DB_USER}:${NINA_DB_PASSWORD}@${PGBOUNCER_IP}:6432/ninaivalaigal_${NINA_ENV}"
fi

REDIS_CONTAINER="${REDIS_CONTAINER:-ninaivalaigal-${NINA_ENV}-redis}"
REDIS_IP=$(container inspect "$REDIS_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_URL=""

if [ -n "$REDIS_IP" ] && [ "$REDIS_IP" != "null" ]; then
    REDIS_URL="redis://${REDIS_IP}:6379/0"
    log "Redis: ${REDIS_IP}:6379"
else
    warn "Redis container not detected; continuing without REDIS_URL"
fi

if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
    log "Building arm64 Docker image..."
    (cd "${PROJECT_ROOT}" && docker build --platform linux/arm64 -t "${IMAGE_NAME}" -f services/business-service/Dockerfile .)
else
    log "Skipping Docker build (SKIP_BUILD=true)"
fi

TMP_TAR=$(mktemp /tmp/business-service-XXXXXX.tar)
trap 'rm -f "${TMP_TAR}"' EXIT

log "Exporting image to ${TMP_TAR}"
docker save "${IMAGE_NAME}" -o "${TMP_TAR}"

log "Loading image into Apple Container CLI"
container image load -i "${TMP_TAR}" >/dev/null

if container list | awk 'NR>1 {print $1}' | grep -q "${CONTAINER_NAME}"; then
    log "Stopping existing container"
    container stop "${CONTAINER_NAME}" >/dev/null || true
    container rm "${CONTAINER_NAME}" >/dev/null || true
fi

ENV_ARGS=(
    -e NINA_ENV="${NINA_ENV}"
    -e PORT="${CONTAINER_PORT}"
    -e SERVICE_ROLE="business-service"
    -e LOG_LEVEL="${LOG_LEVEL:-info}"
)

if [ "$SKIP_DB" = true ]; then
    ENV_ARGS+=(-e BUSINESS_SERVICE_SKIP_DB=true)
else
    ENV_ARGS+=(-e DATABASE_URL="${DATABASE_URL}")
fi

if [ -n "$REDIS_URL" ]; then
    ENV_ARGS+=(-e REDIS_URL="${REDIS_URL}")
fi

log "Launching container"
container run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    "${ENV_ARGS[@]}" \
    "${IMAGE_NAME}" >/dev/null

sleep 3

if command -v curl >/dev/null 2>&1; then
    for _ in {1..10}; do
        if curl -sf "http://localhost:${HOST_PORT}/health" >/dev/null; then
            log "Health check passed"
            break
        fi
        sleep 2
    done
else
    warn "curl not available; skipping health probe"
fi

log "Business Service ready"
log "Logs: container logs -f ${CONTAINER_NAME}"
log "Readiness: curl http://localhost:${HOST_PORT}/ready"
