#!/usr/bin/env bash
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

    while true; do
        local issues=0

        # Check Database
        if ! container list | grep -q "nv-db.*running"; then
            ((issues++))
            log "🚨 DATABASE ISSUE DETECTED - Attempting recreation..."
            safe_container_restart "nv-db" "nv-db-start.sh" || ((issues++))
        fi

        # Check PgBouncer
        if ! container list | grep -q "nv-pgbouncer.*running"; then
            ((issues++))
            log "🚨 PGBOUNCER ISSUE DETECTED - Attempting recreation..."
            safe_container_restart "nv-pgbouncer" "nv-pgbouncer-start.sh" || ((issues++))
        fi

        # Check Redis
        if ! container list | grep -q "nv-redis.*running"; then
            ((issues++))
            log "🚨 REDIS ISSUE DETECTED - Attempting recreation..."
            safe_container_restart "nv-redis" "nv-redis-start.sh" || ((issues++))
        fi

        # Check API with health endpoint
        if ! check_container_health "nv-api" "13370" "nv-api-start.sh"; then
            ((issues++))
        fi

        # Check UI
        if ! container list | grep -q "nv-ui.*running"; then
            ((issues++))
            log "⚠️ UI ISSUE DETECTED - Attempting recreation..."
            safe_container_restart "nv-ui" "nv-ui-start.sh" || ((issues++))
        fi

        # Overall health summary
        if [ $issues -eq 0 ]; then
            log "✅ All systems healthy and running"
        else
            log "⚠️ $issues issues detected and addressed"
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
        safe_container_restart "nv-api" "nv-api-start.sh"
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
