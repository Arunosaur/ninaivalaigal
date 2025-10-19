#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Developer A - Simple service check and basic benchmark run

echo "👋 Developer A - Task #29 Basic Validation"
echo "==========================================="

# Check if memory service is running
echo "1. Testing memory service connection..."
if curl -sf http://localhost:13393/health >/dev/null 2>&1; then
    echo "✅ Memory service is running"
    echo "📊 Health status:"
    curl -s http://localhost:13393/health 2>/dev/null || echo "Could not get detailed health info"
else
    echo "❌ Memory service not running on port 13393"
    echo "   Checking alternative ports..."

    # Check if service might be on different port
    for port in 8080 3000 13393 50051; do
        if curl -sf http://localhost:$port/health >/dev/null 2>&1; then
            echo "✅ Found service on port $port"
            export MEMORY_SERVICE_URL="http://localhost:$port"
            break
        fi
    done
fi

echo ""
echo "2. Checking wrk availability..."
if command -v wrk >/dev/null 2>&1; then
    echo "✅ wrk is installed"

    # Run a quick 5-second test if service is available
    if curl -sf http://localhost:13393/health >/dev/null 2>&1; then
        echo ""
        echo "3. Running quick 5-second performance test..."
        echo "------------------------------------------------"
        wrk -t2 -c10 -d5s http://localhost:13393/health
        echo "------------------------------------------------"
        echo "✅ Quick test completed successfully!"
    else
        echo "⚠️  Cannot run performance test - service not available"
    fi
else
    echo "❌ wrk not installed"
    echo "   Run: brew install wrk"
fi

echo ""
echo "4. Checking existing benchmark results..."
if [ -d "/Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/benchmark-results" ]; then
    echo "📂 Found existing benchmark results:"
    ls -la /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/benchmark-results/ | head -5
else
    echo "📂 No existing benchmark results directory"
fi

echo ""
echo "5. Checking benchmark documentation..."
if [ -f "/Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/README.md" ]; then
    echo "📋 Benchmark README found - checking status..."
    grep -A5 -B5 "31,315" /Users/swami/WorkSpace/ninaivalaigal/rust-services/memory-service/benchmarks/README.md || echo "Previous results documented"
else
    echo "📋 No benchmark README found"
fi

echo ""
echo "📝 Summary:"
echo "- Basic service check: $(curl -sf http://localhost:13393/health >/dev/null 2>&1 && echo 'PASS' || echo 'NEEDS SETUP')"
echo "- wrk tool: $(command -v wrk >/dev/null 2>&1 && echo 'AVAILABLE' || echo 'NEEDS INSTALL')"
echo "- Ready for full Task #29: $(curl -sf http://localhost:13393/health >/dev/null 2>&1 && command -v wrk >/dev/null 2>&1 && echo 'YES' || echo 'NEEDS SETUP')"
