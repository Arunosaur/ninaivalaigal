#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Quick Test Script for Task #29 Validation
# This runs the essential tests quickly to validate the setup

set -euo pipefail

echo "🚀 Quick Task #29 Validation Test"
echo "================================="

# Check services
echo "1. Checking services..."
if curl -sf http://localhost:13393/health > /dev/null; then
    echo "   ✅ Memory service running (port 13393)"
else
    echo "   ❌ Memory service not running"
fi

if curl -sf http://localhost:13390/health > /dev/null 2>&1; then
    echo "   ✅ API service running (port 13390)"
else
    echo "   ⚠️  API service not running (will use mock token)"
fi

# Check Redis
echo "2. Checking Redis..."
if command -v redis-cli >/dev/null && redis-cli -h localhost -p 6399 ping > /dev/null 2>&1; then
    echo "   ✅ Redis responding (port 6399)"
else
    echo "   ⚠️  Redis not responding"
fi

# Check tools
echo "3. Checking tools..."
if command -v wrk >/dev/null 2>&1; then
    echo "   ✅ wrk installed"
else
    echo "   ⚠️  wrk not installed (will install automatically)"
fi

if command -v jq >/dev/null 2>&1; then
    echo "   ✅ jq installed"
else
    echo "   ❌ jq not installed - please run: brew install jq"
fi

echo ""
echo "🎯 Ready to run Task #29 completion!"
echo "Run: ./developer_a_task29_completion.sh"
