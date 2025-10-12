#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Stop ninaivalaigal dev environment on Colima

set -euo pipefail

NINA_ENV="${NINA_ENV:-dev}"

log() { printf "\033[1;34m[colima]\033[0m %s\n" "$*"; }

main() {
  cd "$(dirname "$0")/.."

  log "Stopping Colima dev environment..."
  docker-compose -f compose.colima.yml --env-file .env.colima.dev down

  log "✅ Colima dev environment stopped"
  log "   Data preserved in ./data/postgres_${NINA_ENV} and ./data/redis_${NINA_ENV}"
}

main "$@"
