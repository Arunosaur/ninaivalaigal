#!/bin/bash
# Start consolidated database (graph-db with relational data)
set -euo pipefail

echo "🚀 Starting Consolidated Database (Apache AGE + Relational)"

# Start graph infrastructure (includes both graph-db and graph-redis)
make start-graph-infrastructure

# Wait for database to be ready
echo "⏳ Waiting for consolidated database..."
sleep 10

# Test connectivity
if container exec ninaivalaigal-graph-db pg_isready -U graphuser -d ninaivalaigal_graph; then
    echo "✅ Consolidated database is ready"
    echo "📊 Database info:"
    container exec ninaivalaigal-graph-db psql -U graphuser -d ninaivalaigal_graph -c "SELECT version();"
    echo "🔗 Connection: DATABASE_URL=\"postgresql://nina:secure_nina_password@${DB_IP}:5432/ninaivalaigal\""  # pragma: allowlist secret_graph
else
    echo "❌ Consolidated database failed to start"
    exit 1
fi
