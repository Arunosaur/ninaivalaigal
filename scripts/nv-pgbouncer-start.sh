#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Medhasys LLC
#
# Start PgBouncer with session mode (Task #85)
# Uses centralized .env.dev for configuration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting PgBouncer (Session Mode - Task #85)"
echo "==========================================="

# Source centralized environment
if [ -f "$PROJECT_ROOT/.env.dev" ]; then
    # shellcheck disable=SC1091
    source "$PROJECT_ROOT/.env.dev"
    echo "✅ Loaded environment from .env.dev"
else
    echo "❌ .env.dev not found!"
    echo "   Run: cp .env.example .env.dev"
    echo "   Then edit .env.dev with proper values"
    exit 1
fi

# Validate required environment variables
required_vars=(
    "NINA_ENV"
    "NINA_DB_USER"
    "NINA_DB_PASSWORD"
    "NINA_DB_NAME"
    "PGBOUNCER_PORT"
    "DB_CONTAINER"
    "PGBOUNCER_CONTAINER"
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
echo "  PgBouncer Container: $PGBOUNCER_CONTAINER"
echo "  Port: $PGBOUNCER_PORT"
echo "  Pool Mode: ${PGBOUNCER_POOL_MODE:-session}"
echo "  Database: $NINA_DB_NAME"
echo "  User: $NINA_DB_USER"
echo ""

# Resolve Database IP dynamically
echo "Resolving Database endpoint..."
DB_IP=$(container inspect "$DB_CONTAINER" 2>/dev/null | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
if [ -z "$DB_IP" ] || [ "$DB_IP" = "null" ]; then
    echo "❌ Unable to find Database container ($DB_CONTAINER)"
    echo "   Please ensure database is running:"
    echo "   cd $PROJECT_ROOT && ./scripts/nv-db-start.sh"
    exit 1
fi

echo "  Database IP: $DB_IP"
echo ""

# Stop existing PgBouncer container if running
echo "Checking for existing PgBouncer container..."
if container inspect "$PGBOUNCER_CONTAINER" &>/dev/null; then
    echo "  Stopping existing container..."
    container stop "$PGBOUNCER_CONTAINER" 2>/dev/null || true
    container rm "$PGBOUNCER_CONTAINER" 2>/dev/null || true
    echo "  ✅ Cleaned up"
fi

# Start PgBouncer container
echo ""
echo "Starting PgBouncer container..."
container run -d \
  --name "$PGBOUNCER_CONTAINER" \
  -p "${PGBOUNCER_PORT}:6432" \
  -e DB_HOST="$DB_IP" \
  -e DB_NAME="$NINA_DB_NAME" \
  -e DB_USER="$NINA_DB_USER" \
  -e DB_PASSWORD="$NINA_DB_PASSWORD" \
  nina-pgbouncer:latest

echo "  ✅ Container started"

# Wait for PgBouncer to be ready
echo ""
echo "Waiting for PgBouncer to be ready..."
sleep 3

# Verify container is running
if ! container inspect "$PGBOUNCER_CONTAINER" | grep -q '"status":"running"'; then
    echo "❌ PgBouncer container failed to start"
    echo ""
    echo "Container logs:"
    container logs "$PGBOUNCER_CONTAINER" 2>&1 | tail -20
    exit 1
fi

# Get PgBouncer IP
PGBOUNCER_IP=$(container inspect "$PGBOUNCER_CONTAINER" | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "  ✅ PgBouncer is running"
echo ""

# Display connection info
echo "==========================================="
echo "PgBouncer Started Successfully"
echo "==========================================="
echo ""
echo "Connection Details:"
echo "  External: postgresql://$NINA_DB_USER:***@localhost:$PGBOUNCER_PORT/$NINA_DB_NAME"
echo "  Internal: postgresql://$NINA_DB_USER:***@$PGBOUNCER_IP:6432/$NINA_DB_NAME"
echo ""
echo "Pool Mode: ${PGBOUNCER_POOL_MODE:-session} (supports prepared statements)"
echo ""
echo "Useful Commands:"
echo "  Status:  container list | grep pgbouncer"
echo "  Logs:    container logs -f $PGBOUNCER_CONTAINER"
echo "  Stop:    container stop $PGBOUNCER_CONTAINER"
echo "  Config:  container exec $PGBOUNCER_CONTAINER cat /etc/pgbouncer/pgbouncer.ini"
echo "  Stats:   psql -h localhost -p $PGBOUNCER_PORT -U $NINA_DB_USER -d pgbouncer -c 'SHOW POOLS;'"
echo ""
