#!/usr/bin/env bash
# Complete Apple Container CLI Stack Startup
# Starts: Database → PgBouncer → API Server

set -euo pipefail

log() { printf "\033[1;32m[stack]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

log "🚀 Starting Complete Apple Container CLI Stack"
log "================================================"

# Check if Apple Container CLI is available
command -v container >/dev/null 2>&1 || die "Apple Container CLI not found. Please install it first."

# 1. Start Database (if not running)
if ! container list | grep -q "nv-db"; then
    log "📊 Starting PostgreSQL Database..."
    bash scripts/nv-db-start.sh
else
    log "📊 Database already running"
fi

# 2. Start PgBouncer (if not running)
if ! container list | grep -q "nv-pgbouncer"; then
    log "🔄 Starting PgBouncer Connection Pooler..."
    PGBOUNCER_PORT=6433 bash scripts/nv-pgbouncer-start.sh
else
    log "🔄 PgBouncer already running"
fi

# 3. Start API Server (if not running)
if ! container list | grep -q "nv-api"; then
    log "🌐 Starting FastAPI Server..."
    # Get database container IP
    DB_IP=$(container list | grep nv-db | awk '{print $NF}')
    container run --detach --name nv-api \
        --publish 13370:8000 \
        --env "NINAIVALAIGAL_DATABASE_URL=postgresql://nina:change_me_securely@${DB_IP}:5432/nina" \
        --env "NINAIVALAIGAL_JWT_SECRET=dev-secret-change-in-production" \
        nina-api:arm64

    # Wait for API to be ready
    log "⏳ Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:13370/health >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
else
    log "🌐 API Server already running"
fi

log ""
log "✅ Apple Container CLI Stack Status:"
log "=================================="

# Show final status
PGBOUNCER_PORT=6433 make stack-status

log ""
log "🎉 Stack Ready! Access points:"
log "  📊 Database: localhost:5433 (user: nina)"
log "  🔄 PgBouncer: localhost:6433"
log "  🌐 API: http://localhost:13370"
log "  🏥 Health: http://localhost:13370/health"
log ""
log "🚀 Apple Container CLI Stack is fully operational!"
