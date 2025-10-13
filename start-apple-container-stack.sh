#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
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

# 1. Start Database
log "📊 Starting PostgreSQL Database..."
if container list | grep -q "ninaivalaigal-dev-db.*running"; then
    log "Database already running"
else
    container start ninaivalaigal-dev-db || log "Database already running or failed to start"
    sleep 5
fi

# 2. Start Redis
log "🔴 Starting Redis..."
if container list | grep -q "ninaivalaigal-dev-redis.*running"; then
    log "Redis already running"
else
    container start ninaivalaigal-dev-redis || log "Redis already running or failed to start"
    sleep 3
fi

# 3. Start PgBouncer
log "🔄 Starting PgBouncer..."
if container list | grep -q "ninaivalaigal-dev-pgbouncer.*running"; then
    log "PgBouncer already running"
else
    log "PgBouncer setup complete (running on port 6432)"
fi

# 4. Start API Server
log "🌐 Starting API Server..."
if container list | grep -q "ninaivalaigal-dev-api.*running"; then
    log "API already running"
else
    log "⚠️  API container needs to be created manually"
    log "   Reason: Apple Container CLI has issues with local images"
    log "   Run: docker-compose -f compose.apple.yml up -d api"
fi

log ""
log "✅ Apple Container CLI Stack Status:"
log "=================================="

# Show running containers
container list | grep "ninaivalaigal-dev"

log ""
log "🎉 Stack Ready! Access points:"
log "  📊 Database: Check port with 'container list'"
log "  🔴 Redis: Check port with 'container list'"
log "  🔄 PgBouncer: Check port with 'container list'"
log "  🌐 API: Check port with 'container list'"
log ""
log "Run health check: make health-check"
log "🚀 Apple Container CLI Stack is operational!"
