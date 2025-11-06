#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Build progress tracker for SPEC-145
# Tracks which runtime/architecture/service combinations have been built

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

SERVICES=("core-api" "business-service" "admin-vendor-service" "memory-service" "graph-service" "grpc-gateway")
RUNTIMES=("docker" "colima" "apple")
ARCHITECTURES_DOCKER=("arm64" "amd64")
ARCHITECTURES_COLIMA=("arm64" "amd64")
ARCHITECTURES_APPLE=("arm64")

echo "📊 SPEC-145 Build Progress"
echo "=========================="
echo ""

# Check Docker images
echo "Docker Images:"
for service in "${SERVICES[@]}"; do
    for arch in "${ARCHITECTURES_DOCKER[@]}"; do
        if docker images | grep -q "nina-${service}.*${arch}"; then
            echo "  ✅ docker:$service:$arch"
        else
            echo "  ⏳ docker:$service:$arch"
        fi
    done
done

echo ""
echo "Colima Images: (uses Docker, check docker images)"
echo "Apple Container CLI Images:"
if command -v container &> /dev/null; then
    for service in "${SERVICES[@]}"; do
        if container image list | grep -q "nina-${service}"; then
            echo "  ✅ apple:$service:arm64"
        else
            echo "  ⏳ apple:$service:arm64"
        fi
    done
else
    echo "  ⚠️  Apple Container CLI not available"
fi

echo ""
echo "Total combinations: 18 (3 runtimes × 6 services × 1-2 archs)"
