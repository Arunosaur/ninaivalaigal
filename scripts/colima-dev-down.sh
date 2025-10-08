#!/usr/bin/env bash
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
