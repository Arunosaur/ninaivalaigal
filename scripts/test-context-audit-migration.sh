#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Test script for Context Sharing Audit Trail migration
# US-94: Context Sharing Audit Trail

set -euo pipefail

echo "🧪 Testing Context Sharing Audit Trail Migration"
echo "================================================"
echo ""

# Check if database is available
echo "1. Checking database connection..."

# Try to get PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer 2>/dev/null | jq -r '.[0].networks[0].address' 2>/dev/null | cut -d'/' -f1 || echo "")

if [ -z "$PGB_IP" ]; then
    echo "⚠️  PgBouncer container not found"
    echo "   Please start the database stack first:"
    echo "   ./scripts/stack-start-unified.sh"
    echo ""
    echo "   Or manually start database:"
    echo "   ./scripts/nv-db-start.sh"
    echo "   ./scripts/nv-pgbouncer-start.sh"
    exit 1
fi

echo "✅ Found PgBouncer at: $PGB_IP"
echo ""

# Check database connection
export DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev"

echo "2. Testing database connection..."
if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo "   DATABASE_URL: postgresql://nina:***@${PGB_IP}:6432/ninaivalaigal_dev"
    exit 1
fi
echo ""

# Check if table already exists
echo "3. Checking if context_sharing_audit_logs table exists..."
TABLE_EXISTS=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'context_sharing_audit_logs');" || echo "false")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo "⚠️  Table already exists - migration may have already been applied"
    echo ""
    echo "   To re-run migration, first drop the table:"
    echo "   psql \"$DATABASE_URL\" -c \"DROP TABLE IF EXISTS context_sharing_audit_logs CASCADE;\""
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
else
    echo "✅ Table does not exist - ready to run migration"
fi
echo ""

# Run migration
echo "4. Running migration..."
cd /Users/swami/WorkSpace/ninaivalaigal || exit 1

if alembic upgrade head; then
    echo "✅ Migration completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi
echo ""

# Verify table was created
echo "5. Verifying table structure..."
TABLE_EXISTS=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'context_sharing_audit_logs');" || echo "false")

if [ "$TABLE_EXISTS" = "t" ]; then
    echo "✅ Table created successfully"

    # Show table structure
    echo ""
    echo "Table columns:"
    psql "$DATABASE_URL" -c "\d context_sharing_audit_logs" | head -30

    # Count indexes
    INDEX_COUNT=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'context_sharing_audit_logs';" || echo "0")
    echo ""
    echo "✅ Indexes created: $INDEX_COUNT"
else
    echo "❌ Table was not created"
    exit 1
fi
echo ""

echo "================================================"
echo "✅ Context Sharing Audit Trail migration complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Test audit logging by sharing a context"
echo "2. Query audit logs via API: GET /contexts/{id}/audit-logs"
echo "3. Verify 90-day retention cleanup is working"
