#!/usr/bin/env bash
# Switch Container Runtime
# Usage: ./switch-runtime.sh [docker|colima|apple]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_ROOT/.runtime-config"

log() { printf "\033[1;32m[switch]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die() { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 [docker|colima|apple]"
    echo ""
    echo "Current runtime:"
    [ -f "$CONFIG_FILE" ] && grep ACTIVE_RUNTIME "$CONFIG_FILE" || echo "  Not configured"
    exit 1
fi

NEW_RUNTIME=$1

# Validate runtime
case "$NEW_RUNTIME" in
    docker|colima|apple)
        ;;
    *)
        die "Invalid runtime: $NEW_RUNTIME. Valid options: docker, colima, apple"
        ;;
esac

log "Switching to $NEW_RUNTIME runtime..."

# Stop all running containers from current runtime
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    log "Stopping containers for current runtime: $ACTIVE_RUNTIME"

    case "$ACTIVE_RUNTIME" in
        apple)
            container list | grep -E 'nv-' | awk '{print $1}' | xargs -I {} container stop {} 2>/dev/null || true
            ;;
        docker|colima)
            docker-compose -f "$PROJECT_ROOT/compose.docker.yml" down 2>/dev/null || true
            docker stop $(docker ps -q --filter name=ninaivalaigal) 2>/dev/null || true
            ;;
    esac
fi

# Update config file
cat > "$CONFIG_FILE" <<EOF
# Ninaivalaigal Container Runtime Configuration
# Valid values: docker | colima | apple
# Change this to switch between container runtimes
ACTIVE_RUNTIME=$NEW_RUNTIME

# Health monitoring enabled (true/false)
HEALTH_MONITORING_ENABLED=true

# Auto-restart on failure (true/false)
AUTO_RESTART_ENABLED=false
EOF

log "✅ Runtime switched to: $NEW_RUNTIME"
log ""
log "Next steps:"
log "  1. Start stack: make stack-up"
log "  2. Check health: make health-check"
log ""
log "To enable auto-restart, edit .runtime-config and set AUTO_RESTART_ENABLED=true"
