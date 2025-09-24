#!/usr/bin/env bash
# Nina Intelligence Stack Stop Script
# Gracefully stops the consolidated nina-intelligence stack

set -euo pipefail

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [NINA-STACK] $*"
}

log "🛑 Stopping Nina Intelligence Stack..."

# Stop in reverse order: UI -> API -> Cache -> Database
CONTAINERS_TO_STOP=("nv-ui" "nv-api" "nina-intelligence-cache" "nina-intelligence-db")

for container in "${CONTAINERS_TO_STOP[@]}"; do
  if container list | grep -q "$container.*running"; then
    log "Stopping $container..."
    container stop "$container" || log "Failed to stop $container"
  else
    log "$container not running, skipping."
  fi
done

log "✅ Nina Intelligence Stack stopped."

# Show final status
log "📊 Final status:"
container list | grep -E "(nina-intelligence|nv-api|nv-ui)" || log "All nina intelligence containers stopped."
