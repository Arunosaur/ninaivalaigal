#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail
NAME="${UI_CONTAINER_NAME:-nv-ui}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
echo "Stopped and removed $NAME"
