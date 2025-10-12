#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -euo pipefail
NAME="${1:-nv-api}"
container stop "$NAME" >/dev/null 2>&1 || true
container delete "$NAME" >/dev/null 2>&1 || true
echo "Stopped and removed $NAME"
