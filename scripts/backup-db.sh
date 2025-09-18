#!/usr/bin/env bash
# Backup PostgreSQL database with retention policy
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/srv/ninaivalaigal/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5433}"
POSTGRES_USER="${POSTGRES_USER:-nina}"
POSTGRES_DB="${POSTGRES_DB:-nina}"

log(){ printf "\033[1;34m[backup]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

main(){
  need pg_dump
  
  # Create backup directory
  mkdir -p "$BACKUP_DIR"
  
  # Generate backup filename with timestamp
  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  BACKUP_FILE="${BACKUP_DIR}/ninaivalaigal_${TIMESTAMP}.dump"
  
  log "Starting backup to $BACKUP_FILE"
  
  # Create compressed backup
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$POSTGRES_DB" \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="$BACKUP_FILE"
  
  # Verify backup file exists and has content
  if [[ -f "$BACKUP_FILE" && -s "$BACKUP_FILE" ]]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup completed: $BACKUP_FILE ($BACKUP_SIZE)"
  else
    die "Backup failed: file missing or empty"
  fi
  
  # Clean up old backups
  log "Cleaning up backups older than $RETENTION_DAYS days"
  find "$BACKUP_DIR" -name "ninaivalaigal_*.dump" -mtime +$RETENTION_DAYS -delete
  
  # Show current backups
  log "Current backups:"
  ls -lh "$BACKUP_DIR"/ninaivalaigal_*.dump 2>/dev/null || log "No backups found"
}

main "$@"
