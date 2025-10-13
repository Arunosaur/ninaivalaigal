#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Setup Tailscale Funnel for Ninaivalaigal MCP Server
# Exposes MCP server to colleagues via public URL

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Tailscale Funnel Setup for Ninaivalaigal MCP Server     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if Tailscale is installed
if ! command -v tailscale &> /dev/null; then
    echo -e "${RED}❌ Tailscale is not installed${NC}"
    echo ""
    echo "Install Tailscale:"
    echo "  brew install tailscale"
    echo "  or download from: https://tailscale.com/download"
    exit 1
fi

echo -e "${GREEN}✅ Tailscale is installed${NC}"

# Check if Tailscale is running
if ! tailscale status &> /dev/null; then
    echo -e "${RED}❌ Tailscale is not running${NC}"
    echo ""
    echo "Start Tailscale:"
    echo "  sudo tailscaled"
    echo "  tailscale up"
    exit 1
fi

echo -e "${GREEN}✅ Tailscale is running${NC}"

# Get Tailscale hostname
TAILSCALE_HOSTNAME=$(tailscale status --json | grep -o '"HostName":"[^"]*"' | cut -d'"' -f4)
echo -e "${GREEN}✅ Tailscale hostname: ${TAILSCALE_HOSTNAME}${NC}"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Setting up Funnel for MCP Server"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Enable Funnel for MCP server (port 3000)
echo "Enabling Funnel for MCP server on port 3000..."
tailscale funnel 3000 &

# Wait for Funnel to start
sleep 3

# Get Funnel URL
FUNNEL_URL="https://${TAILSCALE_HOSTNAME}.ts.net:3000"

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  ✅ TAILSCALE FUNNEL SETUP COMPLETE                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}MCP Server URL (for colleagues):${NC}"
echo -e "${YELLOW}${FUNNEL_URL}${NC}"
echo ""
echo "Share this URL with your colleagues for MCP access."
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Testing Funnel Access"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test the Funnel URL
echo "Testing MCP server health..."
if curl -s "${FUNNEL_URL}/health" | grep -q "healthy"; then
    echo -e "${GREEN}✅ MCP server is accessible via Funnel!${NC}"
else
    echo -e "${YELLOW}⚠️  MCP server may not be ready yet. Wait a moment and try:${NC}"
    echo "  curl ${FUNNEL_URL}/health"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Share the MCP URL with colleagues:"
echo -e "   ${YELLOW}${FUNNEL_URL}${NC}"
echo ""
echo "2. Colleagues can configure their Copilot with:"
echo "   - MCP Server URL: ${FUNNEL_URL}"
echo "   - Health Check: ${FUNNEL_URL}/health"
echo ""
echo "3. Monitor Funnel traffic:"
echo "   tailscale funnel status"
echo ""
echo "4. Stop Funnel when done:"
echo "   tailscale funnel off"
echo ""

# Save URL to file for easy reference
echo "${FUNNEL_URL}" > .tailscale-funnel-url
echo -e "${GREEN}✅ Funnel URL saved to .tailscale-funnel-url${NC}"
echo ""
