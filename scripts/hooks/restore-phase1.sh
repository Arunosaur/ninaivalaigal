#!/usr/bin/env bash
# Pre-Commit Hook Restoration - Phase 1 Automation
# Restores enforcement for server/ directory

set -euo pipefail

log() { echo "✓ $*"; }
warn() { echo "⚠️  $*"; }

echo "🚀 Pre-Commit Hook Restoration - Phase 1"
echo "=========================================="
echo ""

# Step 1: Baseline
log "Step 1: Baseline assessment..."
mkdir -p docs/hooks
./scripts/lint/verify-hooks.sh | tee docs/hooks/phase1-baseline.txt

# Step 2: Auto-fix
echo ""
log "Step 2: Auto-fixing imports and formatting..."
./scripts/lint/fix-imports.sh

# Step 3: Format
echo ""
log "Step 3: Running black and isort..."
black server/
isort server/

# Step 4: Check remaining issues
echo ""
log "Step 4: Checking for remaining issues..."
echo ""
echo "CRITICAL ERRORS (must fix manually):"
flake8 server/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
    warn "Found critical errors that need manual fixing"
    echo ""
    echo "Next steps:"
    echo "  1. Review errors above"
    echo "  2. Fix undefined names (F821)"
    echo "  3. Fix syntax errors (E9, F7)"
    echo "  4. Re-run this script"
    exit 1
}

echo ""
echo "🎉 Phase 1 automation complete!"
echo ""
echo "Final steps:"
echo "  1. Update .pre-commit-config.yaml (remove server/ from exclusions)"
echo "  2. Run: pre-commit run --files server/**/*.py"
echo "  3. git add server/ .pre-commit-config.yaml scripts/ docs/"
echo "  4. git commit -m 'fix(hooks): restore pre-commit enforcement for server/'"
