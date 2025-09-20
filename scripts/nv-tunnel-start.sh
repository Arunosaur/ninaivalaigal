#!/bin/bash
set -euo pipefail

# Secure tunneling for remote access to ninaivalaigal stack
# Supports SSH tunneling and socat for cloud deployment

TUNNEL_TYPE="${TUNNEL_TYPE:-ssh}"
REMOTE_HOST="${REMOTE_HOST:-}"
REMOTE_USER="${REMOTE_USER:-ubuntu}"
LOCAL_API_PORT="${LOCAL_API_PORT:-13370}"
LOCAL_DB_PORT="${LOCAL_DB_PORT:-5433}"
LOCAL_PGB_PORT="${LOCAL_PGB_PORT:-6432}"
REMOTE_API_PORT="${REMOTE_API_PORT:-8080}"
TUNNEL_KEY="${TUNNEL_KEY:-~/.ssh/id_rsa}"

echo "🌐 Starting secure tunnel for ninaivalaigal stack"
echo "================================================"

# Validate required parameters
if [ -z "$REMOTE_HOST" ]; then
    echo "❌ Error: REMOTE_HOST is required"
    echo ""
    echo "Usage examples:"
    echo "  # SSH tunnel to cloud server"
    echo "  REMOTE_HOST=my-server.com ./scripts/nv-tunnel-start.sh"
    echo ""
    echo "  # Custom ports and user"
    echo "  REMOTE_HOST=1.2.3.4 REMOTE_USER=admin REMOTE_API_PORT=9000 ./scripts/nv-tunnel-start.sh"
    echo ""
    echo "Environment variables:"
    echo "  TUNNEL_TYPE     - ssh|socat (default: ssh)"
    echo "  REMOTE_HOST     - Target server hostname/IP (required)"
    echo "  REMOTE_USER     - SSH username (default: ubuntu)"
    echo "  REMOTE_API_PORT - Remote port for API (default: 8080)"
    echo "  LOCAL_API_PORT  - Local API port (default: 13370)"
    echo "  LOCAL_DB_PORT   - Local DB port (default: 5433)"
    echo "  LOCAL_PGB_PORT  - Local PgBouncer port (default: 6432)"
    echo "  TUNNEL_KEY      - SSH key path (default: ~/.ssh/id_rsa)"
    exit 1
fi

# Check if stack is running
if ! curl -s "http://localhost:${LOCAL_API_PORT}/health" >/dev/null 2>&1; then
    echo "⚠️  Local stack not running. Starting development environment..."
    make dev-up
    echo "✅ Local stack is ready"
fi

case "$TUNNEL_TYPE" in
    "ssh")
        echo "🔐 Setting up SSH tunnel to $REMOTE_HOST"
        echo "   Local API:      http://localhost:$LOCAL_API_PORT → $REMOTE_HOST:$REMOTE_API_PORT"
        echo "   Local DB:       localhost:$LOCAL_DB_PORT → $REMOTE_HOST:5432"
        echo "   Local PgBouncer: localhost:$LOCAL_PGB_PORT → $REMOTE_HOST:6432"
        echo ""

        # Check SSH connectivity
        if ! ssh -i "$TUNNEL_KEY" -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_USER@$REMOTE_HOST" exit 2>/dev/null; then
            echo "❌ SSH connection failed. Please check:"
            echo "   - SSH key: $TUNNEL_KEY"
            echo "   - Remote host: $REMOTE_HOST"
            echo "   - Remote user: $REMOTE_USER"
            exit 1
        fi

        echo "✅ SSH connectivity verified"
        echo ""
        echo "🚀 Starting SSH tunnels..."

        # Create SSH tunnels (reverse tunnels to expose local services remotely)
        ssh -i "$TUNNEL_KEY" -N -R "$REMOTE_API_PORT:localhost:$LOCAL_API_PORT" "$REMOTE_USER@$REMOTE_HOST" &
        SSH_PID_API=$!

        ssh -i "$TUNNEL_KEY" -N -R "5432:localhost:$LOCAL_DB_PORT" "$REMOTE_USER@$REMOTE_HOST" &
        SSH_PID_DB=$!

        ssh -i "$TUNNEL_KEY" -N -R "6432:localhost:$LOCAL_PGB_PORT" "$REMOTE_USER@$REMOTE_HOST" &
        SSH_PID_PGB=$!

        # Save PIDs for cleanup
        echo "$SSH_PID_API" > /tmp/nv-tunnel-api.pid
        echo "$SSH_PID_DB" > /tmp/nv-tunnel-db.pid
        echo "$SSH_PID_PGB" > /tmp/nv-tunnel-pgb.pid

        sleep 3

        echo "✅ SSH tunnels established!"
        echo ""
        echo "🌍 Remote access URLs:"
        echo "   API Health:     http://$REMOTE_HOST:$REMOTE_API_PORT/health"
        echo "   API Docs:       http://$REMOTE_HOST:$REMOTE_API_PORT/docs"
        echo "   API Metrics:    http://$REMOTE_HOST:$REMOTE_API_PORT/metrics"
        echo ""
        echo "📊 Database access:"
        echo "   PostgreSQL:     postgresql://nina:change_me_securely@$REMOTE_HOST:5432/nina"  # pragma: allowlist secret
        echo "   PgBouncer:      postgresql://nina:change_me_securely@$REMOTE_HOST:6432/nina"  # pragma: allowlist secret
        echo ""
        echo "🛑 To stop tunnels: ./scripts/nv-tunnel-stop.sh"
        echo ""
        echo "📝 Tunnel processes running in background (PIDs: $SSH_PID_API, $SSH_PID_DB, $SSH_PID_PGB)"
        ;;

    "socat")
        echo "🔗 Setting up socat tunnels to $REMOTE_HOST"
        echo "   Note: socat requires the remote server to have socat installed"
        echo ""

        # Check if socat is available locally
        if ! command -v socat >/dev/null 2>&1; then
            echo "❌ socat not found. Installing via Homebrew..."
            brew install socat
        fi

        echo "🚀 Starting socat tunnels..."

        # Create socat tunnels
        socat TCP-LISTEN:"$REMOTE_API_PORT",fork TCP:localhost:"$LOCAL_API_PORT" &
        SOCAT_PID_API=$!

        # Save PIDs for cleanup
        echo "$SOCAT_PID_API" > /tmp/nv-tunnel-socat-api.pid

        echo "✅ socat tunnel established!"
        echo ""
        echo "🌍 Remote access URL:"
        echo "   API: http://$REMOTE_HOST:$REMOTE_API_PORT"
        echo ""
        echo "🛑 To stop tunnel: ./scripts/nv-tunnel-stop.sh"
        ;;

    *)
        echo "❌ Unknown tunnel type: $TUNNEL_TYPE"
        echo "   Supported types: ssh, socat"
        exit 1
        ;;
esac

echo ""
echo "✨ Tunnel setup complete! Your ninaivalaigal stack is now accessible remotely."
