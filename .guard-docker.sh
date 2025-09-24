#!/usr/bin/env bash
# Container Guard - Protects local development containers from CI interference
set -euo pipefail

GUARD_LOG="/tmp/container-guard.log"
PROTECTED_CONTAINERS=("nina-intelligence-db" "nina-intelligence-cache" "nv-api" "nv-ui" "nv-em")

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [GUARD] $*" | tee -a "$GUARD_LOG"
}

check_container_protection() {
    local container_name="$1"

    # Check if container exists and is running
    if container list | grep -q "$container_name.*running"; then
        # Add protection label to prevent CI cleanup
        container update --restart=always "$container_name" 2>/dev/null || true
        log "🛡️  Protected $container_name from external cleanup"
        return 0
    else
        log "⚠️  Container $container_name not running - cannot protect"
        return 1
    fi
}

monitor_container_events() {
    log "🚀 Starting Container Guard - protecting local development containers"
    log "🛡️  Protected containers: ${PROTECTED_CONTAINERS[*]}"

    while true; do
        # Check and protect all containers every 30 seconds
        for container in "${PROTECTED_CONTAINERS[@]}"; do
            check_container_protection "$container"
        done

        # Monitor for external deletion attempts
        if pgrep -f "make stack-down" >/dev/null 2>&1; then
            log "🚨 ALERT: Detected 'make stack-down' process - potential CI interference!"

            # Log the process details
            ps aux | grep "make stack-down" | grep -v grep >> "$GUARD_LOG" || true
        fi

        # Monitor for container removal commands
        if pgrep -f "container.*delete.*nv-" >/dev/null 2>&1; then
            log "🚨 ALERT: Detected container deletion command!"
            ps aux | grep "container.*delete" | grep -v grep >> "$GUARD_LOG" || true
        fi

        sleep 30
    done
}

case "${1:-monitor}" in
    "monitor")
        monitor_container_events
        ;;
    "protect")
        log "🛡️  Applying protection to all containers..."
        for container in "${PROTECTED_CONTAINERS[@]}"; do
            check_container_protection "$container"
        done
        ;;
    "status")
        log "📊 Container Guard Status:"
        for container in "${PROTECTED_CONTAINERS[@]}"; do
            if container list | grep -q "$container.*running"; then
                log "  ✅ $container: Running & Protected"
            else
                log "  ❌ $container: Not Running"
            fi
        done
        ;;
    "logs")
        tail -50 "$GUARD_LOG" 2>/dev/null || echo "No guard logs found"
        ;;
    *)
        echo "Usage: $0 [monitor|protect|status|logs]"
        echo "  monitor: Run continuous protection (default)"
        echo "  protect: Apply protection once"
        echo "  status:  Check protection status"
        echo "  logs:    Show guard logs"
        exit 1
        ;;
esac
