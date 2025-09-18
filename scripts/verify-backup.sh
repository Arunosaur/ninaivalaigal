#!/usr/bin/env bash
# Verify backup integrity without full restore
set -euo pipefail

BACKUP_FILE="${1:-}"

log(){ printf "\033[1;32m[verify]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }
warn(){ printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }

need(){ command -v "$1" >/dev/null 2>&1 || die "Missing '$1'"; }

usage(){
  cat <<EOF
Usage: $0 <backup_file>

Examples:
  $0 /srv/ninaivalaigal/backups/nina-20240101-120000.dump
  $0 latest  # Finds most recent backup

Verifies backup file integrity without performing full restore.
EOF
  exit 1
}

find_latest_backup(){
  local backup_dir="${BACKUP_DIR:-/srv/ninaivalaigal/backups}"
  
  if [[ ! -d "$backup_dir" ]]; then
    die "Backup directory not found: $backup_dir"
  fi
  
  local latest=$(find "$backup_dir" -name "nina-*.dump" -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)
  
  if [[ -z "$latest" ]]; then
    die "No backup files found in $backup_dir"
  fi
  
  echo "$latest"
}

verify_backup_format(){
  local backup_file="$1"
  
  log "Verifying backup format: $(basename "$backup_file")"
  
  # Check file exists and has content
  if [[ ! -f "$backup_file" ]]; then
    die "Backup file not found: $backup_file"
  fi
  
  if [[ ! -s "$backup_file" ]]; then
    die "Backup file is empty: $backup_file"
  fi
  
  local file_size=$(du -h "$backup_file" | cut -f1)
  log "File size: $file_size"
  
  # Verify pg_dump format
  if ! pg_restore -l "$backup_file" >/dev/null 2>&1; then
    die "Invalid pg_dump format or corrupted file"
  fi
  
  log "✅ Backup format is valid"
}

analyze_backup_contents(){
  local backup_file="$1"
  
  log "Analyzing backup contents..."
  
  # Get table of contents
  local toc=$(pg_restore -l "$backup_file" 2>/dev/null)
  
  # Count different object types
  local tables=$(echo "$toc" | grep -c "TABLE DATA" || echo "0")
  local indexes=$(echo "$toc" | grep -c "INDEX" || echo "0") 
  local sequences=$(echo "$toc" | grep -c "SEQUENCE" || echo "0")
  local functions=$(echo "$toc" | grep -c "FUNCTION" || echo "0")
  local extensions=$(echo "$toc" | grep -c "EXTENSION" || echo "0")
  
  log "📊 Backup contents:"
  log "   Tables: $tables"
  log "   Indexes: $indexes" 
  log "   Sequences: $sequences"
  log "   Functions: $functions"
  log "   Extensions: $extensions"
  
  # Check for pgvector extension
  if echo "$toc" | grep -q "EXTENSION.*vector"; then
    log "✅ pgvector extension found"
  else
    warn "⚠️  pgvector extension not found in backup"
  fi
  
  # Check for critical tables (customize based on your schema)
  local critical_tables=("users" "memories" "embeddings")
  for table in "${critical_tables[@]}"; do
    if echo "$toc" | grep -q "TABLE DATA.*$table"; then
      log "✅ Critical table found: $table"
    else
      warn "⚠️  Critical table missing: $table"
    fi
  done
}

test_partial_restore(){
  local backup_file="$1"
  
  log "Testing partial restore (schema only)..."
  
  # Create temporary database for testing
  local test_db="nina_verify_$(date +%s)"
  local postgres_host="${POSTGRES_HOST:-127.0.0.1}"
  local postgres_port="${POSTGRES_PORT:-5433}"
  local postgres_user="${POSTGRES_USER:-nina}"
  
  if [[ -z "${POSTGRES_PASSWORD:-}" ]]; then
    warn "POSTGRES_PASSWORD not set - skipping restore test"
    return 0
  fi
  
  # Create test database
  if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    --host="$postgres_host" \
    --port="$postgres_port" \
    --username="$postgres_user" \
    --dbname="postgres" \
    --command="CREATE DATABASE \"$test_db\";" 2>/dev/null; then
    warn "Could not create test database - skipping restore test"
    return 0
  fi
  
  # Restore schema only
  if PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
    --host="$postgres_host" \
    --port="$postgres_port" \
    --username="$postgres_user" \
    --dbname="$test_db" \
    --schema-only \
    --quiet \
    "$backup_file" 2>/dev/null; then
    log "✅ Schema restore test passed"
  else
    warn "⚠️  Schema restore test failed"
  fi
  
  # Cleanup test database
  PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    --host="$postgres_host" \
    --port="$postgres_port" \
    --username="$postgres_user" \
    --dbname="postgres" \
    --command="DROP DATABASE \"$test_db\";" 2>/dev/null || true
}

main(){
  need pg_restore
  
  if [[ -z "$BACKUP_FILE" ]]; then
    usage
  fi
  
  # Handle 'latest' keyword
  if [[ "$BACKUP_FILE" == "latest" ]]; then
    BACKUP_FILE=$(find_latest_backup)
    log "Using latest backup: $BACKUP_FILE"
  fi
  
  # Verify backup
  verify_backup_format "$BACKUP_FILE"
  analyze_backup_contents "$BACKUP_FILE"
  test_partial_restore "$BACKUP_FILE"
  
  log "✅ Backup verification complete: $(basename "$BACKUP_FILE")"
  log "🔗 File: $BACKUP_FILE"
}

main "$@"
