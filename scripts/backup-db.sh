#!/usr/bin/env bash
# Backup PostgreSQL database with pgvector and verification
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

echo "Creating backup: $BACKUP_FILE"

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
