#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Restart API container with latest code
# Follows naming conventions and uses PgBouncer (no direct DB connection)

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Restarting API with Latest Code ===${NC}"

# 1. Get service IPs
echo "Getting service IPs..."
PGB_IP=$(container inspect ninaivalaigal-dev-pgbouncer | jq -r '.[0].networks[0].address' | cut -d'/' -f1)
REDIS_IP=$(container inspect ninaivalaigal-dev-redis | jq -r '.[0].networks[0].address' | cut -d'/' -f1)

echo "PgBouncer IP: $PGB_IP"
echo "Redis IP: $REDIS_IP"

# 2. Stop and remove old container
echo "Stopping old container..."
if container list | grep -q "ninaivalaigal-dev-api"; then
  container stop ninaivalaigal-dev-api
  container delete ninaivalaigal-dev-api
  echo -e "${GREEN}✅ Old container removed${NC}"
fi

# 3. Start new container (dev environment only - not production credentials)
echo "Starting API container..."
container run -d --name ninaivalaigal-dev-api \
  -p 13390:8000 \
  -e DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@${PGB_IP}:6432/nina" \
  -e REDIS_URL="redis://:nina_redis_dev_password@${REDIS_IP}:6379/0" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-ci" \
  -e ENVIRONMENT="dev" \
  -e LOG_LEVEL="debug" \
  -e PYTHONPATH="/app:/app/server" \
  nina-api:arm64

# 4. Wait for startup
echo "Waiting for API to start..."
sleep 10

# 5. Verify
echo "Testing API health..."
if curl -f http://localhost:13390/health > /dev/null 2>&1; then
  echo -e "${GREEN}✅ API is healthy${NC}"
  echo ""
  echo "API URL: http://localhost:13390"
  echo "API Docs: http://localhost:13390/docs"
  echo ""

  # Test token endpoints
  echo "Checking token endpoints..."
  curl -s http://localhost:13390/openapi.json | python3 -c "import json,sys; d=json.load(sys.stdin); paths=[p for p in d.get('paths',{}).keys() if 'token' in p.lower()]; print('\n'.join(paths))" || echo "Could not check endpoints"
else
  echo -e "${RED}❌ API health check failed${NC}"
  echo "Logs:"
  container logs ninaivalaigal-dev-api | tail -20
  exit 1
fi
