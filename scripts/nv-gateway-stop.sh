#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Stop Traefik API Gateway

set -euo pipefail

NINA_ENV=${NINA_ENV:-dev}
CONTAINER_NAME="ninaivalaigal-${NINA_ENV}-gateway"

echo "🛑 Stopping $CONTAINER_NAME..."
container stop "$CONTAINER_NAME" || true
container rm "$CONTAINER_NAME" || true
echo "✅ Gateway stopped"
