#!/bin/bash
echo "🚀 Starting Ninaivalaigal servers..."

# Start PostgreSQL
echo "📊 Starting PostgreSQL..."
brew services start postgresql@14

# Wait for database
sleep 3

# Start FastAPI backend
echo "🔧 Starting FastAPI backend..."
cd /Users/asrajag/Workspace/mem0/server
uvicorn main:app --host 127.0.0.1 --port 13370 --reload &
FASTAPI_PID=$!

# Start frontend
echo "🌐 Starting frontend..."
cd /Users/asrajag/Workspace/mem0/frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!

echo "✅ All servers started!"
echo "📱 Frontend: http://localhost:8080/"
echo "🔧 Backend: http://127.0.0.1:13370/"
echo "📚 API Docs: http://127.0.0.1:13370/docs"

# Keep script running
wait
