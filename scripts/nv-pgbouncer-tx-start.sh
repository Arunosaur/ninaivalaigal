#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start PgBouncer in TRANSACTION mode (Task #85 - Dual Setup)
# For: Core API, GraphOps, stateless REST services
# Port: 6432

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting PgBouncer - TRANSACTION Mode"
echo "========================================"
echo "Purpose: High-throughput stateless services"
echo "Port: 6432"
echo ""

# Source centralized environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment from .env.dev"
else
    echo "❌ .env.dev not found!"
    echo "   Run: cp .env.example .env.dev"
    exit 1
fi

# Validate required environment variables
required_vars=(
    "NINA_ENV"
    "NINA_DB_USER"
    "NINA_DB_PASSWORD"
    "NINA_DB_NAME"
    "PGBOUNCER_TX_PORT"
    "PGBOUNCER_TX_CONTAINER"
    "PGBOUNCER_TX_MODE"
    "DB_CONTAINER"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "❌ Required environment variable $var not set"
        exit 1
    fi
done

echo ""
echo "Configuration:"
echo "  Environment: $NINA_ENV"
echo "  Container: $PGBOUNCER_TX_CONTAINER"
echo "  Port: $PGBOUNCER_TX_PORT"
echo "  Pool Mode: $PGBOUNCER_TX_MODE"
echo "  Max Connections: ${PGBOUNCER_MAX_CLIENT_CONN:-100}"
echo "  Pool Size: ${PGBOUNCER_DEFAULT_POOL_SIZE:-20}"
echo ""

# Resolve Database IP dynamically
echo "Resolving Database endpoint..."
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$DB_IP" ] || [ "$DB_IP" = "null" ]; then
    echo "❌ Unable to find Database container ($DB_CONTAINER)"
    echo "   Please ensure database is running first"
    exit 1
fi

echo "  Database IP: $DB_IP"
echo ""

# Retrieve SCRAM password hash from PostgreSQL (for PgBouncer authentication)
echo "Retrieving SCRAM password hash from database..."
SCRAM_PASSWORD=$(PGPASSWORD="$NINA_DB_PASSWORD" psql -h "$DB_IP" -p 5432 -U "$NINA_DB_USER" -d "$NINA_DB_NAME" -t -c "SELECT rolpassword FROM pg_authid WHERE rolname='$NINA_DB_USER';" 2>/dev/null | tr -d ' \n')
if [ -z "$SCRAM_PASSWORD" ] || [ "$SCRAM_PASSWORD" = "" ]; then
    echo "❌ Unable to retrieve SCRAM password hash from database"
    echo "   Ensure user $NINA_DB_USER exists and has a password set"
    exit 1
fi
echo "  ✅ SCRAM hash retrieved"
echo ""

# Stop existing container if running
echo "Checking for existing container..."
if container inspect "$PGBOUNCER_TX_CONTAINER" &>/dev/null; then
    echo "  Stopping existing container..."
    container stop "$PGBOUNCER_TX_CONTAINER" 2>/dev/null || true
    container rm "$PGBOUNCER_TX_CONTAINER" 2>/dev/null || true
    echo "  ✅ Cleaned up"
fi

# Start PgBouncer container (Transaction Mode)
echo ""
echo "Starting PgBouncer container (Transaction Mode)..."
container run -d \
  --name "$PGBOUNCER_TX_CONTAINER" \
  -p "${PGBOUNCER_TX_PORT}:6432" \
  -e POOL_MODE="$PGBOUNCER_TX_MODE" \
  -e DB_HOST="$DB_IP" \
  -e DB_NAME="$NINA_DB_NAME" \
  -e DB_USER="$NINA_DB_USER" \
  -e DB_PASSWORD="$NINA_DB_PASSWORD" \
  -e SCRAM_PASSWORD="$SCRAM_PASSWORD" \
  nina-pgbouncer:latest

echo "  ✅ Container started"

# Wait for PgBouncer to be ready
echo ""
echo "Waiting for PgBouncer to be ready..."
sleep 3

# Verify container is running
if ! container inspect "$PGBOUNCER_TX_CONTAINER" | grep -q '"status":"running"'; then
    echo "❌ PgBouncer container failed to start"
    echo ""
    echo "Container logs:"
    container logs "$PGBOUNCER_TX_CONTAINER" 2>&1 | tail -20
    exit 1
fi

# Get PgBouncer IP
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_TX_CONTAINER" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "  ✅ PgBouncer is running"
echo ""

# Display connection info
echo "========================================"
echo "✅ PgBouncer-TX Started Successfully"
echo "========================================"
echo ""
echo "Mode: TRANSACTION (fast, stateless)"
echo "Use for: Core API, GraphOps, REST services"
echo ""
echo "Connection Details:"
echo "  External: postgresql://$NINA_DB_USER:***@localhost:$PGBOUNCER_TX_PORT/$NINA_DB_NAME"
echo "  Internal: postgresql://$NINA_DB_USER:***@$PGBOUNCER_IP:6432/$NINA_DB_NAME"
echo ""
echo "Benefits:"
echo "  • Fastest performance (minimal overhead)"
echo "  • Optimal for stateless queries"
echo "  • Connection reuse per transaction"
echo ""
echo "Monitoring:"
echo "  Status:  container list | grep pgbouncer-tx"
echo "  Logs:    container logs -f $PGBOUNCER_TX_CONTAINER"
echo "  Stats:   psql -h localhost -p $PGBOUNCER_TX_PORT -U $NINA_DB_USER -d pgbouncer -c 'SHOW POOLS;'"
echo ""
echo "Services using this pool:"
echo "  • Core API (Python FastAPI)"
echo "  • GraphOps (Cypher queries)"
echo "  • Future REST services"
echo ""
