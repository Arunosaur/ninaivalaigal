#!/bin/bash
set -euo pipefail

# Stop secure tunnels for ninaivalaigal stack

echo "🛑 Stopping ninaivalaigal tunnels"
echo "================================="

# Stop SSH tunnels
if [ -f /tmp/nv-tunnel-api.pid ]; then
    API_PID=$(cat /tmp/nv-tunnel-api.pid)
    if kill -0 "$API_PID" 2>/dev/null; then
        kill "$API_PID"
        echo "✅ Stopped SSH tunnel for API (PID: $API_PID)"
    fi
    rm -f /tmp/nv-tunnel-api.pid
fi

if [ -f /tmp/nv-tunnel-db.pid ]; then
    DB_PID=$(cat /tmp/nv-tunnel-db.pid)
    if kill -0 "$DB_PID" 2>/dev/null; then
        kill "$DB_PID"
        echo "✅ Stopped SSH tunnel for DB (PID: $DB_PID)"
    fi
    rm -f /tmp/nv-tunnel-db.pid
fi

if [ -f /tmp/nv-tunnel-pgb.pid ]; then
    PGB_PID=$(cat /tmp/nv-tunnel-pgb.pid)
    if kill -0 "$PGB_PID" 2>/dev/null; then
        kill "$PGB_PID"
        echo "✅ Stopped SSH tunnel for PgBouncer (PID: $PGB_PID)"
    fi
    rm -f /tmp/nv-tunnel-pgb.pid
fi

# Stop socat tunnels
if [ -f /tmp/nv-tunnel-socat-api.pid ]; then
    SOCAT_PID=$(cat /tmp/nv-tunnel-socat-api.pid)
    if kill -0 "$SOCAT_PID" 2>/dev/null; then
        kill "$SOCAT_PID"
        echo "✅ Stopped socat tunnel for API (PID: $SOCAT_PID)"
    fi
    rm -f /tmp/nv-tunnel-socat-api.pid
fi

# Clean up any remaining tunnel processes
pkill -f "ssh.*ninaivalaigal" 2>/dev/null || true
pkill -f "socat.*13370" 2>/dev/null || true

echo ""
echo "✅ All tunnels stopped. Remote access disabled."
