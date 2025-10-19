#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# As Developer A, I'm running the Task #29 completion

echo "👋 Developer A starting Task #29 completion"
echo "============================================="
echo ""

# Create results directory
mkdir -p /Users/swami/WorkSpace/ninaivalaigal/task29_results

# First, let's check what services are running
echo "🔍 Checking service status..."

# Check memory service
if curl -sf http://localhost:13393/health > /dev/null 2>&1; then
    echo "✅ Memory service is running on port 13393"
    echo "📊 Getting health status..."
    curl -s http://localhost:13393/health | jq '.' > /Users/swami/WorkSpace/ninaivalaigal/task29_results/health_status.json 2>/dev/null || curl -s http://localhost:13393/health > /Users/swami/WorkSpace/ninaivalaigal/task29_results/health_status.txt
else
    echo "❌ Memory service not running - checking if we can start it..."

    # Try to start the memory service
    if [ -f "/Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/nv-memory-service-start.sh" ]; then
        echo "🚀 Attempting to start memory service..."
        cd /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service || exit
        ./nv-memory-service-start.sh &
        echo "⏳ Waiting for service to start..."
        sleep 10

        if curl -sf http://localhost:13393/health > /dev/null 2>&1; then
            echo "✅ Memory service started successfully"
        else
            echo "❌ Failed to start memory service"
            echo "   Continuing with available tests..."
        fi
    fi
fi

# Check API service
echo ""
echo "🔍 Checking API service..."
if curl -sf http://localhost:13390/health > /dev/null 2>&1; then
    echo "✅ API service is running on port 13390"
else
    echo "⚠️  API service not running - will use mock JWT token"
fi

# Check Redis
echo ""
echo "🔍 Checking Redis..."
if command -v redis-cli >/dev/null 2>&1 && redis-cli -h localhost -p 6399 ping > /dev/null 2>&1; then
    echo "✅ Redis is responding on port 6399"
else
    echo "⚠️  Redis not responding - cache tests may be limited"
fi

# Check required tools
echo ""
echo "🔍 Checking tools..."

if ! command -v jq >/dev/null 2>&1; then
    echo "📦 Installing jq..."
    brew install jq
fi

if ! command -v wrk >/dev/null 2>&1; then
    echo "📦 Installing wrk..."
    brew install wrk
fi

if ! command -v bc >/dev/null 2>&1; then
    echo "📦 Installing bc..."
    brew install bc
fi

echo ""
echo "✅ Setup complete - proceeding with Task #29 tests..."
