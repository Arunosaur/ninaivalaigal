#!/bin/bash
set -euo pipefail

# Build all required container images for ninaivalaigal

echo "🏗️  Building ninaivalaigal container images"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "📍 Project root: $PROJECT_ROOT"
echo ""

# Build PgBouncer image
echo "🔨 Building PgBouncer image..."
if [ -f "containers/pgbouncer/Dockerfile" ]; then
    container build -t nina-pgbouncer:arm64 -f containers/pgbouncer/Dockerfile containers/pgbouncer/
    echo "✅ PgBouncer image built: nina-pgbouncer:arm64"
else
    echo "❌ PgBouncer Dockerfile not found at containers/pgbouncer/Dockerfile"
    exit 1
fi

echo ""

# Build API image
echo "🔨 Building API image..."
if [ -f "Dockerfile" ]; then
    container build -t nina-api:arm64 .
    echo "✅ API image built: nina-api:arm64"
elif [ -f "server/Dockerfile" ]; then
    container build -t nina-api:arm64 -f server/Dockerfile .
    echo "✅ API image built: nina-api:arm64"
else
    echo "⚠️  API Dockerfile not found. Skipping API image build."
    echo "   The stack will use direct Python execution instead."
fi

echo ""

# List built images
echo "📋 Built images:"
container images | grep -E "(nina-|REPOSITORY)" || echo "No nina- images found"

echo ""
echo "✅ Image building complete!"
echo ""
echo "🚀 You can now start the stack with:"
echo "   make dev-up"
