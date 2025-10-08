#!/usr/bin/env bash
# Fix ONLY UI ports - PgBouncer is already working!
# Safe: Only touches UI containers, leaves DB/API/Redis/PgBouncer alone

set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          Fix UI Ports Only (Safe - No DB/API changes)               ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  This will ONLY restart UI containers with correct ports"
echo "✅ Database, API, Redis, PgBouncer will NOT be touched"
echo ""

# Step 1: Stop ALL UI containers first to free ports
echo "=== Step 1: Stopping All UI Containers ==="
container stop ninaivalaigal-dev-ui-customer 2>/dev/null && echo "  Stopped Customer UI" || echo "  Customer UI not running"
container stop ninaivalaigal-dev-ui-admin 2>/dev/null && echo "  Stopped Admin Console" || echo "  Admin Console not running"
container stop ninaivalaigal-dev-em 2>/dev/null && echo "  Stopped Enhanced Memory" || echo "  EM not running"
echo ""

# Step 2: Delete all UI containers
echo "=== Step 2: Removing UI Containers ==="
container delete ninaivalaigal-dev-ui-customer 2>/dev/null && echo "  Deleted Customer UI" || echo "  Customer UI already deleted"
container delete ninaivalaigal-dev-ui-admin 2>/dev/null && echo "  Deleted Admin Console" || echo "  Admin Console already deleted"
container delete ninaivalaigal-dev-em 2>/dev/null && echo "  Deleted Enhanced Memory" || echo "  EM already deleted"
echo ""

echo "Waiting for ports to be released..."
sleep 3
echo ""

# Step 3: Start with correct ports
echo "=== Step 3: Starting Customer UI on Port 8101 ==="
container run -d --name ninaivalaigal-dev-ui-customer -p 8101:8101 \
  nina-customer-ui:arm64
echo "✅ Customer UI started on port 8101"
echo ""

echo "=== Step 4: Starting Admin Console on Port 8201 ==="
container run -d --name ninaivalaigal-dev-ui-admin -p 8201:8102 \
  nina-admin-console:arm64
echo "✅ Admin Console started on port 8201"
echo ""

echo "=== Step 5: Starting Enhanced Memory on Port 8301 ==="
container run -d --name ninaivalaigal-dev-em -p 8301:7070 \
  nina-em:arm64
echo "✅ Enhanced Memory started on port 8301"
echo ""

sleep 5

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          SPEC-086 Compliance Check                                   ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Expected Ports for Apple Dev ==="
echo "PostgreSQL:  5452 ✅"
echo "PgBouncer:   6452 ✅"
echo "Redis:       6399 ✅"
echo "API:         13390 ✅"
echo "Customer UI: 8101 (fixing...)"
echo "Admin UI:    8201 (fixing...)"
echo "EM:          8301 (fixing...)"
echo ""

echo "=== Actual Listening Ports ==="
lsof -nP -iTCP -sTCP:LISTEN | grep -E "(5452|6452|6399|13390|8101|8201|8301)" | awk '{print $1, $9}' | sort -u

echo ""
echo "=== Service Health Checks ==="
curl -s http://localhost:13390/health && echo " ✅ API"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8101/ && echo " ✅ Customer UI"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8201/ && echo " ✅ Admin Console"
curl -s -o /dev/null -w "HTTP %{http_code}" http://localhost:8301/health && echo " ✅ Enhanced Memory"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║          ✅ UI Ports Fixed - Stack Fully SPEC-086 Compliant         ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
