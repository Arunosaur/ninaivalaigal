#!/usr/bin/env bash
# Restore PostgreSQL database from backup
set -euo pipefail

BACKUP_FILE="${1:-}"
TARGET_DB="${2:-nina_restore_$(date +%Y%m%d_%H%M%S)}"
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5433}"
POSTGRES_USER="${POSTGRES_USER:-nina}"

log(){ printf "\033[1;34m[restore]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

usage(){
  cat <<EOF
Usage: $0 <backup_file> [target_db_name]

Examples:
  $0 /srv/ninaivalaigal/backups/ninaivalaigal_20240101_120000.dump
  $0 backup.dump nina_test

Restores to a new database (default: nina_restore_TIMESTAMP)
EOF
  exit 1
}

main(){
  [[ -n "$BACKUP_FILE" ]] || usage
  [[ -f "$BACKUP_FILE" ]] || die "Backup file not found: $BACKUP_FILE"
  
  need pg_restore
  need psql
  
  log "Restoring $BACKUP_FILE to database: $TARGET_DB"
  
  # Create target database
  log "Creating database: $TARGET_DB"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="postgres" \
    --command="CREATE DATABASE \"$TARGET_DB\";"
  
  # Restore from backup
  log "Restoring data..."
  PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$TARGET_DB" \
    --verbose \
    --clean \
    --if-exists \
    "$BACKUP_FILE"
  
  # Verify restore
  log "Verifying restore..."
  TABLE_COUNT=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    --host="$POSTGRES_HOST" \
    --port="$POSTGRES_PORT" \
    --username="$POSTGRES_USER" \
    --dbname="$TARGET_DB" \
    --tuples-only \
    --command="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
  
  log "Restore completed: $TARGET_DB ($TABLE_COUNT tables)"
  log "Connection string: postgresql://$POSTGRES_USER@$POSTGRES_HOST:$POSTGRES_PORT/$TARGET_DB"
}

main "$@"
