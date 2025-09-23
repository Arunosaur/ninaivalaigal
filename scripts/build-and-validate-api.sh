#!/usr/bin/env bash
# Build and Validate API Container with Dependency Verification
# CRITICAL: This script prevents the recurring issue of missing dependencies in containers

set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; NC=$'\033[0m'

ok(){ echo "${GRN}✅${NC} $*"; }
warn(){ echo "${YLW}⚠️${NC} $*"; }
error(){ echo "${RED}❌${NC} $*"; exit 1; }

IMAGE_NAME="${IMAGE_NAME:-nina-api:arm64}"
DOCKERFILE="${DOCKERFILE:-Dockerfile.api}"

echo "🔨 Building API Container with Dependency Validation"
echo "Image: $IMAGE_NAME"
echo "Dockerfile: $DOCKERFILE"
echo ""

# Step 1: Build with --no-cache (MANDATORY for dependency changes)
echo "Step 1: Building container with --no-cache..."
if ! container build --no-cache -t "$IMAGE_NAME" -f "$DOCKERFILE" .; then
    error "Container build failed"
fi
ok "Container built successfully"

# Step 2: Verify critical dependencies are installed
echo ""
echo "Step 2: Verifying critical dependencies..."

CRITICAL_DEPS=(
    "structlog"
    "fastapi"
    "uvicorn"
    "sqlalchemy"
    "psycopg2-binary"
    "redis"
    "prometheus_client"
)

for dep in "${CRITICAL_DEPS[@]}"; do
    if container run --rm "$IMAGE_NAME" pip list 2>/dev/null | grep -i "^$dep " >/dev/null; then
        ok "$dep is installed"
    else
        error "$dep is MISSING from container!"
    fi
done

# Step 3: Test critical imports
echo ""
echo "Step 3: Testing critical imports..."

IMPORT_TESTS=(
    "import structlog; print('structlog OK')"
    "import fastapi; print('fastapi OK')"
    "import uvicorn; print('uvicorn OK')"
    "import sqlalchemy; print('sqlalchemy OK')"
    "import psycopg2; print('psycopg2 OK')"
    "import redis; print('redis OK')"
    "import prometheus_client; print('prometheus_client OK')"
)

for test in "${IMPORT_TESTS[@]}"; do
    if container run --rm "$IMAGE_NAME" python -c "$test" >/dev/null 2>&1; then
        ok "Import test passed: ${test%%;*}"
    else
        error "Import test FAILED: ${test%%;*}"
    fi
done

# Step 4: Test main application import
echo ""
echo "Step 4: Testing main application import..."
if container run --rm "$IMAGE_NAME" python -c "
import sys
sys.path.append('/app/server')
try:
    import main
    print('✅ Main application imports successfully')
except Exception as e:
    print(f'❌ Main application import failed: {e}')
    exit(1)
" >/dev/null 2>&1; then
    ok "Main application imports successfully"
else
    error "Main application import FAILED - check logs above"
fi

# Step 5: Validate requirements.txt matches installed packages
echo ""
echo "Step 5: Validating requirements.txt consistency..."
if [ -f "requirements.txt" ]; then
    while IFS= read -r line; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

        # Extract package name (before any version specifiers)
        pkg_name=$(echo "$line" | sed 's/[<>=!].*//' | tr -d '[:space:]')

        if container run --rm "$IMAGE_NAME" pip list | grep -q "^$pkg_name "; then
            ok "$pkg_name (from requirements.txt) is installed"
        else
            warn "$pkg_name (from requirements.txt) might be missing or named differently"
        fi
    done < requirements.txt
else
    warn "requirements.txt not found - skipping consistency check"
fi

echo ""
ok "🎉 Container build and validation completed successfully!"
echo ""
echo "Container is ready to use: $IMAGE_NAME"
echo ""
echo "Next steps:"
echo "  1. Start the stack: make stack-up"
echo "  2. Check health: make stack-status"
echo "  3. Test API: curl http://localhost:13370/health"
echo ""
echo "🔒 This validation prevents the recurring dependency issues!"
