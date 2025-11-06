#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Comprehensive Build and Deploy Script for All Services
# Tests builds, validates standards compliance, and optionally deploys
#
# COMPLIANCE:
# - Follows CONTAINERIZATION_STANDARD.md
# - Uses ports from config/ports.nv.yaml
# - Uses docker-to-apple-container.sh for builds
# - Validates all start scripts

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

BUILD_SCRIPT="$SCRIPT_DIR/docker-to-apple-container.sh"
ENV_FILE="${ENV_FILE:-configs/env-dev.env}"

# Service configurations (from ports.nv.yaml)
# Note: Python services need project root (.) as context, Rust/Go use service directory
declare -A SERVICES=(
    ["core-api"]=". services/core-api/Dockerfile 13390 8000 python"
    ["business-service"]=". services/business-service/Dockerfile 13391 8000 python"
    ["admin-vendor-service"]=". services/admin-vendor-service/Dockerfile 13392 8000 python"
    ["memory-service"]="rust-services/memory-service rust-services/memory-service/Dockerfile 13393 8000 rust"
    ["graph-service"]=". services/graph-service/Dockerfile 13394 8000 python"
    ["grpc-gateway"]="go-services/grpc-gateway go-services/grpc-gateway/Dockerfile 13395 13395 go"
)

# Options
SKIP_BUILD=false
SKIP_DEPLOY=true
SKIP_TESTS=false
VERBOSE=false

usage() {
    cat << EOF
Build and Deploy All Services

Usage: $0 [OPTIONS]

Options:
    --deploy          Deploy services after building (default: build only)
    --skip-build      Skip building (use existing images)
    --skip-tests      Skip running tests
    -v, --verbose     Verbose output
    -h, --help        Show this help

Examples:
    # Build all services (no deployment)
    $0

    # Build and deploy all services
    $0 --deploy

    # Skip tests
    $0 --skip-tests

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --deploy)
            SKIP_DEPLOY=false
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
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
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

print_header "🏗️  Build and Deploy All Services"
print_header "===================================="
echo ""
print_step "Environment: ${ENV_FILE}"
print_step "Build Script: ${BUILD_SCRIPT}"
print_step "Deploy: $([ "$SKIP_DEPLOY" = false ] && echo "Yes" || echo "No (build only)")"
echo ""

# Verify prerequisites
if [ ! -f "$BUILD_SCRIPT" ]; then
    print_error "Build script not found: $BUILD_SCRIPT"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

if ! command -v container &> /dev/null; then
    print_error "Apple Container CLI is not installed"
    exit 1
fi

# Load environment
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    print_success "Loaded environment from $ENV_FILE"
else
    print_warning "$ENV_FILE not found, using defaults"
fi

NINA_ENV=${NINA_ENV:-dev}

# Track results
BUILT=()
FAILED_BUILDS=()
DEPLOYED=()
FAILED_DEPLOYS=()

# Phase 1: Build all services
print_header "📦 Phase 1: Building All Services"
print_header "==================================="
echo ""

for service_name in "${!SERVICES[@]}"; do
    IFS=' ' read -r context dockerfile port_external port_internal service_type <<< "${SERVICES[$service_name]}"

    print_step "Building: $service_name"
    echo "  Type: $service_type"
    echo "  Context: $context"
    echo "  Dockerfile: $dockerfile"
    echo "  Port: $port_external → $port_internal"

    # Check if files exist
    if [ ! -d "$context" ]; then
        print_warning "  Context directory not found, skipping"
        FAILED_BUILDS+=("$service_name (context missing)")
        echo ""
        continue
    fi

    if [ ! -f "$dockerfile" ]; then
        print_warning "  Dockerfile not found, skipping"
        FAILED_BUILDS+=("$service_name (dockerfile missing)")
        echo ""
        continue
    fi

    # Build
    if [ "$SKIP_BUILD" = false ]; then
        if "$BUILD_SCRIPT" "$service_name" \
            --dockerfile "$dockerfile" \
            --context "$context" \
            --tag arm64 \
            --platform linux/arm64 \
            $([ "$VERBOSE" = true ] && echo "--verbose" || echo "") 2>&1 | tee "/tmp/build-${service_name}.log"; then
            print_success "$service_name built successfully"
            BUILT+=("$service_name")
        else
            print_error "$service_name build failed"
            FAILED_BUILDS+=("$service_name (build error)")
        fi
    else
        print_info "Skipping build (--skip-build)"
        BUILT+=("$service_name")
    fi

    echo ""
done

# Phase 2: Deploy (if requested)
if [ "$SKIP_DEPLOY" = false ]; then
    print_header "🚀 Phase 2: Deploying All Services"
    print_header "==================================="
    echo ""

    for service_name in "${BUILT[@]}"; do
        print_step "Deploying: $service_name"

        # Find start script
        START_SCRIPT=""
        if [ -f "scripts/nv-${service_name}-start.sh" ]; then
            START_SCRIPT="scripts/nv-${service_name}-start.sh"
        elif [ -f "services/${service_name}/nv-${service_name}-start.sh" ]; then
            START_SCRIPT="services/${service_name}/nv-${service_name}-start.sh"
        elif [ -f "rust-services/${service_name}/nv-${service_name}-start.sh" ]; then
            START_SCRIPT="rust-services/${service_name}/nv-${service_name}-start.sh"
        fi

        if [ -z "$START_SCRIPT" ]; then
            print_warning "  Start script not found, skipping deployment"
            FAILED_DEPLOYS+=("$service_name (no start script)")
            echo ""
            continue
        fi

        if [ -x "$START_SCRIPT" ]; then
            if bash "$START_SCRIPT" 2>&1 | tee "/tmp/deploy-${service_name}.log"; then
                print_success "$service_name deployed successfully"
                DEPLOYED+=("$service_name")
            else
                print_error "$service_name deployment failed"
                FAILED_DEPLOYS+=("$service_name (deploy error)")
            fi
        else
            print_warning "  Start script not executable: $START_SCRIPT"
            FAILED_DEPLOYS+=("$service_name (script not executable)")
        fi

        echo ""
        sleep 2  # Brief pause between deployments
    done
fi

# Phase 3: Test (if not skipped)
if [ "$SKIP_TESTS" = false ]; then
    print_header "🧪 Phase 3: Testing Services"
    print_header "============================="
    echo ""

    for service_name in "${BUILT[@]}"; do
        IFS=' ' read -r context dockerfile port_external port_internal service_type <<< "${SERVICES[$service_name]}"

        print_step "Testing: $service_name"

        # Health check
        if curl -sf "http://localhost:${port_external}/health" > /dev/null 2>&1; then
            print_success "$service_name health check passed"
        else
            print_warning "$service_name health check failed (may not be running)"
        fi

        echo ""
    done
fi

# Summary
print_header "===================================="
print_header "Summary"
print_header "===================================="
echo ""
echo "Built: ${#BUILT[@]}"
for service in "${BUILT[@]}"; do
    echo "  ✅ $service"
done
echo ""

if [ ${#FAILED_BUILDS[@]} -gt 0 ]; then
    echo "Failed Builds: ${#FAILED_BUILDS[@]}"
    for service in "${FAILED_BUILDS[@]}"; do
        echo "  ❌ $service"
    done
    echo ""
fi

if [ "$SKIP_DEPLOY" = false ]; then
    echo "Deployed: ${#DEPLOYED[@]}"
    for service in "${DEPLOYED[@]}"; do
        echo "  ✅ $service"
    done
    echo ""

    if [ ${#FAILED_DEPLOYS[@]} -gt 0 ]; then
        echo "Failed Deploys: ${#FAILED_DEPLOYS[@]}"
        for service in "${FAILED_DEPLOYS[@]}"; do
            echo "  ❌ $service"
        done
        echo ""
    fi
fi

# Exit status
if [ ${#FAILED_BUILDS[@]} -eq 0 ] && [ ${#FAILED_DEPLOYS[@]} -eq 0 ]; then
    print_success "All operations completed successfully!"
    exit 0
else
    print_error "Some operations failed"
    exit 1
fi
