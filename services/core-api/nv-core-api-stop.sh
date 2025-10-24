#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Stop Core API service

set -e

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-core-api"

echo "🛑 Stopping Core API Service"
echo "============================="
echo ""

if container stop "$CONTAINER_NAME" 2>/dev/null; then
    echo "✅ Container stopped: $CONTAINER_NAME"

    if container rm "$CONTAINER_NAME" 2>/dev/null; then
        echo "✅ Container removed: $CONTAINER_NAME"
    fi
else
    echo "⚠️  Container not running: $CONTAINER_NAME"
fi

echo ""
echo "✅ Core API service stopped"
