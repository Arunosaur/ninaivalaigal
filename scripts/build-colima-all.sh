#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Build all services for Colima (ARM64 + x86-64)
# Part of SPEC-145: Multi-Runtime Multi-Architecture Builds

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Service configurations
declare -A SERVICES=(
    ["core-api"]=". services/core-api/Dockerfile python"
    ["business-service"]=". services/business-service/Dockerfile python"
    ["admin-vendor-service"]=". services/admin-vendor-service/Dockerfile python"
    ["memory-service"]="rust-services/memory-service rust-services/memory-service/Dockerfile rust"
    ["graph-service"]=". services/graph-service/Dockerfile python"
    ["grpc-gateway"]="go-services/grpc-gateway go-services/grpc-gateway/Dockerfile go"
)

ARCHITECTURES="${ARCHITECTURES:-arm64,amd64}"
VERBOSE="${VERBOSE:-false}"

echo "🏗️  Building All Services for Colima"
echo "====================================="
echo "Architectures: $ARCHITECTURES"
echo ""

BUILT=()
FAILED=()

for service_name in "${!SERVICES[@]}"; do
    IFS=' ' read -r context dockerfile service_type <<< "${SERVICES[$service_name]}"

    echo "Building: $service_name ($service_type)"

    if "$SCRIPT_DIR/build-colima-service.sh" "$service_name" \
        --dockerfile "$dockerfile" \
        --context "$context" \
        --arch "$ARCHITECTURES" \
        "$([ "$VERBOSE" = "true" ] && echo "--verbose" || echo "")"; then
        echo "✅ $service_name built successfully"
        BUILT+=("$service_name")
    else
        echo "❌ $service_name build failed"
        FAILED+=("$service_name")
    fi

    echo ""
done

echo "====================================="
echo "Summary:"
echo "  Built: ${#BUILT[@]}"
echo "  Failed: ${#FAILED[@]}"
echo "====================================="

exit "$([ ${#FAILED[@]} -eq 0 ] && echo 0 || echo 1)"
