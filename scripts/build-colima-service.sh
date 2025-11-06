#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Build Colima container for a service (ARM64 and/or x86-64)
# Part of SPEC-145: Multi-Runtime Multi-Architecture Builds
#
# Note: Colima uses Docker CLI, so this script is similar to build-docker-service.sh
# but with Colima-specific considerations

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_error() { echo -e "${RED}❌ $1${NC}" >&2; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_step() { echo -e "${BLUE}📦 $1${NC}"; }

# Default values
SERVICE_NAME=""
DOCKERFILE="Dockerfile"
BUILD_CONTEXT="."
ARCHITECTURES="arm64,amd64"
MULTI_ARCH=false
PUSH=false
VERBOSE=false

usage() {
    cat << EOF
Build Colima Service Container (ARM64 + x86-64)

Usage: $0 [OPTIONS] SERVICE_NAME

This script builds Colima containers for ARM64 and/or x86-64 architectures.
Colima uses Docker CLI, so builds are Docker-compatible.

Arguments:
    SERVICE_NAME          Name of the service (e.g., core-api, memory-service)

Options:
    -f, --dockerfile FILE    Dockerfile path (default: Dockerfile)
    -c, --context DIR        Build context directory (default: .)
    -a, --arch ARCHS          Architectures: arm64,amd64, or both (default: arm64,amd64)
    -m, --multi-arch          Build multi-arch manifest (buildx)
    --push                    Push to registry (requires --multi-arch)
    -v, --verbose             Verbose output
    -h, --help                Show this help

Examples:
    # Build both architectures separately
    $0 core-api

    # Build only ARM64
    $0 core-api -a arm64

    # Build only x86-64
    $0 core-api -a amd64

Environment Variables:
    DOCKER_REGISTRY       Registry URL
    IMAGE_TAG             Tag for images (default: latest)
    COLIMA_ARCH           Colima architecture (arm64 or x86-64)

EOF
}

# Parse arguments (same as Docker script)
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
        -a|--arch)
            ARCHITECTURES="$2"
            shift 2
            ;;
        -m|--multi-arch)
            MULTI_ARCH=true
            shift
            ;;
        --push)
            PUSH=true
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
                print_error "Multiple service names provided"
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

# Check Colima
if ! command -v colima &> /dev/null; then
    print_warning "Colima not found, but Docker will be used (Colima-compatible)"
fi

# Image naming
REGISTRY="${DOCKER_REGISTRY:-}"
TAG="${IMAGE_TAG:-latest}"
if [ -n "$REGISTRY" ]; then
    IMAGE_BASE="${REGISTRY}/ninaivalaigal-${SERVICE_NAME}"
else
    IMAGE_BASE="nina-${SERVICE_NAME}"
fi

# Print header
echo "================================================================================"
echo "Colima Multi-Architecture Build"
echo "================================================================================"
echo "Service:     $SERVICE_NAME"
echo "Dockerfile:  $DOCKERFILE"
echo "Context:     $BUILD_CONTEXT"
echo "Architectures: $ARCHITECTURES"
echo "Multi-Arch:  $MULTI_ARCH"
echo "================================================================================"
echo ""

# Validate files
if [ ! -f "$DOCKERFILE" ]; then
    print_error "Dockerfile not found: $DOCKERFILE"
    exit 1
fi

if [ ! -d "$BUILD_CONTEXT" ]; then
    print_error "Build context not found: $BUILD_CONTEXT"
    exit 1
fi

# Build (same logic as Docker since Colima uses Docker CLI)
if [ "$MULTI_ARCH" = true ]; then
    print_step "Building multi-architecture image..."

    PLATFORMS=""
    IFS=',' read -ra ARCHS <<< "$ARCHITECTURES"
    for arch in "${ARCHS[@]}"; do
        case "$arch" in
            arm64|aarch64)
                PLATFORMS="${PLATFORMS}linux/arm64,"
                ;;
            amd64|x86_64)
                PLATFORMS="${PLATFORMS}linux/amd64,"
                ;;
            *)
                print_error "Unknown architecture: $arch"
                exit 1
                ;;
        esac
    done
    PLATFORMS="${PLATFORMS%,}"

    # Setup buildx
    if ! docker buildx version &> /dev/null; then
        print_error "Docker buildx is not available"
        exit 1
    fi

    if ! docker buildx ls | grep -q "multiarch"; then
        print_info "Creating buildx builder..."
        docker buildx create --name multiarch --use 2>/dev/null || true
    fi

    BUILD_CMD="docker buildx build --platform $PLATFORMS --no-cache"

    if [ "$PUSH" = true ]; then
        BUILD_CMD="$BUILD_CMD --push"
        print_info "Will push to registry: $IMAGE_BASE:$TAG"
    else
        BUILD_CMD="$BUILD_CMD --load"
    fi

    BUILD_CMD="$BUILD_CMD -t $IMAGE_BASE:$TAG -f $DOCKERFILE $BUILD_CONTEXT"

    if [ "$VERBOSE" = true ]; then
        print_info "Running: $BUILD_CMD"
    fi

    if eval "$BUILD_CMD"; then
        print_success "Multi-arch image built: $IMAGE_BASE:$TAG"
    else
        print_error "Multi-arch build failed"
        exit 1
    fi
else
    # Build individual architectures
    IFS=',' read -ra ARCHS <<< "$ARCHITECTURES"

    for arch in "${ARCHS[@]}"; do
        case "$arch" in
            arm64|aarch64)
                PLATFORM="linux/arm64"
                ARCH_TAG="arm64"
                ;;
            amd64|x86_64)
                PLATFORM="linux/amd64"
                ARCH_TAG="amd64"
                ;;
            *)
                print_error "Unknown architecture: $arch"
                exit 1
                ;;
        esac

        print_step "Building $PLATFORM image..."

        IMAGE_NAME="${IMAGE_BASE}:${ARCH_TAG}"
        BUILD_CMD="docker build --platform $PLATFORM --no-cache -t $IMAGE_NAME -f $DOCKERFILE $BUILD_CONTEXT"

        if [ "$VERBOSE" = true ]; then
            print_info "Running: $BUILD_CMD"
        fi

        if eval "$BUILD_CMD"; then
            print_success "$PLATFORM image built: $IMAGE_NAME"
        else
            print_error "$PLATFORM build failed"
            exit 1
        fi

        echo ""
    done
fi

# Summary
echo ""
echo "================================================================================"
echo "Build Complete"
echo "================================================================================"
echo "Service:     $SERVICE_NAME"
if [ "$MULTI_ARCH" = true ]; then
    echo "Image:       $IMAGE_BASE:$TAG (multi-arch)"
else
    echo "Images:      $IMAGE_BASE:{arm64,amd64}"
fi
echo ""
echo "Colima Notes:"
echo "  - Colima uses Docker CLI, so images are Docker-compatible"
echo "  - Start Colima: colima start --arch arm64 (or x86-64)"
echo "  - Use Docker commands normally with Colima running"
echo "================================================================================"
