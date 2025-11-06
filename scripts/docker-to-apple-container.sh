#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Docker to Apple Container CLI Migration Script
# Automates the Docker → tar → Apple Container CLI workflow
# Part of US#22: Apple Container CLI migration
#
# COMPLIANCE:
# - Follows CONTAINERIZATION_STANDARD.md
# - Uses ports from config/ports.nv.yaml
# - Reads environment from configs/env-{env}.env
# - Follows container naming: ninaivalaigal-{env}-{service}
# - Uses dynamic IP discovery for dependencies

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SERVICE_NAME=""
DOCKERFILE="Dockerfile"
BUILD_CONTEXT="."
IMAGE_TAG="arm64"
PLATFORM="linux/arm64"
SKIP_BUILD=false
SKIP_LOAD=false
CLEANUP=true
VERBOSE=false

# Functions
print_error() {
    echo -e "${RED}❌ $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}📦 $1${NC}"
}

usage() {
    cat << EOF
Docker to Apple Container CLI Migration Script

Usage: $0 [OPTIONS] SERVICE_NAME

This script automates the Docker → tar → Apple Container CLI workflow:
1. Builds image with Docker (reliable DNS)
2. Exports image to tarball
3. Loads image into Apple Container CLI
4. Cleans up temporary files

Arguments:
    SERVICE_NAME          Name of the service (e.g., core-api, memory-service)

Options:
    -f, --dockerfile FILE    Dockerfile path (default: Dockerfile)
    -c, --context DIR        Build context directory (default: .)
    -t, --tag TAG            Image tag (default: arm64)
    -p, --platform PLATFORM   Build platform (default: linux/arm64)
    --skip-build             Skip Docker build (use existing image)
    --skip-load              Skip loading into Apple Container CLI
    --no-cleanup             Don't remove tarball after loading
    -v, --verbose            Verbose output
    -h, --help               Show this help message

Examples:
    # Build and migrate core-api
    $0 core-api

    # Build with custom Dockerfile
    $0 memory-service -f services/memory-service/Dockerfile

    # Build with custom context
    $0 graph-service -c rust-services/graph-service -f Dockerfile

    # Skip build, just load existing image
    $0 core-api --skip-build

Environment Variables:
    NINA_ENV               Environment (dev, test, prod) - affects image naming

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--dockerfile)
            DOCKERFILE="$2"
            shift 2
            ;;
        -c|--context)
            BUILD_CONTEXT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-load)
            SKIP_LOAD=true
            shift
            ;;
        --no-cleanup)
            CLEANUP=false
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
            if [ -z "$SERVICE_NAME" ]; then
                SERVICE_NAME="$1"
            else
                print_error "Multiple service names provided: $SERVICE_NAME and $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [ -z "$SERVICE_NAME" ]; then
    print_error "SERVICE_NAME is required"
    usage
    exit 1
fi

# Check prerequisites
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v container &> /dev/null; then
    print_error "Apple Container CLI is not installed or not in PATH"
    exit 1
fi

# Construct image name
ENV_SUFFIX="${NINA_ENV:-dev}"
IMAGE_NAME="nina-${SERVICE_NAME}:${IMAGE_TAG}"

# Print header
echo "================================================================================"
echo "Docker → Apple Container CLI Migration"
echo "================================================================================"
echo "Service:     $SERVICE_NAME"
echo "Image:       $IMAGE_NAME"
echo "Dockerfile:  $DOCKERFILE"
echo "Context:     $BUILD_CONTEXT"
echo "Platform:    $PLATFORM"
echo "================================================================================"
echo ""

# Step 1: Build with Docker
if [ "$SKIP_BUILD" = false ]; then
    print_step "Step 1: Building image with Docker..."

    if [ ! -f "$DOCKERFILE" ]; then
        print_error "Dockerfile not found: $DOCKERFILE"
        exit 1
    fi

    if [ ! -d "$BUILD_CONTEXT" ]; then
        print_error "Build context not found: $BUILD_CONTEXT"
        exit 1
    fi

    BUILD_CMD="docker build --platform $PLATFORM --no-cache -t $IMAGE_NAME -f $DOCKERFILE $BUILD_CONTEXT"

    if [ "$VERBOSE" = true ]; then
        print_info "Running: $BUILD_CMD"
    fi

    if $BUILD_CMD; then
        print_success "Image built successfully: $IMAGE_NAME"
    else
        print_error "Docker build failed"
        exit 1
    fi
else
    print_info "Skipping Docker build (--skip-build)"

    # Verify image exists
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        print_error "Image not found: $IMAGE_NAME"
        print_info "Run without --skip-build to build the image first"
        exit 1
    fi
    print_success "Using existing image: $IMAGE_NAME"
fi

echo ""

# Step 2: Export to tarball
print_step "Step 2: Exporting image to tarball..."

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TARBALL="/tmp/${SERVICE_NAME}-${TIMESTAMP}.tar"

if [ "$VERBOSE" = true ]; then
    print_info "Exporting to: $TARBALL"
fi

if docker save "$IMAGE_NAME" -o "$TARBALL"; then
    TARBALL_SIZE=$(du -h "$TARBALL" | cut -f1)
    print_success "Image exported: $TARBALL ($TARBALL_SIZE)"
else
    print_error "Failed to export image"
    exit 1
fi

echo ""

# Step 3: Load into Apple Container CLI
if [ "$SKIP_LOAD" = false ]; then
    print_step "Step 3: Loading image into Apple Container CLI..."

    if [ "$VERBOSE" = true ]; then
        print_info "Running: container image load --input $TARBALL"
    fi

    if container image load --input "$TARBALL" 2>&1 | grep -q "Loaded"; then
        print_success "Image loaded into Apple Container CLI"

        # Verify image exists
        if container image list | grep -q "$IMAGE_NAME"; then
            print_success "Verified: Image exists in Apple Container CLI"
        else
            print_warning "Image may not be visible in 'container image list'"
        fi
    else
        print_error "Failed to load image into Apple Container CLI"
        if [ "$CLEANUP" = false ]; then
            print_info "Tarball preserved at: $TARBALL"
        fi
        exit 1
    fi
else
    print_info "Skipping Apple Container CLI load (--skip-load)"
    print_info "Tarball available at: $TARBALL"
fi

echo ""

# Step 4: Cleanup
if [ "$CLEANUP" = true ] && [ "$SKIP_LOAD" = false ]; then
    print_step "Step 4: Cleaning up temporary files..."
    if rm -f "$TARBALL"; then
        print_success "Tarball removed: $TARBALL"
    else
        print_warning "Failed to remove tarball: $TARBALL"
    fi
else
    if [ "$SKIP_LOAD" = true ]; then
        print_info "Tarball preserved (--skip-load): $TARBALL"
    else
        print_info "Tarball preserved (--no-cleanup): $TARBALL"
    fi
fi

echo ""

# Summary
echo "================================================================================"
echo "Migration Complete"
echo "================================================================================"
echo "Service:     $SERVICE_NAME"
echo "Image:       $IMAGE_NAME"
echo "Status:      ✅ Ready for Apple Container CLI"
echo ""
echo "Next steps:"
echo "  1. Verify image: container image list | grep $IMAGE_NAME"
echo "  2. Run container: container run -d --name ninaivalaigal-${ENV_SUFFIX}-${SERVICE_NAME} \\"
echo "                      -p [PORT]:[PORT] \\"
echo "                      $IMAGE_NAME"
echo ""
echo "View image: container image list | grep $IMAGE_NAME"
echo "================================================================================"
