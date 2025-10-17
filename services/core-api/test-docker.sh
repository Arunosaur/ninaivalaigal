#!/usr/bin/env bash
# Test Core API Docker Compose setup

set -e

echo "🧪 Testing Core API Docker Compose Setup"
echo "========================================="

cd /Users/swami/WorkSpace/ninaivalaigal

# Export environment variables
export DB_PASSWORD=dev_password_change_in_production
export JWT_SECRET=dev_jwt_secret_change_in_production

echo ""
echo "1️⃣  Testing Docker Compose configuration..."
docker-compose -f docker/docker-compose.dev.yml config core-api > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

echo ""
echo "2️⃣  Testing Dockerfile..."
docker build -f services/core-api/Dockerfile -t core-api-test:latest . > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Dockerfile builds successfully"
else
    echo "❌ Dockerfile build failed"
    exit 1
fi

echo ""
echo "3️⃣  Testing dependencies in container..."
docker run --rm core-api-test:latest pip list | grep -E "fastapi|sqlalchemy|structlog" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Key dependencies are installed"
else
    echo "❌ Some dependencies are missing"
    exit 1
fi

echo ""
echo "4️⃣  Testing shared utilities in container..."
docker run --rm core-api-test:latest python -c "from database import DatabaseManager; from utils.auth import hash_password; print('✅ Imports work')"
if [ $? -eq 0 ]; then
    echo "✅ Shared utilities are accessible"
else
    echo "❌ Shared utilities import failed"
    exit 1
fi

echo ""
echo "5️⃣  Testing application structure..."
docker run --rm core-api-test:latest ls -la /app | grep -E "main_with_auth.py|routers" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Application files are present"
else
    echo "❌ Application files missing"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ ALL DOCKER TESTS PASSED!"
echo "========================================="
echo ""
echo "🚀 Ready to start with docker-compose:"
echo "   ./docker-start.sh"
echo ""
echo "Or manually:"
echo "   cd /Users/swami/WorkSpace/ninaivalaigal"
echo "   docker-compose -f docker/docker-compose.dev.yml up -d core-api"
echo ""
