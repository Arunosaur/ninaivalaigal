#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# docker-daemon-check.sh - Verify Docker daemon is healthy

echo "🔍 Docker Daemon Health Check"
echo ""

# Step 1: Check socket
echo "1️⃣  Checking socket..."
if ls -l /var/run/docker.sock 2>/dev/null; then
  echo "✅ Socket exists"
else
  echo "❌ Socket missing - daemon not running"
  echo ""
  echo "Recovery:"
  echo "  sudo pkill -9 -f docker"
  echo "  sudo rm -f /var/run/docker.sock"
  echo "  open /Applications/Docker.app"
  exit 1
fi

# Step 2: Check process
echo ""
echo "2️⃣  Checking process..."
if sudo lsof -i -P | grep docker | grep LISTEN; then
  echo "✅ Backend listening"
else
  echo "❌ Backend not listening"
  exit 1
fi

# Step 3: Check version responds
echo ""
echo "3️⃣  Checking daemon response..."
if timeout 5 docker version >/dev/null 2>&1; then
  echo "✅ Daemon responsive"
  docker version | grep -E "Version:|API version:"
else
  echo "❌ Daemon timeout"
  exit 1
fi

echo ""
echo "🎉 Docker daemon is healthy!"
echo "   Ready to run: ./scripts/nv-api-diagnose-repair-v3.1.sh"
