#!/usr/bin/env bash
# Production Stability System - Prevents Demo-Breaking Container Issues
# This script creates a bulletproof container management system

set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; BLU=$'\033[34m'; NC=$'\033[0m'

ok(){ echo "${GRN}✅${NC} $*"; }
warn(){ echo "${YLW}⚠️${NC} $*"; }
error(){ echo "${RED}❌${NC} $*"; exit 1; }
info(){ echo "${BLU}ℹ️${NC} $*"; }

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VERIFIED_TAG="nina-api:verified-${TIMESTAMP}"
STABLE_TAG="nina-api:stable"
ROLLBACK_TAG="nina-api:rollback"

echo "🛡️ Production Stability System"
echo "=============================="
echo "Creating bulletproof container management for demos and production"
echo ""

# Step 1: Build and Validate New Container
echo "Step 1: Building and validating new container..."
if ! ./scripts/build-and-validate-api.sh; then
    error "Container build/validation failed - aborting"
fi
ok "New container built and validated"

# Step 2: Tag Current Stable as Rollback
echo ""
echo "Step 2: Creating rollback point..."
if container image exists nina-api:stable 2>/dev/null; then
    container tag nina-api:stable "$ROLLBACK_TAG"
    ok "Current stable tagged as rollback: $ROLLBACK_TAG"
else
    warn "No existing stable image found - first deployment"
fi

# Step 3: Tag New Build as Verified
echo ""
echo "Step 3: Tagging new build as verified..."
container tag nina-api:arm64 "$VERIFIED_TAG"
ok "New build tagged as verified: $VERIFIED_TAG"

# Step 4: Production Health Test
echo ""
echo "Step 4: Running production health test..."

# Start test container
TEST_CONTAINER="nina-api-health-test"
container run -d --name "$TEST_CONTAINER" \
    -p 13371:8000 \
    -e NINAIVALAIGAL_DATABASE_URL="sqlite:///test.db" \
    -e REDIS_HOST="localhost" \
    -e REDIS_PORT="6379" \
    -e NINAIVALAIGAL_JWT_SECRET="test-secret" \
    "$VERIFIED_TAG" || error "Failed to start test container"

# Wait for startup
sleep 10

# Test health endpoint
if curl -f http://localhost:13371/health >/dev/null 2>&1; then
    ok "Health endpoint responding"
else
    container stop "$TEST_CONTAINER" && container rm "$TEST_CONTAINER"
    error "Health endpoint failed - container not production ready"
fi

# Test import functionality
if container exec "$TEST_CONTAINER" python -c "
import sys
sys.path.append('/app/server')
import main
import structlog
print('All critical imports working')
" >/dev/null 2>&1; then
    ok "All critical imports working in running container"
else
    container stop "$TEST_CONTAINER" && container rm "$TEST_CONTAINER"
    error "Critical imports failed in running container"
fi

# Cleanup test container
container stop "$TEST_CONTAINER" && container rm "$TEST_CONTAINER"
ok "Production health test passed"

# Step 5: Promote to Stable
echo ""
echo "Step 5: Promoting to stable..."
container tag "$VERIFIED_TAG" "$STABLE_TAG"
ok "New build promoted to stable: $STABLE_TAG"

# Step 6: Update Stack to Use Stable
echo ""
echo "Step 6: Updating stack configuration..."

# Create production-ready Makefile target
cat >> Makefile.production << 'EOF'

# Production Stability Targets
.PHONY: production-build production-deploy production-rollback production-status

production-build:
	@echo "🏗️ Building production-ready API container..."
	@./scripts/production-stability-system.sh

production-deploy:
	@echo "🚀 Deploying stable container..."
	@make stack-down || true
	@container tag nina-api:stable nina-api:arm64
	@make stack-up
	@make stack-status

production-rollback:
	@echo "🔄 Rolling back to previous stable version..."
	@make stack-down || true
	@container tag nina-api:rollback nina-api:arm64
	@make stack-up
	@make stack-status
	@echo "⚠️ Rollback complete - investigate issues with latest build"

production-status:
	@echo "📊 Production Container Status"
	@echo "=============================="
	@echo "Available Images:"
	@container image list | grep nina-api || echo "No nina-api images found"
	@echo ""
	@echo "Stack Status:"
	@make stack-status

EOF

ok "Production Makefile targets created"

# Step 7: Create Demo-Safe Startup Script
echo ""
echo "Step 7: Creating demo-safe startup script..."

cat > scripts/demo-safe-startup.sh << 'EOF'
#!/usr/bin/env bash
# Demo-Safe Startup - Guarantees working stack for demos
set -euo pipefail

echo "🎭 Demo-Safe Startup"
echo "==================="
echo "Ensuring bulletproof stack for demonstrations"

# Use stable tagged image
if ! container image exists nina-api:stable; then
    echo "❌ No stable image found - run 'make production-build' first"
    exit 1
fi

# Ensure we're using stable image
container tag nina-api:stable nina-api:arm64

# Start stack
make stack-up

# Validate all endpoints
echo "🧪 Validating all critical endpoints..."

ENDPOINTS=(
    "http://localhost:13370/health"
    "http://localhost:13370/health/detailed"
    "http://localhost:8080"
)

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f "$endpoint" >/dev/null 2>&1; then
        echo "✅ $endpoint - OK"
    else
        echo "❌ $endpoint - FAILED"
        echo "🔄 Attempting rollback..."
        make production-rollback
        exit 1
    fi
done

echo ""
echo "🎉 Demo-safe stack is ready!"
echo ""
echo "🌐 Access Points:"
echo "  API: http://localhost:13370"
echo "  UI:  http://localhost:8080"
echo ""
echo "🛡️ This stack is guaranteed to work for demos"
EOF

chmod +x scripts/demo-safe-startup.sh
ok "Demo-safe startup script created"

# Step 8: Create Monitoring Script
echo ""
echo "Step 8: Creating continuous monitoring..."

cat > scripts/production-monitor.sh << 'EOF'
#!/usr/bin/env bash
# Production Monitor - Detects and auto-fixes container degradation
set -euo pipefail

while true; do
    # Check if API is responding
    if ! curl -f http://localhost:13370/health >/dev/null 2>&1; then
        echo "🚨 API health check failed - attempting auto-recovery"

        # Try restarting API container
        container restart nv-api || {
            echo "🔄 Container restart failed - rolling back to stable"
            make production-rollback
        }

        # Wait and recheck
        sleep 30
        if curl -f http://localhost:13370/health >/dev/null 2>&1; then
            echo "✅ Auto-recovery successful"
        else
            echo "❌ Auto-recovery failed - manual intervention required"
        fi
    fi

    sleep 60  # Check every minute
done
EOF

chmod +x scripts/production-monitor.sh
ok "Production monitor created"

echo ""
echo "🎉 Production Stability System Complete!"
echo "========================================"
echo ""
echo "📋 New Commands Available:"
echo "  make production-build    - Build and validate new container"
echo "  make production-deploy   - Deploy stable container"
echo "  make production-rollback - Rollback to previous version"
echo "  ./scripts/demo-safe-startup.sh - Guaranteed working demo stack"
echo "  ./scripts/production-monitor.sh - Continuous health monitoring"
echo ""
echo "🛡️ This system prevents:"
echo "  ✅ Missing dependencies in containers"
echo "  ✅ Demo failures due to container issues"
echo "  ✅ Production outages from bad deployments"
echo "  ✅ Loss of working states"
echo ""
echo "🚀 For your next demo, just run: ./scripts/demo-safe-startup.sh"
