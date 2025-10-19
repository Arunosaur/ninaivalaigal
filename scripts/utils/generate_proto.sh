#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#

# Protocol Buffer Generation Script for Developer A Task #36
# This script will generate Go gRPC code from the .proto files

set -e

echo "🔧 Protocol Buffer Generation for Task #36 gRPC Gateway"
echo "=================================================="

# Navigate to the gateway directory
cd /Users/swami/WorkSpace/ninaivalaigal/go-services/grpc-gateway || exit

# Check if we have the necessary tools
echo "📋 Checking prerequisites..."

# Check protoc
if ! command -v protoc &> /dev/null; then
    echo "❌ protoc not found. Installing via Homebrew..."
    brew install protobuf
fi

# Check Go protobuf plugins
echo "📦 Installing/updating Go protobuf plugins..."
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Add Go bin to PATH if needed
export PATH="$PATH:$(go env GOPATH)/bin"

echo "✅ Prerequisites ready"
echo ""

# Navigate to proto directory
cd proto || exit

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

echo ""
echo "✅ Protocol Buffer code generation complete!"
echo "📁 Generated files in $(pwd):"
ls -la *.pb.go 2>/dev/null || echo "   (Files will appear after running this script)"

echo ""
echo "🚀 Next steps:"
echo "   1. Run: chmod +x /Users/swami/WorkSpace/ninaivalaigal/generate_proto.sh"
echo "   2. Run: /Users/swami/WorkSpace/ninaivalaigal/generate_proto.sh"
echo "   3. Update imports in clients.go and handlers.go"
echo "   4. Test the gateway with: make run"

echo ""
echo "🎯 Task #36 Status: Protocol buffer generation ready!"
