#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Monthly SPEC Audit Script
# Runs automated SPEC index audit and generates monthly report
#
# Usage:
#   ./scripts/monthly_spec_audit.sh
#
# Schedule: Run on 1st of each month
# Cron: 0 9 1 * * /path/to/scripts/monthly_spec_audit.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "Monthly SPEC Audit - $(date +%Y-%m-%d)"
echo "=========================================="
echo ""

# Activate conda environment if available
if command -v conda &> /dev/null; then
    echo "📦 Activating conda environment..."
    source "$(conda info --base)/etc/profile.d/conda.sh" 2>/dev/null || true
    if conda env list | grep -q "nina"; then
        conda activate nina || true
        echo "✅ Conda environment activated"
    else
        echo "⚠️  Conda environment 'nina' not found, using system Python"
    fi
else
    echo "⚠️  Conda not found, using system Python"
fi

echo ""
echo "🔍 Running SPEC index audit..."
if python3 "$SCRIPT_DIR/audit_spec_index.py"; then
    echo -e "${GREEN}✅ Audit completed successfully${NC}"
else
    echo -e "${RED}❌ Audit failed${NC}"
    exit 1
fi

echo ""
echo "📊 Generating monthly report..."
if [ -f "$SCRIPT_DIR/generate_monthly_spec_report.py" ]; then
    if python3 "$SCRIPT_DIR/generate_monthly_spec_report.py"; then
        echo -e "${GREEN}✅ Monthly report generated${NC}"
    else
        echo -e "${YELLOW}⚠️  Monthly report generation failed (non-critical)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Monthly report generator not found, skipping${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Monthly SPEC audit complete${NC}"
echo "=========================================="
echo ""
echo "Reports generated:"
echo "  - governance/reports/SPEC_INDEX_AUDIT_$(date +%Y-%m-%d).md"
if [ -f "$SCRIPT_DIR/generate_monthly_spec_report.py" ]; then
    echo "  - governance/reports/SPEC_STATUS_MONTHLY_$(date +%Y-%m).md"
fi
echo ""
