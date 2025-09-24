#!/usr/bin/env bash
# Nina Intelligence Stack Status Script
# Shows comprehensive status of the consolidated stack

set -euo pipefail

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [NINA-STACK] $*"
}

echo "📊 Nina Intelligence Stack Status"
echo "=================================="

# Check container status
echo ""
echo "🐳 Container Status:"
echo "-------------------"

CONTAINERS=("nina-intelligence-db" "nina-intelligence-cache" "nv-api" "nv-ui" "nv-em")
for container in "${CONTAINERS[@]}"; do
  if container list | grep -q "$container.*running"; then
    IP=$(container list | grep "$container" | awk '{print $NF}')
    echo "  ✅ $container: Running ($IP)"
  else
    echo "  ❌ $container: Not Running"
  fi
done

echo ""
echo "🔗 Service Health:"
echo "------------------"

# Database health
if container list | grep -q "nina-intelligence-db.*running"; then
  if container exec nina-intelligence-db pg_isready -U nina -d ninaivalaigal >/dev/null 2>&1; then
    echo "  ✅ Database: Healthy"

    # Check extensions
    EXTENSIONS=$(container exec nina-intelligence-db psql -U nina -d ninaivalaigal -t -c "SELECT string_agg(extname || ' ' || extversion, ', ') FROM pg_extension WHERE extname IN ('age', 'vector');" 2>/dev/null | xargs)
    echo "     Extensions: $EXTENSIONS"

    # Check user count
    USER_COUNT=$(container exec nina-intelligence-db psql -U nina -d ninaivalaigal -t -c "SELECT count(*) FROM users;" 2>/dev/null | xargs)
    echo "     Users: $USER_COUNT"
  else
    echo "  ❌ Database: Unhealthy"
  fi
else
  echo "  ❌ Database: Not Running"
fi

# Redis health
if container list | grep -q "nina-intelligence-cache.*running"; then
  if container exec nina-intelligence-cache redis-cli ping >/dev/null 2>&1; then
    echo "  ✅ Cache: Healthy"

    # Check memory usage
    MEMORY=$(container exec nina-intelligence-cache redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo "     Memory: $MEMORY"
  else
    echo "  ❌ Cache: Unhealthy"
  fi
else
  echo "  ❌ Cache: Not Running"
fi

# API health
if container list | grep -q "nv-api.*running"; then
  if curl -s http://localhost:13370/health >/dev/null 2>&1; then
    echo "  ✅ API: Healthy"
    echo "     Endpoint: http://localhost:13370"
  else
    echo "  ❌ API: Unhealthy"
  fi
else
  echo "  ❌ API: Not Running"
fi

# UI health
if container list | grep -q "nv-ui.*running"; then
  if curl -s http://localhost:8081/health >/dev/null 2>&1; then
    echo "  ✅ UI: Healthy"
    echo "     Endpoint: http://localhost:8081"
  else
    echo "  ❌ UI: Unhealthy"
  fi
else
  echo "  ❌ UI: Not Running"
fi

echo ""
echo "🌐 Network Endpoints:"
echo "--------------------"
echo "  Database: localhost:5432 (nina/ninaivalaigal)"
echo "  Cache:    localhost:6379"
echo "  API:      http://localhost:13370"
echo "  UI:       http://localhost:8081"
echo "  Health:   http://localhost:13370/health"
echo "  Docs:     http://localhost:13370/docs"

echo ""
echo "🔧 Quick Commands:"
echo "-----------------"
echo "  Start:  make nina-stack-up"
echo "  Stop:   make nina-stack-down"
echo "  Logs:   container logs nina-intelligence-db"
echo "  DB:     container exec nina-intelligence-db psql -U nina -d ninaivalaigal"
echo "  Cache:  container exec nina-intelligence-cache redis-cli"
