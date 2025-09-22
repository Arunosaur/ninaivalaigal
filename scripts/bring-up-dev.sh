#!/bin/bash
set -euo pipefail

# Bring up all core services and GraphOps for development

echo "🚀 [+] Starting full dev stack..."

# Check if we have the main stack scripts
if [ -f "scripts/nv-stack-start.sh" ]; then
    echo "📦 Starting main stack (nv-db, nv-redis, nv-api)..."
    ./scripts/nv-stack-start.sh
    sleep 5
else
    echo "⚠️  Main stack scripts not found, using Docker Compose fallback..."
    if [ -f "docker-compose.dev.yml" ]; then
        docker-compose -f docker-compose.dev.yml up -d
        sleep 5
    else
        echo "❌ No docker-compose.dev.yml found"
    fi
fi

# Start GraphOps stack
echo "🌐 Starting GraphOps stack (Apache AGE + Redis)..."
make start-graph-infrastructure

# Health check
echo "🏥 Checking service health..."
sleep 10

echo "📊 Service Status:"
container list | grep -E "(nv-|ninaivalaigal-)" || echo "No containers running"

echo "🎉 Dev stack startup complete!"
echo ""
echo "📋 Available Services:"
echo "  • Main DB (PostgreSQL + pgvector): localhost:5433"
echo "  • Main Redis: localhost:6379"
echo "  • Main API: localhost:13370"
echo "  • Graph DB (Apache AGE): localhost:5434"
echo "  • Graph Redis: localhost:6381"
echo ""
echo "🔍 Health Endpoints:"
echo "  • curl http://localhost:13370/health"
echo "  • curl http://localhost:13370/health/detailed"
echo "  • curl http://localhost:13370/metrics"
