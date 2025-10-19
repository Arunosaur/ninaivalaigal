#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#

# Generate Go code from Protocol Buffer definitions
# Developer A Task #36 - gRPC Gateway

set -e

echo "🔧 Generating Go gRPC stubs from Protocol Buffers..."

# Check if protoc is available
if ! command -v protoc &> /dev/null; then
    echo "❌ protoc is not installed. Please install Protocol Buffer compiler:"
    echo "   macOS: brew install protobuf"
    echo "   Linux: apt-get install protobuf-compiler"
    exit 1
fi

# Check if protoc-gen-go is available
if ! command -v protoc-gen-go &> /dev/null; then
    echo "📦 Installing protoc-gen-go..."
    go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
fi

# Check if protoc-gen-go-grpc is available
if ! command -v protoc-gen-go-grpc &> /dev/null; then
    echo "📦 Installing protoc-gen-go-grpc..."
    go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
fi

# Create output directories
mkdir -p memorypb
mkdir -p graphopspb

echo "🏗️  Generating Memory Service gRPC code..."
protoc \
    --go_out=. \
    --go_opt=paths=source_relative \
    --go-grpc_out=. \
    --go-grpc_opt=paths=source_relative \
    memory.proto

echo "🏗️  Generating GraphOps Service gRPC code..."
protoc \
    --go_out=. \
    --go_opt=paths=source_relative \
    --go-grpc_out=. \
    --go-grpc_opt=paths=source_relative \
    graphops.proto

echo "✅ Protocol Buffer code generation complete!"
echo "📁 Generated files:"
echo "   - memory.pb.go (Memory Service types)"
echo "   - memory_grpc.pb.go (Memory Service gRPC client/server)"
echo "   - graphops.pb.go (GraphOps Service types)"
echo "   - graphops_grpc.pb.go (GraphOps Service gRPC client/server)"

echo ""
echo "🚀 Next steps:"
echo "   1. Update go.mod with generated dependencies"
echo "   2. Implement gRPC client connections in main.go"
echo "   3. Add request/response translation logic"
