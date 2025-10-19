#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# fix-developer-b-db.sh

set -euo pipefail

echo "🔧 Fixing Developer B Database Connection"
echo "=========================================="
echo ""

# 1. Check containers
echo "1. Checking containers..."
if ! container list | grep -q "ninaivalaigal-dev-db.*running"; then
    echo "❌ Database not running! Starting..."
    cd /Users/swami/WorkSpace/ninaivalaigal || exit
    ./scripts/nv-db-start.sh
fi

if ! container list | grep -q "ninaivalaigal-dev-pgbouncer.*running"; then
    echo "❌ PgBouncer not running! Starting..."
    ./scripts/nv-pgbouncer-start.sh
fi

# 2. Get current IPs
echo "2. Getting container IPs..."
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "   PgBouncer IP: $PGB_IP"

# 3. Check database exists
echo "3. Checking if ninaivalaigal_dev database exists..."
if ! psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='ninaivalaigal_dev'" | grep -q 1; then
    echo "   Creating ninaivalaigal_dev database..."
    psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres" << EOF
CREATE DATABASE ninaivalaigal_dev;
\\c ninaivalaigal_dev
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pgvector\";
EOF
else
    echo "   ✅ Database exists"
fi

# 4. Test connection
echo "4. Testing database connection..."
if psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "   ✅ Connection successful!"
else
    echo "   ❌ Connection failed!"
    exit 1
fi

# 5. Run migrations
echo "5. Running migrations..."
cd /Users/swami/WorkSpace/ninaivalaigal || exit
alembic upgrade head || echo "   ⚠️  Migrations may have issues (check manually)"

echo ""
echo "=========================================="
echo "✅ Database setup complete!"
echo "=========================================="
echo ""
echo "Current connection string:"
echo "postgresql://nina:***@${PGB_IP}:6432/ninaivalaigal_dev"
echo ""
echo "Update your test configuration to use:"
echo "export PGBOUNCER_IP=${PGB_IP}"
echo ""
echo "Now run your tests:"
echo "conda activate nina && pytest tests/integration/test_business_service.py -v"
