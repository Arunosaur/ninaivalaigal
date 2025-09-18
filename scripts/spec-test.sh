#!/usr/bin/env bash
# Test SPEC implementation with comprehensive validation
set -euo pipefail

SPEC_ID="${1:-}"

# Source system detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/system-detect.sh"

log(){ printf "\033[1;36m[spec-test]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }
warn(){ printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }

usage(){
  cat <<EOF
Usage: $0 <SPEC_ID>

Examples:
  $0 013
  $0 011

Runs validation for the specified SPEC including:
  - Demo script execution
  - Acceptance criteria verification
  - Integration testing (if applicable)

EOF
  exit 1
}

find_spec_dir(){
  local spec_id="$1"
  
  # Find SPEC directory by ID
  local spec_dirs=(specs/${spec_id}-*)
  
  if [[ ${#spec_dirs[@]} -eq 0 || ! -d "${spec_dirs[0]}" ]]; then
    die "SPEC $spec_id not found. Available SPECs: $(ls specs/ | grep -E '^[0-9]{3}-' | cut -d'-' -f1 | sort -u | tr '\n' ' ')"
  fi
  
  if [[ ${#spec_dirs[@]} -gt 1 ]]; then
    log "Multiple SPECs found for ID $spec_id:"
    printf "  %s\n" "${spec_dirs[@]}"
    die "Please be more specific"
  fi
  
  echo "${spec_dirs[0]}"
}

run_spec_validation(){
  local spec_dir="$1"
  local spec_name=$(basename "$spec_dir")
  
  log "Running validation for SPEC: $spec_name"
  
  # Check required files exist
  [[ -f "$spec_dir/spec.md" ]] || die "Missing spec.md in $spec_dir"
  [[ -f "$spec_dir/demo.sh" ]] || die "Missing demo.sh in $spec_dir"
  [[ -x "$spec_dir/demo.sh" ]] || die "demo.sh is not executable in $spec_dir"
  
  # Run demo script
  log "Executing demo script..."
  if bash "$spec_dir/demo.sh"; then
    log "✅ Demo script passed"
  else
    die "❌ Demo script failed"
  fi
  
  # Check acceptance criteria if exists
  if [[ -f "$spec_dir/acceptance.md" ]]; then
    log "Checking acceptance criteria..."
    local unchecked=$(grep -c "- \[ \]" "$spec_dir/acceptance.md" || echo "0")
    local checked=$(grep -c "- \[x\]" "$spec_dir/acceptance.md" || echo "0")
    local total=$((unchecked + checked))
    
    if [[ $total -gt 0 ]]; then
      log "Acceptance criteria: $checked/$total completed"
      if [[ $unchecked -gt 0 ]]; then
        log "⚠️  $unchecked criteria still pending"
      else
        log "✅ All acceptance criteria completed"
      fi
    fi
  fi
  
  # Run integration tests if available
  if [[ -f "$spec_dir/test.py" ]]; then
    log "Running Python tests..."
    if command -v pytest >/dev/null 2>&1; then
      pytest "$spec_dir/test.py" -v || die "Python tests failed"
      log "✅ Python tests passed"
    else
      log "⚠️  pytest not available, skipping Python tests"
    fi
  fi
  
  # Check for implementation files
  local impl_files=()
  if [[ -d "server" ]]; then
    while IFS= read -r -d '' file; do
      impl_files+=("$file")
    done < <(find server -name "*$(echo "$spec_name" | cut -d'-' -f2-)*" -type f -print0 2>/dev/null || true)
  fi
  
  if [[ ${#impl_files[@]} -gt 0 ]]; then
    log "Found implementation files:"
    printf "  %s\n" "${impl_files[@]}"
  else
    log "⚠️  No implementation files found (this may be expected for planning SPECs)"
  fi
}

main(){
  [[ -n "$SPEC_ID" ]] || usage
  
  # System detection and recommendations
  eval "$(detect_system)"
  
  if [[ "${SYSTEM_ROLE:-unknown}" == "laptop" ]]; then
    warn "You're on laptop - SPEC testing works best on Mac Studio"
    warn "Consider: git push → let Studio CI validate, or connect to Studio stack"
    log "Laptop is optimized for: make spec-new, UI development, authoring"
  fi
  
  # Find SPEC directory
  SPEC_DIR=$(find_spec_dir "$SPEC_ID")
  
  log "Testing SPEC: $SPEC_DIR"
  
  # Ensure stack is available for integration testing
  if command -v make >/dev/null 2>&1; then
    log "Checking stack status for integration testing..."
    if make stack-status >/dev/null 2>&1; then
      log "✅ Stack is running - integration tests available"
    else
      log "⚠️  Stack not running - integration tests may be limited"
      if [[ "${SYSTEM_ROLE:-unknown}" == "studio" ]]; then
        log "   Start with: make stack-up"
      else
        log "   Connect to Studio stack or start local: make stack-up"
      fi
    fi
  fi
  
  # Run validation
  run_spec_validation "$SPEC_DIR"
  
  log "✅ SPEC $SPEC_ID validation complete!"
  log ""
  log "Next steps:"
  log "  - Review any pending acceptance criteria"
  log "  - Update implementation if needed"
  log "  - Commit changes when ready"
}

main "$@"
