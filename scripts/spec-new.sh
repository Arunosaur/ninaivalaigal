#!/usr/bin/env bash
# Create new SPEC from template with automated setup
set -euo pipefail

SPEC_ID="${1:-}"
SPEC_NAME="${2:-}"

# Source system detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/system-detect.sh"

log(){ printf "\033[1;36m[spec-new]\033[0m %s\n" "$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "$*"; exit 1; }
warn(){ printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }

usage(){
  cat <<EOF
Usage: $0 <SPEC_ID> <SPEC_NAME>

Examples:
  $0 013 "memory-substrate-v2"
  $0 014 "team-rollup-layer"

Creates:
  specs/SPEC_ID-SPEC_NAME/
  ├── spec.md (from template)
  ├── acceptance.md (test criteria)
  └── demo.sh (validation script)

EOF
  exit 1
}

main(){
  [[ -n "$SPEC_ID" && -n "$SPEC_NAME" ]] || usage
  
  # System detection and recommendations (skip in deployment environments)
  # Temporarily simplified - detect_system has parsing issues with "Mac Studio"
  if [[ "${SYSTEM_IS_DEPLOYMENT:-false}" == "false" ]] && [[ $(uname -m) == "arm64" ]] && [[ $(sysctl -n hw.memsize 2>/dev/null || echo 0) -gt 100000000000 ]]; then
    warn "You're on Mac Studio - consider authoring SPECs on laptop for faster iteration"
    warn "Studio is optimized for: make stack-up && make spec-test"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 0
  elif [[ "${SYSTEM_IS_DEPLOYMENT:-false}" == "true" ]]; then
    log "Deployment environment detected - proceeding automatically"
  fi
  
  # Validate SPEC ID format
  [[ "$SPEC_ID" =~ ^[0-9]{3}$ ]] || die "SPEC_ID must be 3 digits (e.g., 013)"
  
  # Create SPEC directory
  SPEC_DIR="specs/${SPEC_ID}-${SPEC_NAME}"
  
  if [[ -d "$SPEC_DIR" ]]; then
    die "SPEC directory already exists: $SPEC_DIR"
  fi
  
  log "Creating SPEC $SPEC_ID: $SPEC_NAME"
  mkdir -p "$SPEC_DIR"
  
  # Generate spec.md from template
  log "Generating spec.md from template..."
  sed "s/\[FEATURE NAME\]/$SPEC_NAME/g; s/\[###-feature-name\]/$SPEC_ID-$SPEC_NAME/g; s/\[DATE\]/$(date +%Y-%m-%d)/g" \
    templates/spec-template.md > "$SPEC_DIR/spec.md"
  
  # Create acceptance criteria
  cat > "$SPEC_DIR/acceptance.md" <<EOF
# SPEC $SPEC_ID: $SPEC_NAME - Acceptance Criteria

## Test Scenarios

### Functional Tests
- [ ] **FT-001**: Core functionality works as specified
- [ ] **FT-002**: Error handling behaves correctly
- [ ] **FT-003**: Integration with existing systems

### Performance Tests
- [ ] **PT-001**: Response times within acceptable limits
- [ ] **PT-002**: Resource usage within bounds
- [ ] **PT-003**: Concurrent user handling

### Security Tests
- [ ] **ST-001**: Authentication/authorization enforced
- [ ] **ST-002**: Data validation prevents injection
- [ ] **ST-003**: Audit logging captures events

## Validation Commands

\`\`\`bash
# Run SPEC validation
make spec-test ID=$SPEC_ID

# Manual testing
./specs/$SPEC_ID-$SPEC_NAME/demo.sh
\`\`\`

## Success Criteria

- [ ] All functional tests pass
- [ ] Performance benchmarks met
- [ ] Security requirements satisfied
- [ ] Documentation complete
- [ ] Code review approved
EOF
  
  # Create demo/validation script
  cat > "$SPEC_DIR/demo.sh" <<EOF
#!/usr/bin/env bash
# SPEC $SPEC_ID: $SPEC_NAME - Demo and Validation Script
set -euo pipefail

log(){ printf "\033[1;35m[spec-$SPEC_ID]\033[0m %s\n" "\$*"; }
die(){ printf "\033[1;31m[fail]\033[0m %s\n" "\$*"; exit 1; }

main(){
  log "Starting SPEC $SPEC_ID validation: $SPEC_NAME"
  
  # TODO: Add your validation logic here
  log "✅ Placeholder validation - implement actual tests"
  
  # Example validation steps:
  # 1. Setup test environment
  # 2. Run functional tests
  # 3. Verify expected outcomes
  # 4. Cleanup
  
  log "SPEC $SPEC_ID validation complete"
}

main "\$@"
EOF
  
  chmod +x "$SPEC_DIR/demo.sh"
  
  # Add to git
  git add "$SPEC_DIR/"
  
  log "✅ SPEC $SPEC_ID created successfully!"
  log ""
  log "Next steps:"
  log "  1. Edit specs/$SPEC_ID-$SPEC_NAME/spec.md"
  log "  2. Implement validation in specs/$SPEC_ID-$SPEC_NAME/demo.sh"
  log "  3. Test with: make spec-test ID=$SPEC_ID"
  log "  4. Commit when ready: git commit -m 'feat: Add SPEC $SPEC_ID - $SPEC_NAME'"
}

main "$@"
