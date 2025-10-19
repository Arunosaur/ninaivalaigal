#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#

# Start minimal ninaivalaigal stack (API + Redis)
# This script starts a minimal working environment for testing Redis fixes

set -e

echo "🚀 Starting ninaivalaigal minimal stack..."

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.minimal.yml down --remove-orphans 2>/dev/null || true

# Clean up any existing containers with same names
echo "🧹 Cleaning up existing containers..."
docker rm -f ninaivalaigal-minimal-redis ninaivalaigal-minimal-api 2>/dev/null || true

# Build and start the minimal stack
echo "🔨 Building and starting minimal stack..."
docker-compose -f docker-compose.minimal.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose -f docker-compose.minimal.yml ps | grep -q "healthy"; then
        redis_healthy=$(docker-compose -f docker-compose.minimal.yml ps redis | grep -c "healthy" || echo "0")
        api_healthy=$(docker-compose -f docker-compose.minimal.yml ps api | grep -c "healthy" || echo "0")

        if [ "$redis_healthy" -eq 1 ] && [ "$api_healthy" -eq 1 ]; then
            echo "✅ All services are healthy!"
            break
        fi
    fi

    echo "⏳ Waiting for services... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Services failed to become healthy within $timeout seconds"
    echo "📋 Container status:"
    docker-compose -f docker-compose.minimal.yml ps
    echo "📋 Container logs:"
    docker-compose -f docker-compose.minimal.yml logs
    exit 1
fi

# Test the services
echo "🧪 Testing services..."

# Test Redis connection
echo "🔍 Testing Redis connection..."
if docker exec ninaivalaigal-minimal-redis redis-cli -a secure_nina_password ping | grep -q "PONG"; then
    echo "✅ Redis is responding"
else
    echo "❌ Redis is not responding"
    exit 1
fi

# Test API health
echo "🔍 Testing API health..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding"
    exit 1
fi

# Test API Redis integration
echo "🔍 Testing API Redis integration..."
if curl -s http://localhost:8000/health/detailed | grep -q "healthy"; then
    echo "✅ API Redis integration is working"
else
    echo "⚠️  API Redis integration may have issues"
    echo "📋 Detailed health response:"
    curl -s http://localhost:8000/health/detailed | jq . 2>/dev/null || curl -s http://localhost:8000/health/detailed
fi

echo ""
echo "🎉 Minimal stack is running!"
echo ""
echo "📍 Available endpoints:"
echo "   • API Health: http://localhost:8000/health"
echo "   • API Detailed Health: http://localhost:8000/health/detailed"
echo "   • API Redis Test: http://localhost:8000/redis/test"
echo "   • API Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Redis connection:"
echo "   • Host: localhost"
echo "   • Port: 6379"
echo "   • Password: secure_nina_password"
echo ""
echo "📋 To view logs: docker-compose -f docker-compose.minimal.yml logs -f"
echo "🛑 To stop: docker-compose -f docker-compose.minimal.yml down"
