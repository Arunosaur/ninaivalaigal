#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Stop eM sidecar
set -euo pipefail

CONTAINER_NAME="${EM_CONTAINER_NAME:-nv-em}"

log(){ printf "\033[1;35m[eM]\033[0m %s\n" "$*"; }

container stop "$CONTAINER_NAME" || true
container delete "$CONTAINER_NAME" || true
log "Stopped $CONTAINER_NAME"
