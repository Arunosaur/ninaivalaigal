#!/usr/bin/env bash
# Start the complete ninaivalaigal stack on Mac Studio
# Database → PgBouncer → API in sequence

set -euo pipefail

log()  { printf "\033[1;34m[stack]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die()  { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse options
SKIP_DB=false
SKIP_PGBOUNCER=false
SKIP_API=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --skip-db)
      SKIP_DB=true
      shift
      ;;
    --skip-pgbouncer)
      SKIP_PGBOUNCER=true
      shift
      ;;
    --skip-api)
      SKIP_API=true
      shift
      ;;
    --db-only)
      SKIP_PGBOUNCER=true
      SKIP_API=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --skip-db         Skip database startup"
      echo "  --skip-pgbouncer  Skip PgBouncer startup"
      echo "  --skip-api        Skip API startup"
      echo "  --db-only         Start only database (skip PgBouncer and API)"
      echo "  --help            Show this help"
      exit 0
      ;;
    *)
      warn "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

main() {
  log "🚀 Starting ninaivalaigal stack on Mac Studio"
  log "============================================="
  
  # Step 1: Database
  if [ "$SKIP_DB" = false ]; then
    log "📊 Step 1: Starting PostgreSQL + pgvector..."
    "$SCRIPT_DIR/nv-db-start.sh"
    echo ""
  else
    log "📊 Step 1: Skipping database (--skip-db)"
  fi
  
  # Step 2: PgBouncer
  if [ "$SKIP_PGBOUNCER" = false ]; then
    log "🔄 Step 2: Starting PgBouncer connection pooler..."
    "$SCRIPT_DIR/nv-pgbouncer-start.sh"
    echo ""
  else
    log "🔄 Step 2: Skipping PgBouncer (--skip-pgbouncer)"
  fi
  
  # Step 3: API
  if [ "$SKIP_API" = false ]; then
    log "🌐 Step 3: Starting ninaivalaigal API server..."
    "$SCRIPT_DIR/nv-api-start.sh"
    echo ""
  else
    log "🌐 Step 3: Skipping API (--skip-api)"
  fi
  
  # Summary
  log "✅ Stack startup complete!"
  log "========================="
  echo ""
  
  # Show running containers
  log "Running containers:"
  container list | head -1  # Header
  container list | grep -E "(nv-db|nv-pgbouncer|nv-api)" || echo "No ninaivalaigal containers running"
  echo ""
  
  # Show service URLs
  log "Service URLs:"
  if [ "$SKIP_DB" = false ]; then
    echo "  📊 Database (direct):  postgresql://nina:***@localhost:5433/nina"
  fi
  if [ "$SKIP_PGBOUNCER" = false ]; then
    echo "  🔄 Database (pooled):  postgresql://nina:***@localhost:6432/nina"
  fi
  if [ "$SKIP_API" = false ]; then
    echo "  🌐 API Health:         http://localhost:13370/health"
    echo "  📚 API Docs:           http://localhost:13370/docs"
  fi
  echo ""
  
  log "Stack management:"
  echo "  Status:  ./nv-stack-status.sh"
  echo "  Stop:    ./nv-stack-stop.sh"
  echo "  Restart: ./nv-stack-stop.sh && ./nv-stack-start.sh"
}

main "$@"
