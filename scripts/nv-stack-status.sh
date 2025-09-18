#!/usr/bin/env bash
# Show comprehensive status of ninaivalaigal stack on Mac Studio

set -euo pipefail

log()  { printf "\033[1;34m[stack]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
success() { printf "\033[1;32m[ok]\033[0m %s\n" "$*"; }

check_service() {
  local name="$1"
  local port="$2"
  local description="$3"
  
  if container list | grep -q "$name"; then
    if nc -z 127.0.0.1 "$port" >/dev/null 2>&1; then
      success "$description: ✅ Running and accessible on port $port"
    else
      warn "$description: ⚠️  Container running but port $port not accessible"
    fi
  else
    warn "$description: ❌ Container not running"
  fi
}

main() {
  log "📊 ninaivalaigal Stack Status (Mac Studio)"
  log "=========================================="
  echo ""
  
  # Container system status
  log "Apple Container CLI:"
  if container system status >/dev/null 2>&1; then
    success "✅ Container system operational"
  else
    warn "❌ Container system not running"
  fi
  echo ""
  
  # Individual service status
  log "Service Status:"
  check_service "nv-db" "5433" "Database (PostgreSQL + pgvector)"
  check_service "nv-pgbouncer" "6432" "PgBouncer (Connection pooler)"  
  check_service "nv-api" "13370" "API Server (FastAPI)"
  echo ""
  
  # Container details
  log "Container Details:"
  echo "ID          IMAGE                             STATE    PORTS"
  echo "----------  --------------------------------  -------  -------------------------"
  container list | grep -E "(nv-db|nv-pgbouncer|nv-api)" || echo "No ninaivalaigal containers running"
  echo ""
  
  # Service URLs and connection strings
  log "Connection Information:"
  if container list | grep -q "nv-db"; then
    echo "  📊 Database (direct):   postgresql://nina:***@localhost:5433/nina"
  fi
  if container list | grep -q "nv-pgbouncer"; then
    echo "  🔄 Database (pooled):   postgresql://nina:***@localhost:6432/nina"
  fi
  if container list | grep -q "nv-api"; then
    echo "  🌐 API Health:          http://localhost:13370/health"
    echo "  📚 API Documentation:   http://localhost:13370/docs"
    echo "  🔗 API Base URL:        http://localhost:13370/"
  fi
  echo ""
  
  # Quick health checks
  log "Health Checks:"
  if container list | grep -q "nv-db"; then
    if container exec nv-db pg_isready -h 127.0.0.1 -p 5432 -U nina -d nina >/dev/null 2>&1; then
      success "✅ Database accepting connections"
    else
      warn "❌ Database not accepting connections"
    fi
  fi
  
  if container list | grep -q "nv-api"; then
    if curl -f http://127.0.0.1:13370/health >/dev/null 2>&1; then
      success "✅ API health endpoint responding"
    else
      warn "❌ API health endpoint not responding"
    fi
  fi
  echo ""
  
  # Management commands
  log "Stack Management:"
  echo "  Start full stack:  ./nv-stack-start.sh"
  echo "  Stop full stack:   ./nv-stack-stop.sh"
  echo "  Database only:     ./nv-stack-start.sh --db-only"
  echo "  Individual:        ./nv-db-start.sh, ./nv-pgbouncer-start.sh, ./nv-api-start.sh"
  echo ""
}

main "$@"
