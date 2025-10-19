#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Generate Go bindings from Protocol Buffer definitions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTRACTS_DIR="$PROJECT_ROOT/shared/contracts"

echo "🔨 Generating Go Protocol Buffer Bindings"
echo "=========================================="
echo ""

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo "❌ Error: protoc not found"
    echo "Install with: brew install protobuf (macOS)"
    exit 1
fi

PROTOC_VERSION=$(protoc --version | awk '{print $2}')
echo "✅ Found protoc version: $PROTOC_VERSION"
echo ""

# Check Go plugins
if ! command -v protoc-gen-go &> /dev/null; then
    echo "❌ Error: protoc-gen-go not found"
    echo "Install with: go install google.golang.org/protobuf/cmd/protoc-gen-go@latest"
    exit 1
fi

if ! command -v protoc-gen-go-grpc &> /dev/null; then
    echo "❌ Error: protoc-gen-go-grpc not found"
    echo "Install with: go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest"
    exit 1
fi

echo "✅ Found Go protoc plugins"
echo ""

# Find all .proto files
echo "📂 Finding .proto files..."
PROTO_FILES=$(find "$CONTRACTS_DIR" -name "*.proto" | sort)
PROTO_COUNT=$(echo "$PROTO_FILES" | wc -l | tr -d ' ')
echo "✅ Found $PROTO_COUNT proto files"
echo ""

# Generate Go bindings
echo "🔨 Generating Go bindings..."
echo ""

for proto_file in $PROTO_FILES; do
    rel_path="${proto_file#$CONTRACTS_DIR/}"
    echo "  Processing: $rel_path"

    protoc \
        --proto_path="$CONTRACTS_DIR" \
        --go_out="$CONTRACTS_DIR" \
        --go_opt=paths=source_relative \
        --go-grpc_out="$CONTRACTS_DIR" \
        --go-grpc_opt=paths=source_relative \
        "$proto_file"

    if [ $? -eq 0 ]; then
        echo "    ✅ Generated Go bindings"
    else
        echo "    ❌ Failed to generate bindings"
        exit 1
    fi
done

echo ""
echo "✅ Go binding generation complete!"
echo ""
echo "📊 Generated files:"
find "$CONTRACTS_DIR" -name "*.pb.go" | wc -l | xargs echo "  Go modules (*.pb.go):"
find "$CONTRACTS_DIR" -name "*_grpc.pb.go" | wc -l | xargs echo "  gRPC stubs (*_grpc.pb.go):"
echo ""
echo "🎯 Next steps:"
echo "  1. Import in Go services: import authv1 \"github.com/Arunosaur/ninaivalaigal/shared/contracts/auth/v1\""
echo "  2. Use generated types in your code"
echo "  3. Run go mod tidy"
