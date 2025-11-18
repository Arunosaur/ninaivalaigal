#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Stack Status Script
# Version: 1.0.0 - Day 3 Infrastructure Reliability

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
readonly ENV="${NINA_ENV:-dev}"
readonly DB_CONTAINER="ninaivalaigal-${ENV}-db"
readonly PGBOUNCER_TX_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-tx"
readonly PGBOUNCER_SESSION_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-session"
readonly PGBOUNCER_SESS_CONTAINER="ninaivalaigal-${ENV}-pgbouncer-sess"
readonly REDIS_CONTAINER="ninaivalaigal-${ENV}-redis"
readonly API_CONTAINER="ninaivalaigal-${ENV}-api"
readonly CUSTOMER_APP_CONTAINER="ninaivalaigal-${ENV}-customer-app"
readonly ADMIN_CONSOLE_CONTAINER="ninaivalaigal-${ENV}-admin-console"

readonly DB_PORT=5452
readonly PGBOUNCER_PORT=6452
readonly REDIS_PORT=6399
readonly API_PORT=13390
readonly CUSTOMER_UI_PORT=8101
readonly ADMIN_UI_PORT=8201

readonly DB_NAME="ninaivalaigal_${ENV}"
readonly DB_USER="nina"
readonly DB_PASSWORD="${NINA_DB_PASSWORD:-dev_password_change_in_production}"
readonly REDIS_PASSWORD="${NINA_REDIS_PASSWORD:-dev_redis_password}"

check_container_status() {
    local container_name=$1

    if container list | grep -q "$container_name.*running"; then
        echo -e "  ${GREEN}●${NC} $container_name: ${GREEN}RUNNING${NC}"
        return 0
    elif container list --all | grep -q "$container_name"; then
        echo -e "  ${RED}●${NC} $container_name: ${RED}STOPPED${NC}"
        return 1
    else
        echo -e "  ${YELLOW}●${NC} $container_name: ${YELLOW}NOT FOUND${NC}"
        return 1
    fi
}

check_database_health() {
    if PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Database responding to queries"

        # Get version
        local version=$(PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT version();" 2>/dev/null | head -1 | xargs)
        echo -e "    Version: ${version:0:60}..."

        # Get extensions
        echo -e "    Extensions:"
        PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "\dx" 2>/dev/null | grep -E "vector|age" | while read line; do
            echo -e "      - $line"
        done

        return 0
    else
        echo -e "  ${RED}✗${NC} Database not responding"
        return 1
    fi
}

check_redis_health() {
    if redis-cli -h localhost -p $REDIS_PORT -a "$REDIS_PASSWORD" ping 2>/dev/null | grep -q "PONG"; then
        echo -e "  ${GREEN}✓${NC} Redis responding to commands"

        # Get info
        local info=$(redis-cli -h localhost -p $REDIS_PORT -a "$REDIS_PASSWORD" INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
        echo -e "    Version: $info"

        # Get memory usage
        local memory=$(redis-cli -h localhost -p $REDIS_PORT -a "$REDIS_PASSWORD" INFO memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
        echo -e "    Memory: $memory"

        return 0
    else
        echo -e "  ${RED}✗${NC} Redis not responding"
        return 1
    fi
}

check_pgbouncer_health() {
    if PGPASSWORD="$DB_PASSWORD" psql -h localhost -p $PGBOUNCER_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} PgBouncer responding (connection pooling active)"
        echo -e "    Port: $PGBOUNCER_PORT"
        return 0
    else
        echo -e "  ${RED}✗${NC} PgBouncer not responding"
        return 1
    fi
}

check_api_health() {
    if curl -sf "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} API responding to health checks"
        echo -e "    Endpoint: http://localhost:$API_PORT/health"
        echo -e "    Docs: http://localhost:$API_PORT/docs"
        return 0
    else
        echo -e "  ${YELLOW}✗${NC} API not responding (may not be started)"
        return 1
    fi
}

main() {
    local all_healthy=true

    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║      Ninaivalaigal Complete Stack Status Report     ║${NC}"
    echo -e "${BLUE}║         Environment: ${ENV}                          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo "📦 Container Status:"
    check_container_status "$DB_CONTAINER" || all_healthy=false
    check_container_status "$PGBOUNCER_TX_CONTAINER" || all_healthy=false
    check_container_status "$PGBOUNCER_SESSION_CONTAINER" || all_healthy=false
    check_container_status "$PGBOUNCER_SESS_CONTAINER" || all_healthy=false
    check_container_status "$REDIS_CONTAINER" || all_healthy=false
    check_container_status "$API_CONTAINER" || all_healthy=false
    check_container_status "$CUSTOMER_APP_CONTAINER" || all_healthy=false
    check_container_status "$ADMIN_CONSOLE_CONTAINER" || all_healthy=false
    echo ""

    echo "🔍 Core Infrastructure Health:"
    check_database_health || all_healthy=false
    echo ""
    check_pgbouncer_health || all_healthy=false
    echo ""
    check_redis_health || all_healthy=false
    echo ""

    echo "🌐 Application Layer Health:"
    check_api_health || all_healthy=false
    echo ""

    echo "📊 Full Container List:"
    container list | grep "ninaivalaigal-${ENV}" || echo "  No containers found"
    echo ""

    if [ "$all_healthy" = true ]; then
        echo -e "${GREEN}✅ All services healthy and operational${NC}"
        exit 0
    else
        echo -e "${RED}⚠️  Some services are not healthy${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  - View logs: container logs $DB_CONTAINER"
        echo "  - Restart:   ./scripts/stack-restart.sh"
        echo "  - Stop:      ./scripts/stack-stop.sh"
        exit 1
    fi
}

main "$@"
