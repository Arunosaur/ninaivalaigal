#!/usr/bin/env bash
# PRODUCTION FIX: Get stack working immediately by disabling problematic features
set -euo pipefail

echo "🚨 PRODUCTION FIX: Creating stable working version"
echo "=================================================="

# Step 1: Disable agentic API (already done)
echo "✅ Agentic API already disabled in main.py"

# Step 2: Disable performance API temporarily
echo "🔧 Temporarily disabling performance API..."
sed -i '' 's/from performance_api import router as performance_router/# from performance_api import router as performance_router/' server/main.py
sed -i '' 's/app.include_router(performance_router)/# app.include_router(performance_router)/' server/main.py

# Step 3: Build stable container
echo "🏗️ Building stable container..."
container build --no-cache -t nina-api:stable -f Dockerfile.api .

# Step 4: Tag as working version
echo "🏷️ Tagging as working version..."
container tag nina-api:stable nina-api:arm64

# Step 5: Restart API
echo "🔄 Restarting API with stable version..."
container stop nv-api && container rm nv-api || true

container run -d --name nv-api -p 13370:8000 \
  --workdir /app/server \
  -e NINAIVALAIGAL_DATABASE_URL="postgresql://nina:change_me_securely@192.168.65.173:6432/nina" \
  -e DATABASE_URL="postgresql://nina:change_me_securely@192.168.65.173:6432/nina" \
  -e REDIS_HOST="192.168.65.168" \
  -e REDIS_PORT="6379" \
  -e REDIS_PASSWORD="nina_redis_dev_password" \
  -e NINAIVALAIGAL_JWT_SECRET="test-jwt-secret-for-production-demo" \
  nina-api:arm64 \
  uvicorn main:app --host 0.0.0.0 --port 8000

# Step 6: Wait and test
echo "⏳ Waiting for API to start..."
sleep 10

if curl -f http://localhost:13370/health >/dev/null 2>&1; then
    echo "✅ SUCCESS: API is responding!"
    echo "🌐 API: http://localhost:13370/health"
    echo "🌐 UI:  http://localhost:8080"
    echo ""
    echo "🎯 PRODUCTION STACK STATUS:"
    make stack-status
else
    echo "❌ API still not responding - checking logs..."
    container logs nv-api
fi

echo ""
echo "🛡️ PERMANENT FIX NEEDED:"
echo "  1. Fix all relative imports in performance/ and agent/ modules"
echo "  2. Run ./scripts/production-stability-system.sh"
echo "  3. Create verified stable images with proper tagging"
