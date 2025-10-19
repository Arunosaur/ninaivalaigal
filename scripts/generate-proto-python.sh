#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Generate Python bindings from Protocol Buffer definitions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONTRACTS_DIR="$PROJECT_ROOT/shared/contracts"

echo "🔨 Generating Python Protocol Buffer Bindings"
echo "=============================================="
echo ""

# Check if protoc is installed
if ! command -v protoc &> /dev/null; then
    echo "❌ Error: protoc not found"
    echo "Install with: brew install protobuf (macOS) or apt-get install protobuf-compiler (Linux)"
    exit 1
fi

# Check protoc version
PROTOC_VERSION=$(protoc --version | awk '{print $2}')
echo "✅ Found protoc version: $PROTOC_VERSION"
echo ""

# Check if Python plugin is available
if ! python3 -c "import google.protobuf" 2>/dev/null; then
    echo "❌ Error: protobuf Python package not found"
    echo "Install with: pip install protobuf grpcio grpcio-tools"
    exit 1
fi

echo "✅ Found Python protobuf package"
echo ""

# Find all .proto files
echo "📂 Finding .proto files..."
PROTO_FILES=$(find "$CONTRACTS_DIR" -name "*.proto" | sort)
PROTO_COUNT=$(echo "$PROTO_FILES" | wc -l | tr -d ' ')
echo "✅ Found $PROTO_COUNT proto files"
echo ""

# Generate Python bindings
echo "🔨 Generating Python bindings..."
echo ""

for proto_file in $PROTO_FILES; do
    rel_path="${proto_file#$CONTRACTS_DIR/}"
    echo "  Processing: $rel_path"

    python3 -m grpc_tools.protoc \
        --proto_path="$CONTRACTS_DIR" \
        --python_out="$CONTRACTS_DIR" \
        --pyi_out="$CONTRACTS_DIR" \
        --grpc_python_out="$CONTRACTS_DIR" \
        "$proto_file"

    if [ $? -eq 0 ]; then
        echo "    ✅ Generated Python bindings"
    else
        echo "    ❌ Failed to generate bindings"
        exit 1
    fi
done

echo ""
echo "✅ Python binding generation complete!"
echo ""
echo "📊 Generated files:"
find "$CONTRACTS_DIR" -name "*_pb2.py" | wc -l | xargs echo "  Python modules (*_pb2.py):"
find "$CONTRACTS_DIR" -name "*_pb2.pyi" | wc -l | xargs echo "  Type stubs (*_pb2.pyi):"
find "$CONTRACTS_DIR" -name "*_pb2_grpc.py" | wc -l | xargs echo "  gRPC stubs (*_pb2_grpc.py):"
echo ""
echo "🎯 Next steps:"
echo "  1. Import in Python services: from shared.contracts.auth.v1 import auth_pb2"
echo "  2. Use generated classes in your code"
echo "  3. Run services to test integration"
