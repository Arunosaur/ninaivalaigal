#!/bin/bash
# Start Ninaivalaigal server with proper JWT configuration

echo "🚀 Starting Ninaivalaigal server..."

# Set JWT secret
export NINAIVALAIGAL_JWT_SECRET="gAMpvQggENkOYTc+hMh0UXdV5qxOnM5jVXIRFzk+D/8="

# Kill any existing server
pkill -f "uvicorn.*main:app" 2>/dev/null

# Start server
cd /Users/asrajag/Workspace/mem0/server
uvicorn main:app --host 127.0.0.1 --port 13370 --reload
