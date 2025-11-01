#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Start the Go gRPC Gateway inside the Apple Container CLI runtime.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_ROOT="${PROJECT_ROOT}/go-services/grpc-gateway"

log() { printf '\033[1;36m[gateway]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[gateway]\033[0m %s\n' "$*"; }

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
IMAGE_NAME="${IMAGE_NAME:-ninaivalaigal-grpc-gateway:arm64}"
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-grpc-gateway"
# Standard: gRPC gateway binds to canonical port 13395 inside container
# See: config/ports.nv.yaml and docs/standards/CONTAINERIZATION_STANDARD.md
CONTAINER_PORT=13395
HOST_PORT=${GATEWAY_HOST_PORT:-13395}

HOST_IP=${HOST_SERVICE_IP:-$(detect_host_ip)}
PUBLIC_HOST="${GATEWAY_PUBLIC_HOST_OVERRIDE:-localhost}"
PUBLIC_PORT="${GATEWAY_PUBLIC_PORT_OVERRIDE:-${HOST_PORT}}"

MEMORY_PORT=${MEMORY_SERVICE_PORT:-13393}
GRAPHOPS_PORT=${GRAPHOPS_SERVICE_PORT:-13398}
CORE_API_PORT=${CORE_API_PORT:-13390}

MEMORY_ADDR="${MEMORY_SERVICE_ADDR_OVERRIDE:-${HOST_IP}:${MEMORY_PORT}}"
GRAPHOPS_ADDR="${GRAPHOPS_SERVICE_ADDR_OVERRIDE:-${HOST_IP}:${GRAPHOPS_PORT}}"
CORE_API_ADDR="${CORE_API_ADDR_OVERRIDE:-${HOST_IP}:${CORE_API_PORT}}"

OTEL_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}"
OTEL_ENABLED="${OTEL_TRACING_ENABLED:-true}"

log "Starting gRPC gateway"
log "Environment: ${NINA_ENV}"
log "Container:   ${CONTAINER_NAME}"
log "Image:       ${IMAGE_NAME}"
log "Host port:   ${HOST_PORT} -> container ${CONTAINER_PORT}"
log "Public URL:  http://${PUBLIC_HOST}:${PUBLIC_PORT}/health"
log "Memory addr: ${MEMORY_ADDR}"
log "GraphOps:    ${GRAPHOPS_ADDR}"
log "Core API:    ${CORE_API_ADDR}"

if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
	log "Building arm64 Docker image..."
	(cd "${SERVICE_ROOT}" && docker build --platform linux/arm64 -t "${IMAGE_NAME}" .)
else
	log "Skipping Docker build (SKIP_BUILD=true)"
fi

TMP_TAR=$(mktemp /tmp/grpc-gateway-XXXXXX.tar)
trap 'rm -f "${TMP_TAR}"' EXIT

log "Exporting image to ${TMP_TAR}"
docker save "${IMAGE_NAME}" -o "${TMP_TAR}"

log "Loading image into Apple container runtime"
container image load -i "${TMP_TAR}" >/dev/null

if container list | awk 'NR>1 {print $1}' | grep -q "${CONTAINER_NAME}"; then
	log "Stopping existing container"
	container stop "${CONTAINER_NAME}" >/dev/null || true
	container rm "${CONTAINER_NAME}" >/dev/null || true
fi

log "Launching container"
container run -d \
	--name "${CONTAINER_NAME}" \
	-p "${HOST_PORT}:${CONTAINER_PORT}" \
	-e GATEWAY_HOST="0.0.0.0" \
	-e GATEWAY_PORT="${CONTAINER_PORT}" \
	-e GATEWAY_PUBLIC_HOST="${PUBLIC_HOST}" \
	-e GATEWAY_PUBLIC_PORT="${PUBLIC_PORT}" \
	-e CORE_API_ADDR="${CORE_API_ADDR}" \
	-e MEMORY_SERVICE_ADDR="${MEMORY_ADDR}" \
	-e GRAPHOPS_SERVICE_ADDR="${GRAPHOPS_ADDR}" \
	-e OTEL_SERVICE_NAME="ninaivalaigal-grpc-gateway" \
	-e OTEL_EXPORTER_OTLP_ENDPOINT="${OTEL_ENDPOINT}" \
	-e OTEL_TRACING_ENABLED="${OTEL_ENABLED}" \
	"${IMAGE_NAME}" >/dev/null

sleep 2

if command -v curl >/dev/null 2>&1; then
	if curl -sf "http://localhost:${HOST_PORT}/health" >/dev/null; then
		log "Health check passed"
	else
		err "Health check failed (gateway may still be starting)"
	fi
else
	log "curl not available; skipping health probe"
fi

log "Gateway ready"
log "Logs: container logs -f ${CONTAINER_NAME}"
log "gRPC list: grpcurl -plaintext localhost:${HOST_PORT} list"
