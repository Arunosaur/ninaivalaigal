#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Stack Stop Script
# Version: 1.0.0 - Day 3 Infrastructure Reliability

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m'

# Configuration
readonly ENV="${NINA_ENV:-dev}"
readonly DB_CONTAINER="ninaivalaigal-${ENV}-db"
readonly PGBOUNCER_CONTAINER="ninaivalaigal-${ENV}-pgbouncer"
readonly REDIS_CONTAINER="ninaivalaigal-${ENV}-redis"
readonly API_CONTAINER="ninaivalaigal-${ENV}-api"
readonly CUSTOMER_APP_CONTAINER="ninaivalaigal-${ENV}-customer-app"
readonly ADMIN_CONSOLE_CONTAINER="ninaivalaigal-${ENV}-admin-console"

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ℹ️  $*"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ✅ $*"
}

stop_container() {
    local container_name=$1

    if container list | grep -q "$container_name.*running"; then
        log_info "Stopping $container_name..."
        container stop "$container_name"
        log_success "$container_name stopped"
    else
        log_info "$container_name not running"
    fi
}

main() {
    echo ""
    log_info "═══════════════════════════════════════"
    log_info "Stopping Ninaivalaigal Complete Stack"
    log_info "═══════════════════════════════════════"
    echo ""

    # Stop in reverse order (UIs → API → Redis → PgBouncer → DB)
    stop_container "$ADMIN_CONSOLE_CONTAINER"
    stop_container "$CUSTOMER_APP_CONTAINER"
    stop_container "$API_CONTAINER"
    stop_container "$REDIS_CONTAINER"
    stop_container "$PGBOUNCER_CONTAINER"
    stop_container "$DB_CONTAINER"

    echo ""
    log_success "Complete stack stopped successfully"
    echo ""
}

main "$@"
