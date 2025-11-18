#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start PgBouncer in SESSION mode (Task #85 - Dual Setup)
# For: Memory Service (Rust/SQLx with prepared statements)
# Port: 6433

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Starting PgBouncer - SESSION Mode"
echo "===================================="
echo "Purpose: Prepared statements (Rust/SQLx)"
echo "Port: 6433"
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
    "PGBOUNCER_SESS_PORT"
    "PGBOUNCER_SESS_CONTAINER"
    "PGBOUNCER_SESS_MODE"
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
echo "  Container: $PGBOUNCER_SESS_CONTAINER"
echo "  Port: $PGBOUNCER_SESS_PORT"
echo "  Pool Mode: $PGBOUNCER_SESS_MODE"
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
if container inspect "$PGBOUNCER_SESS_CONTAINER" &>/dev/null; then
    echo "  Stopping existing container..."
    container stop "$PGBOUNCER_SESS_CONTAINER" 2>/dev/null || true
    container rm "$PGBOUNCER_SESS_CONTAINER" 2>/dev/null || true
    echo "  ✅ Cleaned up"
fi

# Start PgBouncer container (Session Mode)
echo ""
echo "Starting PgBouncer container (Session Mode)..."
container run -d \
  --name "$PGBOUNCER_SESS_CONTAINER" \
  -p "${PGBOUNCER_SESS_PORT}:6433" \
  -e POOL_MODE="$PGBOUNCER_SESS_MODE" \
  -e DB_HOST="$DB_IP" \
  -e DB_NAME="$NINA_DB_NAME" \
  -e DB_USER="$NINA_DB_USER" \
  -e DB_PASSWORD="$NINA_DB_PASSWORD" \
  -e SCRAM_PASSWORD="$SCRAM_PASSWORD" \
  -e LISTEN_PORT="6433" \
  nina-pgbouncer:latest

echo "  ✅ Container started"

# Wait for PgBouncer to be ready
echo ""
echo "Waiting for PgBouncer to be ready..."
sleep 3

# Verify container is running
if ! container inspect "$PGBOUNCER_SESS_CONTAINER" | grep -q '"status":"running"'; then
    echo "❌ PgBouncer container failed to start"
    echo ""
    echo "Container logs:"
    container logs "$PGBOUNCER_SESS_CONTAINER" 2>&1 | tail -20
    exit 1
fi

# Get PgBouncer IP
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_SESS_CONTAINER" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "  ✅ PgBouncer is running"
echo ""

# Display connection info
echo "===================================="
echo "✅ PgBouncer-SESS Started Successfully"
echo "===================================="
echo ""
echo "Mode: SESSION (prepared statements)"
echo "Use for: Memory Service (Rust/SQLx)"
echo ""
echo "Connection Details:"
echo "  External: postgresql://$NINA_DB_USER:***@localhost:$PGBOUNCER_SESS_PORT/$NINA_DB_NAME"
echo "  Internal: postgresql://$NINA_DB_USER:***@$PGBOUNCER_IP:6433/$NINA_DB_NAME"
echo ""
echo "Benefits:"
echo "  • Supports prepared statements"
echo "  • Maintains session state"
echo "  • Required for SQLx (Rust)"
echo ""
echo "Monitoring:"
echo "  Status:  container list | grep pgbouncer-sess"
echo "  Logs:    container logs -f $PGBOUNCER_SESS_CONTAINER"
echo "  Stats:   psql -h localhost -p $PGBOUNCER_SESS_PORT -U $NINA_DB_USER -d pgbouncer -c 'SHOW POOLS;'"
echo ""
echo "Services using this pool:"
echo "  • Memory Service (Rust/SQLx)"
echo "  • Future services requiring prepared statements"
echo ""
