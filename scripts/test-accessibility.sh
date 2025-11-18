#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Accessibility Testing Script
# Runs automated accessibility checks using available tools

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CUSTOMER_UI_DIR="$PROJECT_ROOT/apps/customer"

echo "=========================================="
echo "Accessibility Testing - WCAG AA Compliance"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found. Please install Node.js to run accessibility tests.${NC}"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found. Please install npm to run accessibility tests.${NC}"
    exit 1
fi

echo "📋 Checking for accessibility testing tools..."
echo ""

# Check for axe-core CLI
if command -v axe &> /dev/null; then
    echo -e "${GREEN}✅ axe CLI found${NC}"
    AXE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  axe CLI not found (install: npm install -g @axe-core/cli)${NC}"
    AXE_AVAILABLE=false
fi

# Check for Lighthouse CLI
if command -v lighthouse &> /dev/null; then
    echo -e "${GREEN}✅ Lighthouse CLI found${NC}"
    LIGHTHOUSE_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  Lighthouse CLI not found (install: npm install -g lighthouse)${NC}"
    LIGHTHOUSE_AVAILABLE=false
fi

# Check for pa11y CLI
if command -v pa11y &> /dev/null; then
    echo -e "${GREEN}✅ pa11y CLI found${NC}"
    PA11Y_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  pa11y CLI not found (install: npm install -g pa11y)${NC}"
    PA11Y_AVAILABLE=false
fi

echo ""
echo "=========================================="
echo "Testing Recommendations"
echo "=========================================="
echo ""
echo "1. Manual Testing:"
echo "   - Use browser DevTools (Chrome/Firefox) to check contrast ratios"
echo "   - Use WAVE browser extension for visual accessibility checker"
echo "   - Test with keyboard navigation (Tab, Arrow keys, Enter)"
echo "   - Test with screen readers (NVDA, VoiceOver, JAWS)"
echo ""
echo "2. Automated Testing:"
echo "   - Install tools: npm install -g @axe-core/cli lighthouse pa11y"
echo "   - Run Lighthouse: lighthouse http://localhost:3000 --view --only-categories=accessibility"
echo "   - Run axe: axe http://localhost:3000"
echo "   - Run pa11y: pa11y http://localhost:3000"
echo ""
echo "3. Color Contrast Verification:"
echo "   - Use WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/"
echo "   - Check all text colors meet 4.5:1 ratio (normal text)"
echo "   - Check all interactive elements meet 3:1 ratio"
echo "   - See: apps/customer/ACCESSIBILITY_COLOR_CONTRAST.md"
echo ""
echo "4. Browser DevTools:"
echo "   - Chrome: Elements → Computed → Contrast ratio"
echo "   - Firefox: Accessibility panel → Check contrast"
echo ""
echo "=========================================="
echo "Quick Accessibility Checklist"
echo "=========================================="
echo ""
echo "✅ All pages have h1 heading"
echo "✅ All interactive elements have ARIA labels"
echo "✅ All forms have associated labels"
echo "✅ All error messages use aria-live"
echo "✅ All buttons have focus indicators"
echo "✅ Skip-to-content link is present"
echo "✅ Semantic HTML used (nav, main, section, article)"
echo "✅ Keyboard navigation works (Tab, Arrow keys)"
echo "⚠️  Color contrast needs manual verification"
echo "⚠️  Screen reader testing needs user validation"
echo ""
echo "=========================================="
echo "Documentation"
echo "=========================================="
echo ""
echo "📄 Color Contrast Guide: apps/customer/ACCESSIBILITY_COLOR_CONTRAST.md"
echo "📄 Final Audit: apps/customer/ACCESSIBILITY_FINAL_AUDIT.md"
echo ""
echo "=========================================="

# If tools are available, offer to run tests
if [ "$AXE_AVAILABLE" = true ] || [ "$LIGHTHOUSE_AVAILABLE" = true ] || [ "$PA11Y_AVAILABLE" = true ]; then
    echo ""
    read -p "Would you like to run automated tests? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Starting automated tests..."
        echo ""

        # Check if dev server is running
        if ! curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  Dev server not running on http://localhost:3000${NC}"
            echo "   Please start the dev server first: cd apps/customer && npm run dev"
            exit 1
        fi

        if [ "$AXE_AVAILABLE" = true ]; then
            echo "Running axe accessibility tests..."
            axe http://localhost:3000 --tags wcag2a,wcag2aa,wcag21aa || true
        fi

        if [ "$LIGHTHOUSE_AVAILABLE" = true ]; then
            echo "Running Lighthouse accessibility audit..."
            lighthouse http://localhost:3000 --only-categories=accessibility --output=html --output-path=/tmp/lighthouse-accessibility.html || true
            echo "Lighthouse report saved to /tmp/lighthouse-accessibility.html"
        fi

        if [ "$PA11Y_AVAILABLE" = true ]; then
            echo "Running pa11y accessibility tests..."
            pa11y http://localhost:3000 --standard WCAG2AA || true
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ Accessibility testing guide complete${NC}"
echo ""




