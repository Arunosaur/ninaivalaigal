#!/usr/bin/env bash
# Stop Core API service

set -e

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-core-api"

echo "🛑 Stopping Core API Service"
echo "============================="
echo ""

if container stop "$CONTAINER_NAME" 2>/dev/null; then
    echo "✅ Container stopped: $CONTAINER_NAME"
    
    if container rm "$CONTAINER_NAME" 2>/dev/null; then
        echo "✅ Container removed: $CONTAINER_NAME"
    fi
else
    echo "⚠️  Container not running: $CONTAINER_NAME"
fi

echo ""
echo "✅ Core API service stopped"
