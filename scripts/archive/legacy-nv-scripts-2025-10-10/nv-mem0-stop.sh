#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail
CONTAINER_NAME="${MEM0_CONTAINER_NAME:-nv-mem0}"
container stop "$CONTAINER_NAME" || true
container delete "$CONTAINER_NAME" || true
echo "[mem0] Stopped $CONTAINER_NAME"
