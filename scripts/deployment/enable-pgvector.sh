#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Enable pgvector extension in ninaivalaigal-dev-db

set -euo pipefail

echo "🔌 Enabling pgvector extension in ninaivalaigal-dev-db..."

# Enable pgvector extension
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "CREATE EXTENSION IF NOT EXISTS vector;" || {
    echo "❌ Failed to enable pgvector extension"
    echo "   Check if pgvector is installed in the database image"
    exit 1
}

echo "✅ pgvector extension enabled!"

# Also enable pgcrypto for UUIDs
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" || {
    echo "⚠️  pgcrypto extension failed (non-critical)"
}

echo ""
echo "📊 Verify extensions:"
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "\dx"

echo ""
echo "✅ Database ready for Developer B's tests!"
