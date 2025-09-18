#!/usr/bin/env bash
# Stop the complete ninaivalaigal stack on Mac Studio
# API → PgBouncer → Database in reverse order

set -euo pipefail

log()  { printf "\033[1;34m[stack]\033[0m %s\n" "$*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

main() {
  log "🛑 Stopping ninaivalaigal stack on Mac Studio"
  log "============================================="
  
  # Stop in reverse order for clean shutdown
  log "🌐 Stopping API server..."
  "$SCRIPT_DIR/nv-api-stop.sh" || true
  
  log "🔄 Stopping PgBouncer..."
  "$SCRIPT_DIR/nv-pgbouncer-stop.sh" || true
  
  log "📊 Stopping database..."
  "$SCRIPT_DIR/nv-db-stop.sh" || true
  
  log "✅ Stack shutdown complete!"
  
  # Verify cleanup
  echo ""
  log "Remaining ninaivalaigal containers:"
  if container list | grep -E "(nv-db|nv-pgbouncer|nv-api)"; then
    log "⚠️  Some containers still running"
  else
    log "✅ All containers stopped"
  fi
}

main "$@"
