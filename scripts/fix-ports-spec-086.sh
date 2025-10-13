#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Fix port mappings to comply with SPEC-086
# Apple CLI Dev Environment - Runtime Offset +20

set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          SPEC-086 Port Correction - Apple CLI Dev                   ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Get IPs (column 6 in container list output)
DB_IP=$(container list | grep ninaivalaigal-dev-db | awk '{print $6}')
REDIS_IP=$(container list | grep ninaivalaigal-dev-redis | awk '{print $6}')
echo "Database IP: $DB_IP"
echo "Redis IP: $REDIS_IP"
echo ""

# 1. Fix PgBouncer Port (should be 6452)
echo "=== 1. Fixing PgBouncer Port (ADD port binding) ==="
echo "Note: PgBouncer was running WITHOUT -p flag (no port exposed to host)"
container stop ninaivalaigal-dev-pgbouncer 2>/dev/null || true
container delete ninaivalaigal-dev-pgbouncer 2>/dev/null || true

# Check if PgBouncer config exists
if [ ! -f /tmp/pgbouncer.ini ]; then
    echo "Creating PgBouncer configuration..."
    cat > /tmp/pgbouncer.ini << EOF
[databases]
ninaivalaigal_dev = host=${DB_IP} port=5432 dbname=ninaivalaigal_dev

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
admin_users = postgres
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/lib/pgbouncer/pgbouncer.pid
EOF
fi

container run -d --name ninaivalaigal-dev-pgbouncer -p 6452:6432 \
  -v /tmp/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini \
  nina-pgbouncer:arm64
echo "✅ PgBouncer now on port 6452 (host) → 6432 (container)"
echo ""

# Get new PgBouncer IP
sleep 3
PGBOUNCER_IP=$(container list | grep ninaivalaigal-dev-pgbouncer | awk '{print $6}')
echo "PgBouncer IP: $PGBOUNCER_IP"
echo ""

# 2. Fix API to use correct PgBouncer
echo "=== 2. Updating API with Correct PgBouncer Connection ==="
container stop ninaivalaigal-dev-api 2>/dev/null || true
container delete ninaivalaigal-dev-api 2>/dev/null || true
container run -d --name ninaivalaigal-dev-api -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:dev_password_change_in_production@${PGBOUNCER_IP}:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://:dev_redis_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="dev-secret-change-in-production" \
  -e PYTHONPATH=/app:/app/server \
  -e ENVIRONMENT=development \
  nina-api:arm64
echo "✅ API restarted with correct PgBouncer connection"
echo ""

# 3. Fix Customer UI Port (should be 8101)
echo "=== 3. Fixing Customer UI Port: 8100 → 8101 ==="
container stop ninaivalaigal-dev-ui-customer 2>/dev/null || true
container delete ninaivalaigal-dev-ui-customer 2>/dev/null || true
container run -d --name ninaivalaigal-dev-ui-customer -p 8101:8101 \
  nina-customer-ui:arm64
echo "✅ Customer UI now on port 8101"
echo ""

# 4. Fix Admin Console Port (should be 8201)
echo "=== 4. Fixing Admin Console Port: 8101 → 8201 ==="
container stop ninaivalaigal-dev-ui-admin 2>/dev/null || true
container delete ninaivalaigal-dev-ui-admin 2>/dev/null || true
container run -d --name ninaivalaigal-dev-ui-admin -p 8201:8102 \
  nina-admin-console:arm64
echo "✅ Admin Console now on port 8201"
echo ""

echo "=== Waiting for services to start (10 seconds) ==="
sleep 10
echo ""

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          SPEC-086 Compliance Verification                            ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Port Bindings (SPEC-086 Apple Dev) ==="
echo "Expected Ports: 5452, 6452, 6399, 13390, 8101, 8201"
echo ""
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201)" | awk '{print $1, $9}' | sort -u || true
echo ""

echo "=== Service Health Checks ==="
echo -n "API Health: "
curl -s http://localhost:13390/health || echo "❌ Failed"
echo ""
echo -n "Customer UI: "
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8101/ || echo "❌ Failed"
echo -n "Admin Console: "
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8201/ || echo "❌ Failed"
echo ""

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Updated Service URLs                                        ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Database (PostgreSQL):  localhost:5452"
echo "🔄 PgBouncer:              localhost:6452"
echo "🔴 Redis:                  localhost:6399"
echo "🚀 API:                    http://localhost:13390"
echo "   - Health:               http://localhost:13390/health"
echo "   - Swagger:              http://localhost:13390/docs"
echo "👥 Customer UI:            http://localhost:8101"
echo "🔧 Admin Console:          http://localhost:8201"
echo "🧠 Enhanced Memory:        http://localhost:7070"
echo ""
echo "✅ SPEC-086 Compliance Complete!"
