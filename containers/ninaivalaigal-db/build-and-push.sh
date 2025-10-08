#!/usr/bin/env bash
# Build and push Ninaivalaigal database image to GitHub Container Registry
# Supports multi-architecture builds (ARM64 + x86_64)

set -euo pipefail

VERSION="${1:-1.0.0}"
REGISTRY="ghcr.io/arunosaur"
IMAGE_NAME="ninaivalaigal-db"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}"

log() { echo "🔧 $*"; }
error() { echo "❌ $*" >&2; exit 1; }

# Check if logged into GitHub Container Registry
if ! docker info | grep -q "Username"; then
    log "Not logged into Docker registry. Run:"
    log "  echo \$GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin"
    error "Please login to GitHub Container Registry first"
fi

log "Building Ninaivalaigal Database Image v${VERSION}"
log "Target: ${FULL_IMAGE}:${VERSION}"

# Create builder if it doesn't exist
if ! docker buildx inspect ninaivalaigal-builder &>/dev/null; then
    log "Creating buildx builder..."
    docker buildx create --name ninaivalaigal-builder --use
fi

docker buildx use ninaivalaigal-builder

# Build for multiple architectures
log "Building multi-arch image (arm64, amd64)..."
docker buildx build \
    --platform linux/arm64,linux/amd64 \
    --tag "${FULL_IMAGE}:${VERSION}" \
    --tag "${FULL_IMAGE}:latest" \
    --push \
    .

log "✅ Successfully built and pushed:"
log "   ${FULL_IMAGE}:${VERSION}"
log "   ${FULL_IMAGE}:latest"
log ""
log "To use this image, update compose files:"
log "   image: ${FULL_IMAGE}:${VERSION}"
