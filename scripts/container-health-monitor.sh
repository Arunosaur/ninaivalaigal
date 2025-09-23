#!/usr/bin/env bash
# Container Health Monitor - Prevents future stack disruptions
set -euo pipefail

MONITOR_INTERVAL=${MONITOR_INTERVAL:-300}  # 5 minutes
LOG_FILE="/tmp/ninaivalaigal-health.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

check_container_health() {
    local container_name="$1"
    local port="$2"

    if container list | grep -q "$container_name.*running"; then
        if curl -f "http://localhost:$port/health" >/dev/null 2>&1; then
            log "✅ $container_name: Healthy (port $port responding)"
            return 0
        else
            log "⚠️ $container_name: Container running but port $port not responding"
            return 1
        fi
    else
        log "❌ $container_name: Container not running"
        return 1
    fi
}

monitor_stack() {
    log "🔍 Starting container health monitoring (interval: ${MONITOR_INTERVAL}s)"

    while true; do
        local issues=0

        # Check API
        if ! check_container_health "nv-api" "13370"; then
            ((issues++))
            log "🚨 API ISSUE DETECTED - Attempting restart..."
            container restart nv-api || log "❌ Failed to restart nv-api"
        fi

        # Check UI
        if ! check_container_health "nv-ui" "8080"; then
            ((issues++))
            log "⚠️ UI issue detected"
        fi

        # Check database connectivity
        if ! curl -f "http://localhost:13370/health/detailed" >/dev/null 2>&1; then
            ((issues++))
            log "🚨 DATABASE CONNECTIVITY ISSUE"
        fi

        if [ $issues -eq 0 ]; then
            log "✅ All systems healthy"
        else
            log "⚠️ $issues issues detected - check logs above"
        fi

        sleep "$MONITOR_INTERVAL"
    done
}

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
    *)
        echo "Usage: $0 [monitor|status|logs]"
        exit 1
        ;;
esac
