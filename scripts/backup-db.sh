#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# Backup PostgreSQL database with pgvector and verification
# US#955: DB-REPL-006: Backup from Replicas & Disaster Recovery
# Supports backup from replica if BACKUP_FROM_REPLICA=true
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_DIR:-/srv/ninaivalaigal/backups}"
BACKUP_FILE="${BACKUP_DIR}/nina-${TIMESTAMP}.dump"

# Ensure backup directory exists
mkdir -p "$(dirname "$BACKUP_FILE")"

# Database connection parameters
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5433}"
POSTGRES_USER="${POSTGRES_USER:-nina}"
POSTGRES_DB="${POSTGRES_DB:-nina}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}"

# Parse command-line arguments
USE_REPLICA=false
for arg in "$@"; do
    case $arg in
        --replica|-r)
            USE_REPLICA=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--replica]"
            echo "  --replica, -r    Backup from replica instead of primary"
            exit 0
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Check if backup from replica is enabled (via flag or env var)
BACKUP_FROM_REPLICA="${BACKUP_FROM_REPLICA:-false}"
if [ "$USE_REPLICA" = "true" ] || [ "$BACKUP_FROM_REPLICA" = "true" ]; then
    echo "Backup from replica enabled (--replica flag or BACKUP_FROM_REPLICA=true), using replica backup script..."
    exec "$(dirname "$0")/database/backup-from-replica.sh"
fi

echo "Creating backup from primary: $BACKUP_FILE"

# Create backup using pg_dump with custom format (-Fc)
PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -Fc \
  -f "$BACKUP_FILE"

echo "Wrote $BACKUP_FILE"

# Quick verification - list contents without restoring
pg_restore -l "$BACKUP_FILE" >/dev/null && echo "Verified dump format OK"

echo "Backup completed successfully"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
