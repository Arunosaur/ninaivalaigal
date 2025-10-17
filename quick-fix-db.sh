#!/usr/bin/env bash
# Quick fix for Developer B's database issue

set -euo pipefail

echo "Fixing database connection for Developer B..."

# 1. Start containers if not running
container list | grep -q "ninaivalaigal-dev-db" || ./scripts/nv-db-start.sh
container list | grep -q "ninaivalaigal-dev-pgbouncer" || ./scripts/nv-pgbouncer-start.sh

# 2. Get current PgBouncer IP
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
echo "PgBouncer IP: $PGB_IP"

# 3. Create database if it doesn't exist
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/postgres" << EOF
SELECT 'CREATE DATABASE ninaivalaigal_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ninaivalaigal_dev')\\gexec
\c ninaivalaigal_dev
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
EOF

# 4. Run migrations
cd /Users/swami/WorkSpace/ninaivalaigal
alembic upgrade head

# 5. Test connection
psql "postgresql://nina:dev_password_change_in_production@${PGB_IP}:6432/ninaivalaigal_dev" -c "SELECT 1;"

echo "✅ Database ready! Update your test config to use: $PGB_IP"
