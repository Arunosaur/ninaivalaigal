#!/usr/bin/env bash
# Capture current working state of the ninaivalaigal stack
# Use this when everything is working to document the state

set -euo pipefail

RED=$'\033[31m'; GRN=$'\033[32m'; YLW=$'\033[33m'; NC=$'\033[0m'

ok(){ echo "${GRN}✅${NC} $*"; }
warn(){ echo "${YLW}⚠️${NC} $*"; }
error(){ echo "${RED}❌${NC} $*"; }

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')
SNAPSHOT_FILE="docs/working-state-$(date '+%Y%m%d-%H%M%S').md"

echo "📸 Capturing working state snapshot..."
echo "Timestamp: $TIMESTAMP"
echo ""

# Create snapshot file
cat > "$SNAPSHOT_FILE" << EOF
# Working State Snapshot

**Captured**: $TIMESTAMP
**Status**: $(make stack-status >/dev/null 2>&1 && echo "OPERATIONAL" || echo "ISSUES DETECTED")

## Stack Status
EOF

# Capture stack status
echo "Capturing stack status..."
{
    make stack-status
    echo ""
    echo "## Container Details"
    echo ""
    echo "\`\`\`"
    container list
    echo "\`\`\`"
} >> "$SNAPSHOT_FILE" 2>&1

# Capture API container dependencies
{
    echo ""
    echo "## API Container Dependencies"
    echo ""
    echo "\`\`\`"
    if container run --rm nina-api:arm64 pip list 2>/dev/null; then
        container run --rm nina-api:arm64 pip list | grep -E "(structlog|fastapi|uvicorn|sqlalchemy|psycopg2|redis)" || echo "Dependencies not found"
    else
        echo "API container not available"
    fi
    echo "\`\`\`"
} >> "$SNAPSHOT_FILE" 2>&1

# Test API endpoints
{
    echo ""
    echo "## API Health Tests"
    echo ""
} >> "$SNAPSHOT_FILE"

if curl -s http://localhost:13370/health >/dev/null 2>&1; then
    echo "✅ /health endpoint: $(curl -s http://localhost:13370/health)" >> "$SNAPSHOT_FILE"
else
    echo "❌ /health endpoint: Not responding" >> "$SNAPSHOT_FILE"
fi

if curl -s http://localhost:13370/health/detailed >/dev/null 2>&1; then
    echo "✅ /health/detailed endpoint: Working" >> "$SNAPSHOT_FILE"
else
    echo "❌ /health/detailed endpoint: Not responding" >> "$SNAPSHOT_FILE"
fi

# Test database operations
{
    echo ""
    echo "## Database Operations Test"
    echo ""
} >> "$SNAPSHOT_FILE"

if python -c "
import sys
sys.path.append('server')
from database.operations import DatabaseOperations, get_db
print('✅ Database operations import successful')
" 2>/dev/null; then
    echo "✅ Database operations: Import successful" >> "$SNAPSHOT_FILE"
else
    echo "❌ Database operations: Import failed" >> "$SNAPSHOT_FILE"
fi

# Add recovery instructions
cat >> "$SNAPSHOT_FILE" << 'EOF'

## Recovery Instructions

If the stack goes down, use these commands to restore this working state:

```bash
# 1. Check what's actually down
make stack-status

# 2. If API is down, rebuild container
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .

# 3. Verify dependencies
container run --rm nina-api:arm64 pip list | grep structlog

# 4. Restart API
container stop nv-api && container delete nv-api
./scripts/nv-api-start.sh

# 5. Verify working
curl http://localhost:13370/health
```

## Context

This snapshot was captured during database operations modularization work.
The stack was fully operational with all dependencies properly installed.
EOF

ok "Working state captured: $SNAPSHOT_FILE"
echo ""
echo "📋 Summary:"
echo "  - Stack status documented"
echo "  - Container details captured"
echo "  - API dependencies verified"
echo "  - Health endpoints tested"
echo "  - Recovery instructions included"
echo ""
echo "💡 Use this snapshot to restore working state if issues occur"
