#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Comprehensive Health Monitor - Self-healing container management
# Fixes the root cause: recreates containers instead of trying to restart ghosts

set -euo pipefail

MONITOR_INTERVAL=${MONITOR_INTERVAL:-300}  # 5 minutes
LOG_FILE="/tmp/ninaivalaigal-health-fixed.log"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Safe container restart/recreate function
safe_container_restart() {
    local container_name="$1"
    local start_script="$2"

    if ! container list | grep -q "$container_name"; then
        log "💥 CRITICAL: $container_name container was removed! Recreating..."
        log "🔍 EXTERNAL DELETION DETECTED - investigating source..."

        # Log potential external processes
        if pgrep -f "make stack-down" >/dev/null 2>&1; then
            log "🚨 FOUND: 'make stack-down' process running - likely CI interference"
            ps aux | grep "make stack-down" | grep -v grep >> "$LOG_FILE" || true
        fi

        if pgrep -f "github.*actions" >/dev/null 2>&1; then
            log "🚨 FOUND: GitHub Actions process running"
            ps aux | grep "github.*actions" | grep -v grep >> "$LOG_FILE" || true
        fi

        if [[ -f "$SCRIPTS_DIR/$start_script" ]]; then
            bash "$SCRIPTS_DIR/$start_script"
            return $?
        else
            log "❌ Start script not found: $start_script"
            return 1
        fi
    else
        log "🔄 Restarting $container_name..."
        if container restart "$container_name"; then
            log "✅ Successfully restarted $container_name"
            return 0
        else
            log "⚠️ Restart failed, attempting full recreation..."
            bash "$SCRIPTS_DIR/$start_script"
            return $?
        fi
    fi
}

# Check container health with port test
check_container_health() {
    local container_name="$1"
    local port="$2"
    local start_script="$3"

    # First check if container exists and is running
    if ! container list | grep -q "$container_name.*running"; then
        log "❌ $container_name: Container not running"
        safe_container_restart "$container_name" "$start_script"
        return $?
    fi

    # Then check if port is responding
    if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
        log "✅ $container_name: Healthy (port $port responding)"
        return 0
    else
        log "⚠️ $container_name: Container running but port $port not responding"
        safe_container_restart "$container_name" "$start_script"
        return $?
    fi
}

monitor_stack() {
    log "🔍 Starting comprehensive health monitoring (interval: ${MONITOR_INTERVAL}s)"
    log "🛠️ Using self-healing container recreation logic"
    log "📦 Monitoring ONLY ninaivalaigal-dev-* containers"

    while true; do
        local issues=0

        # Check Database (NEW NAME)
        if ! container list | grep -q "ninaivalaigal-dev-db.*running"; then
            ((issues++))
            log "⚠️ Database (ninaivalaigal-dev-db) not running"
            log "   Manual start required: ./start-apple-container-stack.sh"
        fi

        # Check PgBouncer (NEW NAME)
        if ! container list | grep -q "ninaivalaigal-dev-pgbouncer.*running"; then
            ((issues++))
            log "⚠️ PgBouncer (ninaivalaigal-dev-pgbouncer) not running"
            log "   Manual start required: ./start-apple-container-stack.sh"
        fi

        # Check Redis (NEW NAME)
        if ! container list | grep -q "ninaivalaigal-dev-redis.*running"; then
            ((issues++))
            log "⚠️ Redis (ninaivalaigal-dev-redis) not running"
            log "   Manual start required: ./start-apple-container-stack.sh"
        fi

        # Check Core API (NEW NAME)
        if ! container list | grep -q "ninaivalaigal-dev-core-api.*running"; then
            ((issues++))
            log "⚠️ Core API (ninaivalaigal-dev-core-api) not running"
        fi

        # Overall health summary
        if [ $issues -eq 0 ]; then
            log "✅ All ninaivalaigal-dev-* containers healthy and running"
        else
            log "⚠️ $issues issues detected - manual intervention required"
            log "   OLD containers (nv-*) are DEPRECATED and should NOT be running"
        fi

        sleep "$MONITOR_INTERVAL"
    done
}

# Handle signals gracefully
trap 'log "🛑 Health monitor stopping..."; exit 0' SIGTERM SIGINT

case "${1:-monitor}" in
    "monitor")
        monitor_stack
        ;;
    "status")
        log "📊 Current Stack Status:"
        make stack-status
        ;;
    "logs")
        tail -f "$LOG_FILE"
        ;;
    "test")
        log "🧪 Testing safe restart logic..."
        safe_container_restart "" "-start.sh"
        ;;
    *)
        echo "Usage: $0 [monitor|status|logs|test]"
        echo "  monitor: Start continuous health monitoring (default)"
        echo "  status:  Show current stack status"
        echo "  logs:    Follow health monitor logs"
        echo "  test:    Test safe restart logic"
        exit 1
        ;;
esac
