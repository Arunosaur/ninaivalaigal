#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Test build script for all services using docker-to-apple-container.sh
# Tests Docker → tar → Apple Container CLI workflow for all 6 services

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() { echo -e "${BLUE}$1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

BUILD_SCRIPT="$SCRIPT_DIR/docker-to-apple-container.sh"

print_header "🧪 Testing Build Script for All Services"
print_header "=========================================="
echo ""

# Verify build script exists
if [ ! -f "$BUILD_SCRIPT" ]; then
    print_error "Build script not found: $BUILD_SCRIPT"
    exit 1
fi

# Service configurations (service_name:context:dockerfile)
# Note: Most Dockerfiles need project root as context, not service directory
SERVICE_CONFIGS=(
    "core-api:.:services/core-api/Dockerfile"
    "business-service:.:services/business-service/Dockerfile"
    "admin-vendor-service:.:services/admin-vendor-service/Dockerfile"
    "memory-service:rust-services/memory-service:rust-services/memory-service/Dockerfile"
    "graph-service:.:services/graph-service/Dockerfile"
    "grpc-gateway:go-services/grpc-gateway:go-services/grpc-gateway/Dockerfile"
)

FAILED=()
PASSED=()
SKIPPED=()

# Test each service
for service_config in "${SERVICE_CONFIGS[@]}"; do
    IFS=':' read -r service_name context dockerfile <<< "$service_config"

    print_header "Testing: $service_name"
    echo "  Context: $context"
    echo "  Dockerfile: $dockerfile"

    # Check if files exist
    if [ ! -d "$context" ]; then
        print_warning "  Context directory not found, skipping"
        SKIPPED+=("$service_name")
        echo ""
        continue
    fi

    if [ ! -f "$dockerfile" ]; then
        print_warning "  Dockerfile not found, skipping"
        SKIPPED+=("$service_name")
        echo ""
        continue
    fi

    # Test build (dry run - just check the script works)
    echo "  Running build script..."
    if "$BUILD_SCRIPT" "$service_name" \
        --dockerfile "$dockerfile" \
        --context "$context" \
        --tag arm64 \
        --platform linux/arm64 \
        --verbose 2>&1 | tee "/tmp/build-test-${service_name}.log"; then
        print_success "$service_name build completed"
        PASSED+=("$service_name")
    else
        print_error "$service_name build failed"
        FAILED+=("$service_name")
    fi

    echo ""
done

# Summary
print_header "=========================================="
print_header "Test Summary"
print_header "=========================================="
echo ""
echo "Passed: ${#PASSED[@]}"
for service in "${PASSED[@]}"; do
    echo "  ✅ $service"
done
echo ""
echo "Failed: ${#FAILED[@]}"
for service in "${FAILED[@]}"; do
    echo "  ❌ $service"
    echo "     Logs: /tmp/build-test-${service}.log"
done
echo ""
echo "Skipped: ${#SKIPPED[@]}"
for service in "${SKIPPED[@]}"; do
    echo "  ⚠️  $service"
done
echo ""

if [ ${#FAILED[@]} -eq 0 ]; then
    print_success "All service builds passed!"
    exit 0
else
    print_error "${#FAILED[@]} service build(s) failed"
    exit 1
fi
