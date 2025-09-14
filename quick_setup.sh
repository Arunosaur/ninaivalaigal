#!/bin/bash
# Quick JWT Authentication Setup for Ninaivalaigal

echo "🔧 Setting up JWT authentication..."

# Kill any existing servers
pkill -f "uvicorn.*main:app" 2>/dev/null

# Set environment variables for this session
export NINAIVALAIGAL_JWT_SECRET="gAMpvQggENkOYTc+hMh0UXdV5qxOnM5jVXIRFzk+D/8="
export NINAIVALAIGAL_USER_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJlbWFpbCI6ImR1cmFpQGV4YW1wbGUuY29tIiwiYWNjb3VudF90eXBlIjoiaW5kaXZpZHVhbCIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzYwNDg2ODE4fQ.KEMlv46BYE5AYCaHTmplpg-Rx6SMjDni0FDsDF3HjPk"

echo "✅ Environment variables set"

# Start server in background
cd /Users/asrajag/Workspace/mem0/server
nohup uvicorn main:app --host 127.0.0.1 --port 13370 > /tmp/mem0_server.log 2>&1 &
SERVER_PID=$!

echo "🚀 Server starting (PID: $SERVER_PID)..."
sleep 3

# Test authentication
echo "🧪 Testing authentication..."
python3 /Users/asrajag/Workspace/mem0/mem0 contexts

echo ""
echo "✅ Setup complete! Use these commands:"
echo "  eM contexts"
echo "  eM start --context test"
echo "  eM remember '{\"data\": \"test\"}' --context test"
echo ""
echo "To stop server: kill $SERVER_PID"
