#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Build script for GraphOps Rust service
# SPEC-099: High-performance Apache AGE query execution

set -euo pipefail

echo "🏗️  Building GraphOps Rust Service..."

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]] || [[ "$ARCH" == "aarch64" ]]; then
    PLATFORM="linux/arm64"
    TAG="graphops-rust:arm64"
elif [[ "$ARCH" == "x86_64" ]]; then
    PLATFORM="linux/amd64"
    TAG="graphops-rust:amd64"
else
    echo "❌ Unsupported architecture: $ARCH"
    exit 1
fi

echo "📦 Building for platform: $PLATFORM"
echo "🏷️  Tag: $TAG"

# Build with container (Apple Container CLI compatible)
if command -v container &> /dev/null; then
    container build \
        --platform "$PLATFORM" \
        -t "$TAG" \
        -f containers/graphops-rust/Dockerfile \
        .
elif command -v docker &> /dev/null; then
    docker build \
        --platform "$PLATFORM" \
        -t "$TAG" \
        -f containers/graphops-rust/Dockerfile \
        .
else
    echo "❌ Neither 'container' nor 'docker' command found"
    exit 1
fi

echo "✅ GraphOps Rust service built successfully"
echo ""
echo "Run with:"
if command -v container &> /dev/null; then
    echo "  container run -p 50051:50051 $TAG"
else
    echo "  docker run -p 50051:50051 $TAG"
fi
