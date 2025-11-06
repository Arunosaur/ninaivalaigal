#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Unified Multi-Runtime Multi-Architecture Build Script
# Part of SPEC-145: Multi-Runtime Multi-Architecture Builds
#
# Builds containers for Docker, Colima, and Apple Container CLI
# Supports ARM64 and x86-64 where applicable

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

print_header() { echo -e "${BOLD}${BLUE}$1${NC}"; }
print_step() { echo -e "${BLUE}🔄 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

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

# Options
RUNTIMES="docker,colima,apple"
ARCHITECTURES="arm64,amd64"
SERVICES_TO_BUILD=""
SKIP_BUILD=false
VERBOSE=false

usage() {
    cat << EOF
Build All Runtimes and Architectures

Usage: $0 [OPTIONS] [SERVICES...]

Builds containers for Docker, Colima, and Apple Container CLI with ARM64 and x86-64 support.

Options:
    -r, --runtimes RUNTIMES      Comma-separated: docker,colima,apple (default: all)
    -a, --arch ARCHS              Comma-separated: arm64,amd64 (default: both)
    -s, --services SERVICES       Comma-separated service names (default: all)
    --skip-build                  Skip building (validate only)
    -v, --verbose                 Verbose output
    -h, --help                    Show this help

Examples:
    # Build all services for all runtimes and architectures
    $0

    # Build only Docker (both architectures)
    $0 -r docker

    # Build only ARM64 for all runtimes
    $0 -a arm64

    # Build specific services
    $0 core-api business-service

    # Build Docker ARM64 only
    $0 -r docker -a arm64

Architecture Support:
    Docker:     ARM64 ✅, x86-64 ✅
    Colima:    ARM64 ✅, x86-64 ✅
    Apple CLI: ARM64 ✅, x86-64 ❌ (macOS only)

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--runtimes)
            RUNTIMES="$2"
            shift 2
            ;;
        -a|--arch)
            ARCHITECTURES="$2"
            shift 2
            ;;
        -s|--services)
            SERVICES_TO_BUILD="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [ -z "$SERVICES_TO_BUILD" ]; then
                SERVICES_TO_BUILD="$1"
            else
                SERVICES_TO_BUILD="$SERVICES_TO_BUILD,$1"
            fi
            shift
            ;;
    esac
done

print_header "🏗️  Multi-Runtime Multi-Architecture Build"
print_header "============================================"
echo ""
print_step "Runtimes: $RUNTIMES"
print_step "Architectures: $ARCHITECTURES"
print_step "Skip Build: $SKIP_BUILD"
echo ""

# Determine which services to build
if [ -z "$SERVICES_TO_BUILD" ]; then
    SERVICES_TO_BUILD="${!SERVICES[@]}"
    SERVICES_TO_BUILD="${SERVICES_TO_BUILD// /,}"
fi

# Track results
BUILT=()
FAILED=()

# Build for each runtime
IFS=',' read -ra RUNTIME_LIST <<< "$RUNTIMES"
IFS=',' read -ra ARCH_LIST <<< "$ARCHITECTURES"
IFS=',' read -ra SERVICE_LIST <<< "$SERVICES_TO_BUILD"

for runtime in "${RUNTIME_LIST[@]}"; do
    print_header "📦 Runtime: ${runtime^^}"
    print_header "============================================"
    echo ""

    for service_name in "${SERVICE_LIST[@]}"; do
        if [ -z "${SERVICES[$service_name]:-}" ]; then
            print_warning "Unknown service: $service_name, skipping"
            continue
        fi

        IFS=' ' read -r context dockerfile service_type <<< "${SERVICES[$service_name]}"

        print_step "Building: $service_name ($service_type)"
        echo "  Context: $context"
        echo "  Dockerfile: $dockerfile"

        # Check files
        if [ ! -d "$context" ]; then
            print_warning "  Context directory not found, skipping"
            FAILED+=("$runtime:$service_name (context missing)")
            continue
        fi

        if [ ! -f "$dockerfile" ]; then
            print_warning "  Dockerfile not found, skipping"
            FAILED+=("$runtime:$service_name (dockerfile missing)")
            continue
        fi

        # Build based on runtime
        case "$runtime" in
            docker)
                for arch in "${ARCH_LIST[@]}"; do
                    if [ "$SKIP_BUILD" = false ]; then
                        if "$SCRIPT_DIR/build-docker-service.sh" "$service_name" \
                            --dockerfile "$dockerfile" \
                            --context "$context" \
                            --arch "$arch" \
                            $([ "$VERBOSE" = true ] && echo "--verbose" || echo "") \
                            2>&1 | tee "/tmp/build-${runtime}-${service_name}-${arch}.log"; then
                            print_success "$service_name ($arch) built for Docker"
                            BUILT+=("docker:$service_name:$arch")
                        else
                            print_error "$service_name ($arch) build failed for Docker"
                            FAILED+=("docker:$service_name:$arch")
                        fi
                    else
                        print_info "Skipping build (--skip-build)"
                        BUILT+=("docker:$service_name:$arch")
                    fi
                done
                ;;
            colima)
                for arch in "${ARCH_LIST[@]}"; do
                    if [ "$SKIP_BUILD" = false ]; then
                        if "$SCRIPT_DIR/build-colima-service.sh" "$service_name" \
                            --dockerfile "$dockerfile" \
                            --context "$context" \
                            --arch "$arch" \
                            $([ "$VERBOSE" = true ] && echo "--verbose" || echo "") \
                            2>&1 | tee "/tmp/build-${runtime}-${service_name}-${arch}.log"; then
                            print_success "$service_name ($arch) built for Colima"
                            BUILT+=("colima:$service_name:$arch")
                        else
                            print_error "$service_name ($arch) build failed for Colima"
                            FAILED+=("colima:$service_name:$arch")
                        fi
                    else
                        print_info "Skipping build (--skip-build)"
                        BUILT+=("colima:$service_name:$arch")
                    fi
                done
                ;;
            apple)
                # Apple Container CLI only supports ARM64
                if [[ " ${ARCH_LIST[*]} " =~ " arm64 " ]] || [[ " ${ARCH_LIST[*]} " =~ " all " ]]; then
                    if [ "$SKIP_BUILD" = false ]; then
                        if "$SCRIPT_DIR/docker-to-apple-container.sh" "$service_name" \
                            --dockerfile "$dockerfile" \
                            --context "$context" \
                            --tag arm64 \
                            --platform linux/arm64 \
                            $([ "$VERBOSE" = true ] && echo "--verbose" || echo "") \
                            2>&1 | tee "/tmp/build-${runtime}-${service_name}-arm64.log"; then
                            print_success "$service_name (arm64) built for Apple Container CLI"
                            BUILT+=("apple:$service_name:arm64")
                        else
                            print_error "$service_name (arm64) build failed for Apple Container CLI"
                            FAILED+=("apple:$service_name:arm64")
                        fi
                    else
                        print_info "Skipping build (--skip-build)"
                        BUILT+=("apple:$service_name:arm64")
                    fi
                else
                    print_warning "  Apple Container CLI only supports ARM64, skipping"
                fi
                ;;
            *)
                print_error "Unknown runtime: $runtime"
                FAILED+=("$runtime:$service_name (unknown runtime)")
                ;;
        esac

        echo ""
    done

    echo ""
done

# Summary
print_header "============================================"
print_header "Summary"
print_header "============================================"
echo ""
echo "Built: ${#BUILT[@]}"
for build in "${BUILT[@]}"; do
    echo "  ✅ $build"
done

if [ ${#FAILED[@]} -gt 0 ]; then
    echo ""
    echo "Failed: ${#FAILED[@]}"
    for build in "${FAILED[@]}"; do
        echo "  ❌ $build"
    done
fi

echo ""
if [ ${#FAILED[@]} -eq 0 ]; then
    print_success "All builds completed successfully!"
    exit 0
else
    print_error "Some builds failed"
    exit 1
fi
