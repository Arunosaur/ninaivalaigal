#!/usr/bin/env bash
# Quick Fix for API Container - Immediate Solution
set -euo pipefail

echo "🔧 Quick Fix: Rebuilding API with validated dependencies"
echo "======================================================"

# Use our validated build script
./scripts/build-and-validate-api.sh

# Restart the stack
echo ""
echo "🔄 Restarting stack with fixed container..."
make stack-down || true
make stack-up

echo ""
echo "✅ Quick fix complete!"
echo ""
echo "🧪 Testing endpoints..."
sleep 5

if curl -f http://localhost:13370/health >/dev/null 2>&1; then
    echo "✅ API health check passed"
else
    echo "❌ API health check failed - check logs: container logs nv-api"
fi

if curl -f http://localhost:8080 >/dev/null 2>&1; then
    echo "✅ UI health check passed"
else
    echo "❌ UI health check failed"
fi

echo ""
echo "🎯 Next: Run './scripts/production-stability-system.sh' to prevent future issues"
