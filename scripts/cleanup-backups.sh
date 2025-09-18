#!/usr/bin/env bash
# Backup retention and cleanup with safety checks
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/srv/ninaivalaigal/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DRY_RUN="${DRY_RUN:-false}"

log(){ printf "\033[1;36m[cleanup]\033[0m %s\n" "$*"; }
warn(){ printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }

usage(){
  cat <<EOF
Usage: $0 [options]

Options:
  --retention-days N    Keep backups for N days (default: 14)
  --backup-dir PATH     Backup directory (default: /srv/ninaivalaigal/backups)
  --dry-run            Show what would be deleted without deleting
  --help               Show this help

Environment Variables:
  BACKUP_DIR           Backup directory path
  RETENTION_DAYS       Days to retain backups
  DRY_RUN             Set to 'true' for dry run

Examples:
  $0                                    # Clean backups older than 14 days
  $0 --retention-days 30                # Keep 30 days of backups
  $0 --dry-run                         # Preview what would be deleted
  RETENTION_DAYS=7 $0                  # Keep only 1 week of backups
EOF
  exit 1
}

parse_args(){
  while [[ $# -gt 0 ]]; do
    case $1 in
      --retention-days)
        RETENTION_DAYS="$2"
        shift 2
        ;;
      --backup-dir)
        BACKUP_DIR="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --help)
        usage
        ;;
      *)
        die "Unknown option: $1"
        ;;
    esac
  done
}

validate_inputs(){
  # Validate retention days
  if ! [[ "$RETENTION_DAYS" =~ ^[0-9]+$ ]] || [[ "$RETENTION_DAYS" -lt 1 ]]; then
    die "Invalid retention days: $RETENTION_DAYS (must be positive integer)"
  fi
  
  # Validate backup directory
  if [[ ! -d "$BACKUP_DIR" ]]; then
    die "Backup directory not found: $BACKUP_DIR"
  fi
  
  # Safety check - ensure we're in the right directory
  if [[ ! "$BACKUP_DIR" =~ ninaivalaigal ]]; then
    die "Safety check failed: backup directory path must contain 'ninaivalaigal'"
  fi
}

find_old_backups(){
  local backup_dir="$1"
  local retention_days="$2"
  
  # Find backup files older than retention period
  find "$backup_dir" -name "nina-*.dump" -type f -mtime +$retention_days 2>/dev/null || true
}

analyze_backups(){
  local backup_dir="$1"
  local retention_days="$2"
  
  log "Analyzing backups in: $backup_dir"
  log "Retention policy: $retention_days days"
  
  # Count all backups
  local total_backups=$(find "$backup_dir" -name "nina-*.dump" -type f 2>/dev/null | wc -l)
  log "Total backups found: $total_backups"
  
  if [[ "$total_backups" -eq 0 ]]; then
    warn "No backup files found"
    return 0
  fi
  
  # Find old backups
  local old_backups=$(find_old_backups "$backup_dir" "$retention_days")
  local old_count=$(echo "$old_backups" | grep -c "nina-" || echo "0")
  
  log "Backups to clean: $old_count"
  log "Backups to keep: $((total_backups - old_count))"
  
  if [[ "$old_count" -eq 0 ]]; then
    log "✅ No cleanup needed - all backups within retention period"
    return 0
  fi
  
  # Show what will be cleaned
  log "Files to be removed:"
  echo "$old_backups" | while read -r file; do
    if [[ -n "$file" ]]; then
      local size=$(du -h "$file" 2>/dev/null | cut -f1 || echo "unknown")
      local age=$(find "$file" -printf '%C+\n' 2>/dev/null || echo "unknown")
      log "  $(basename "$file") ($size, created: $age)"
    fi
  done
  
  # Calculate space to be freed
  local total_size=0
  echo "$old_backups" | while read -r file; do
    if [[ -n "$file" && -f "$file" ]]; then
      local size=$(du -b "$file" 2>/dev/null | cut -f1 || echo "0")
      total_size=$((total_size + size))
    fi
  done
  
  if [[ "$total_size" -gt 0 ]]; then
    local human_size=$(numfmt --to=iec --suffix=B "$total_size" 2>/dev/null || echo "${total_size} bytes")
    log "Space to be freed: $human_size"
  fi
}

cleanup_backups(){
  local backup_dir="$1"
  local retention_days="$2"
  local dry_run="$3"
  
  local old_backups=$(find_old_backups "$backup_dir" "$retention_days")
  local old_count=$(echo "$old_backups" | grep -c "nina-" || echo "0")
  
  if [[ "$old_count" -eq 0 ]]; then
    return 0
  fi
  
  if [[ "$dry_run" == "true" ]]; then
    log "🔍 DRY RUN - No files will be deleted"
    return 0
  fi
  
  # Safety check - ensure we have recent backups before deleting old ones
  local recent_backups=$(find "$backup_dir" -name "nina-*.dump" -type f -mtime -1 2>/dev/null | wc -l)
  if [[ "$recent_backups" -eq 0 ]]; then
    die "Safety check failed: No recent backups found (within 24 hours). Aborting cleanup."
  fi
  
  log "🗑️  Cleaning up old backups..."
  local deleted_count=0
  local failed_count=0
  
  echo "$old_backups" | while read -r file; do
    if [[ -n "$file" && -f "$file" ]]; then
      if rm "$file" 2>/dev/null; then
        log "✅ Deleted: $(basename "$file")"
        deleted_count=$((deleted_count + 1))
      else
        warn "❌ Failed to delete: $(basename "$file")"
        failed_count=$((failed_count + 1))
      fi
    fi
  done
  
  log "Cleanup completed: $deleted_count deleted, $failed_count failed"
}

show_final_status(){
  local backup_dir="$1"
  
  log "Final backup status:"
  
  if [[ -d "$backup_dir" ]]; then
    local remaining=$(find "$backup_dir" -name "nina-*.dump" -type f 2>/dev/null | wc -l)
    log "Remaining backups: $remaining"
    
    if [[ "$remaining" -gt 0 ]]; then
      log "Recent backups:"
      find "$backup_dir" -name "nina-*.dump" -type f -printf '%C+ %s %p\n' 2>/dev/null | \
        sort -r | head -5 | while read -r date size path; do
        local human_size=$(numfmt --to=iec --suffix=B "$size" 2>/dev/null || echo "${size}B")
        log "  $(basename "$path") ($human_size, $date)"
      done
    fi
  fi
}

main(){
  parse_args "$@"
  validate_inputs
  
  log "Backup cleanup starting..."
  log "Directory: $BACKUP_DIR"
  log "Retention: $RETENTION_DAYS days"
  log "Mode: $([ "$DRY_RUN" == "true" ] && echo "DRY RUN" || echo "LIVE")"
  
  analyze_backups "$BACKUP_DIR" "$RETENTION_DAYS"
  cleanup_backups "$BACKUP_DIR" "$RETENTION_DAYS" "$DRY_RUN"
  show_final_status "$BACKUP_DIR"
  
  log "✅ Backup cleanup completed"
}

main "$@"
