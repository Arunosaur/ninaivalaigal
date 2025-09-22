#!/bin/bash
# Production MCP Server Startup Script for mem0
# Ensures proper environment and graceful startup/shutdown

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PROJECT_ROOT/server"
PID_FILE="$PROJECT_ROOT/mcp_server.pid"
LOG_FILE="$PROJECT_ROOT/logs/mcp_server.log"

# Create logs directory
mkdir -p "$PROJECT_ROOT/logs"

# Environment setup
export NINAIVALAIGAL_DATABASE_URL="${NINAIVALAIGAL_DATABASE_URL:-sqlite:///$PROJECT_ROOT/ninaivalaigal.db}"
export NINAIVALAIGAL_JWT_SECRET="${NINAIVALAIGAL_JWT_SECRET:-your-secret-key-here}"
export PYTHONPATH="$SERVER_DIR:$PYTHONPATH"

# Functions
start_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "MCP server already running (PID: $PID)"
            return 0
        else
            echo "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    echo "Starting mem0 MCP server..."
    echo "Database: $NINAIVALAIGAL_DATABASE_URL"
    echo "Log file: $LOG_FILE"

    cd "$SERVER_DIR"
    python mcp_server.py > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!

    echo "$SERVER_PID" > "$PID_FILE"
    echo "MCP server started (PID: $SERVER_PID)"

    # Wait a moment to check if it started successfully
    sleep 2
    if ! ps -p "$SERVER_PID" > /dev/null 2>&1; then
        echo "ERROR: MCP server failed to start. Check log: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi

    echo "✅ MCP server running successfully"
}

stop_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Stopping MCP server (PID: $PID)..."
            kill "$PID"

            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! ps -p "$PID" > /dev/null 2>&1; then
                    break
                fi
                sleep 1
            done

            # Force kill if still running
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Force killing MCP server..."
                kill -9 "$PID"
            fi

            rm -f "$PID_FILE"
            echo "✅ MCP server stopped"
        else
            echo "MCP server not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "MCP server not running (no PID file)"
    fi
}

status_server() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ MCP server running (PID: $PID)"
            return 0
        else
            echo "❌ MCP server not running (stale PID file)"
            return 1
        fi
    else
        echo "❌ MCP server not running"
        return 1
    fi
}

test_server() {
    echo "Testing MCP server functionality..."
    cd "$PROJECT_ROOT"
    python tests/test_mcp_server_basic.py
}

# Main command handling
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        start_server
        ;;
    status)
        status_server
        ;;
    test)
        test_server
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo "No log file found: $LOG_FILE"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the MCP server"
        echo "  stop    - Stop the MCP server"
        echo "  restart - Restart the MCP server"
        echo "  status  - Check server status"
        echo "  test    - Run MCP server tests"
        echo "  logs    - Follow server logs"
        exit 1
        ;;
esac
