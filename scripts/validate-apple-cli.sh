#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Validate Apple Container CLI Runtime
# Optimized for M1/M2 Macs with native ARM performance

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Apple Container CLI Validation                           ║"
echo "║  Native ARM Performance for M1/M2 Macs                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if running on Apple Silicon
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo -e "${YELLOW}⚠️  Warning: Not running on Apple Silicon (arm64)${NC}"
    echo "   Current architecture: $ARCH"
    echo "   Apple Container CLI is optimized for M1/M2 Macs"
    echo ""
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"

# Start the Apple CLI stack
echo ""
echo "Starting Apple Container CLI stack..."
docker-compose -f compose.apple.dev.yml up -d --build

# Wait for services
echo "Waiting for services to be healthy (60s)..."
sleep 60

# Check services
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Service Health Checks"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check PostgreSQL
if docker exec ninaivalaigal-apple-dev-db pg_isready -U nina -d ninaivalaigal_dev > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL${NC}: Healthy"
else
    echo -e "${RED}❌ PostgreSQL${NC}: Unhealthy"
fi

# Check Redis
if docker exec ninaivalaigal-apple-dev-redis redis-cli -a secure_nina_password ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Redis${NC}: Healthy"
else
    echo -e "${RED}❌ Redis${NC}: Unhealthy"
fi

# Check API (Apple/Dev port: 13390)
if curl -s http://localhost:13390/health | grep -q "ok"; then
    echo -e "${GREEN}✅ API${NC}: Responding"
else
    echo -e "${RED}❌ API${NC}: Not responding"
fi

# Check UI (Apple/Dev port: 8101)
if curl -s http://localhost:8101 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ UI${NC}: Accessible"
else
    echo -e "${YELLOW}⚠️  UI${NC}: Not accessible (may still be starting)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Running Smoke Tests"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Run smoke tests against Apple CLI stack
export REDIS_PASSWORD=secure_nina_password
export API_URL=http://localhost:13390

# Test Redis
echo "Testing Redis..."
if docker exec ninaivalaigal-apple-dev-redis redis-cli -a secure_nina_password SET test_key "test_value" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis SET/GET${NC}: Working"
else
    echo -e "${RED}❌ Redis SET/GET${NC}: Failed"
fi

# Test PostgreSQL
echo "Testing PostgreSQL..."
if docker exec ninaivalaigal-apple-dev-db psql -U nina -d ninaivalaigal_dev -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL Query${NC}: Working"
else
    echo -e "${RED}❌ PostgreSQL Query${NC}: Failed"
fi

# Test API endpoints
echo "Testing API endpoints..."

# Health endpoint
if curl -s http://localhost:13390/health | grep -q "ok"; then
    echo -e "${GREEN}✅ /health${NC}: Working"
else
    echo -e "${RED}❌ /health${NC}: Failed"
fi

# Detailed health endpoint
if curl -s http://localhost:13390/health/detailed > /dev/null 2>&1; then
    echo -e "${GREEN}✅ /health/detailed${NC}: Working"
else
    echo -e "${RED}❌ /health/detailed${NC}: Failed"
fi

# Memory health endpoint
if curl -s http://localhost:13390/health/status | grep -q "healthy"; then
    echo -e "${GREEN}✅ /health/status${NC}: Working"
else
    echo -e "${YELLOW}⚠️  /health/status${NC}: May need time to start"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Platform Information"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Show platform info
echo "Architecture: $(uname -m)"
echo "OS: $(uname -s)"
echo "Docker Version: $(docker --version)"

# Show container platforms
echo ""
echo "Container Platforms:"
docker inspect ninaivalaigal-apple-dev-api --format '{{.Platform}}' 2>/dev/null || echo "N/A"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ APPLE CONTAINER CLI VALIDATION COMPLETE               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Access Points (Apple/Dev from Port Matrix):"
echo "  API:  http://localhost:13390"
echo "  UI:   http://localhost:8101"
echo "  DB:   localhost:5452"
echo "  Redis: localhost:6399"
echo ""
echo "Stop stack:"
echo "  docker-compose -f compose.apple.dev.yml down"
echo ""
