#!/usr/bin/env bash
# Nina Intelligence Stack Health Monitor
# Monitors and maintains the consolidated nina-intelligence-db + nina-intelligence-cache + API stack

set -euo pipefail

MONITOR_INTERVAL=${MONITOR_INTERVAL:-300}  # 5 minutes
LOG_FILE="/tmp/nina-intelligence-health.log"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [NINA-HEALTH] $*" | tee -a "$LOG_FILE"
}

# Health check function for nina-intelligence stack
check_nina_intelligence_health() {
    local issues=0

    # Check nina-intelligence-db
    if ! container list | grep -q "nina-intelligence-db.*running"; then
        log "🚨 nina-intelligence-db: Not running - attempting restart"
        make nina-stack-up >/dev/null 2>&1 || log "❌ Failed to restart nina-intelligence-db"
        ((issues++))
    else
        # Check database health
        if ! container exec nina-intelligence-db pg_isready -U nina -d ninaivalaigal >/dev/null 2>&1; then
            log "⚠️ nina-intelligence-db: Database not ready"
            ((issues++))
        fi
    fi

    # Check nina-intelligence-cache
    if ! container list | grep -q "nina-intelligence-cache.*running"; then
        log "🚨 nina-intelligence-cache: Not running - attempting restart"
        make nina-stack-up >/dev/null 2>&1 || log "❌ Failed to restart nina-intelligence-cache"
        ((issues++))
    else
        # Check Redis health
        if ! container exec nina-intelligence-cache redis-cli ping >/dev/null 2>&1; then
            log "⚠️ nina-intelligence-cache: Redis not responding"
            ((issues++))
        fi
    fi

    # Check nv-api
    if ! container list | grep -q "nv-api.*running"; then
        log "🚨 nv-api: Not running - attempting restart"
        make nina-stack-up >/dev/null 2>&1 || log "❌ Failed to restart nv-api"
        ((issues++))
    else
        # Check API health
        if ! curl -s http://localhost:13370/health >/dev/null 2>&1; then
            log "⚠️ nv-api: Health endpoint not responding"
            ((issues++))
        fi
    fi

    # Check nv-ui
    if ! container list | grep -q "nv-ui.*running"; then
        log "🚨 nv-ui: Not running - attempting restart"
        make nina-stack-up >/dev/null 2>&1 || log "❌ Failed to restart nv-ui"
        ((issues++))
    else
        # Check UI health
        if ! curl -s http://localhost:8081/health >/dev/null 2>&1; then
            log "⚠️ nv-ui: Health endpoint not responding"
            ((issues++))
        fi
    fi

    if [ $issues -eq 0 ]; then
        log "✅ Nina Intelligence Stack: All services healthy"
    else
        log "⚠️ Nina Intelligence Stack: $issues issues detected and addressed"
    fi

    return $issues
}

# Performance monitoring
monitor_performance() {
    # Database connections
    local db_connections=$(container exec nina-intelligence-db psql -U nina -d ninaivalaigal -t -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | xargs || echo "0")

    # Redis memory usage
    local redis_memory=$(container exec nina-intelligence-cache redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r' || echo "unknown")

    # API response time
    local api_response_time=$(curl -s -w "%{time_total}" -o /dev/null http://localhost:13370/health 2>/dev/null || echo "timeout")

    log "📊 Performance: DB connections: $db_connections, Redis memory: $redis_memory, API response: ${api_response_time}s"
}

# Main monitoring loop
monitor_loop() {
    log "🚀 Starting Nina Intelligence Stack Health Monitor (interval: ${MONITOR_INTERVAL}s)"

    while true; do
        check_nina_intelligence_health
        monitor_performance

        log "😴 Sleeping for $MONITOR_INTERVAL seconds..."
        sleep "$MONITOR_INTERVAL"
    done
}

# Handle different modes
case "${1:-monitor}" in
    "monitor")
        monitor_loop
        ;;
    "check")
        check_nina_intelligence_health
        ;;
    "performance")
        monitor_performance
        ;;
    *)
        echo "Usage: $0 [monitor|check|performance]"
        exit 1
        ;;
esac
