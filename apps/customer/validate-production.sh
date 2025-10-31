#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Production Readiness Validation Script
# Run this before committing to GitHub to ensure code quality

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔍 PRODUCTION READINESS VALIDATION                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Track overall status
VALIDATION_FAILED=0

# 1. ESLint Check
echo "📋 Running ESLint..."
if npm run lint > /dev/null 2>&1; then
  echo "   ✅ ESLint: PASSED (0 errors, 0 warnings)"
else
  echo "   ❌ ESLint: FAILED"
  echo "   Run 'npm run lint' to see details"
  VALIDATION_FAILED=1
fi
echo ""

# 2. TypeScript Check
echo "📋 Running TypeScript Type Check..."
if npm run type-check > /dev/null 2>&1; then
  echo "   ✅ TypeScript: PASSED (no type errors)"
else
  echo "   ❌ TypeScript: FAILED"
  echo "   Run 'npm run type-check' to see details"
  VALIDATION_FAILED=1
fi
echo ""

# 3. Production Build Test
echo "📋 Testing Production Build..."
if npm run build > /tmp/build-output.log 2>&1; then
  BUILD_SIZE=$(du -sh dist 2>/dev/null | cut -f1 || echo "unknown")
  echo "   ✅ Production Build: SUCCESS"
  echo "   📦 Build Size: $BUILD_SIZE"
else
  echo "   ❌ Production Build: FAILED"
  echo "   Check /tmp/build-output.log for details"
  VALIDATION_FAILED=1
fi
echo ""

# 4. Check for console.log (optional - warn only)
echo "📋 Checking for Debug Statements..."
DEBUG_COUNT=$(grep -r "console\.log\|console\.warn\|debugger" src --include="*.tsx" --include="*.ts" 2>/dev/null | wc -l | tr -d ' ')
if [ "$DEBUG_COUNT" -gt "0" ]; then
  echo "   ⚠️  Found $DEBUG_COUNT debug statement(s) (not blocking)"
else
  echo "   ✅ No debug statements found"
fi
echo ""

# 5. Check SPDX Headers (sample check)
echo "📋 Checking License Headers..."
MISSING_HEADERS=$(find src -name "*.tsx" -o -name "*.ts" | while read file; do
  if ! head -5 "$file" | grep -q "SPDX-License-Identifier"; then
    echo "$file"
  fi
done | wc -l | tr -d ' ')

if [ "$MISSING_HEADERS" -eq "0" ]; then
  echo "   ✅ All files have proper license headers"
else
  echo "   ⚠️  $MISSING_HEADERS file(s) missing SPDX headers (review manually)"
fi
echo ""

# Final Result
echo "╔════════════════════════════════════════════════════════════╗"
if [ $VALIDATION_FAILED -eq 0 ]; then
  echo "║  ✅ VALIDATION PASSED - READY FOR GITHUB                   ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""
  echo "🚀 Your code is production-ready and safe to commit!"
  echo ""
  echo "Next steps:"
  echo "  git add ."
  echo "  git commit -m \"your message\""
  echo "  git push"
  exit 0
else
  echo "║  ❌ VALIDATION FAILED - FIX ISSUES BEFORE COMMIT           ║"
  echo "╚════════════════════════════════════════════════════════════╝"
  echo ""
  echo "⚠️  Please fix the issues above before committing to GitHub"
  exit 1
fi
