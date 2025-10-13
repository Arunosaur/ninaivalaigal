#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
set -e

NAME="nv-api"
SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="/tmp/ninaivalaigal-health-fixed.log"

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') [${NAME}] $1" | tee -a "$LOGFILE"
}

if ! container list | grep -q "$NAME"; then
  log "💥 CRITICAL: $NAME container was removed! Attempting to recreate..."
  bash "$SCRIPTS/${NAME}-start.sh"
else
  log "Health check failed — restarting $NAME"
  container restart "$NAME" || {
    log "Restart failed — attempting full recreation..."
    bash "$SCRIPTS/${NAME}-start.sh"
  }
fi
