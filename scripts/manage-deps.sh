#!/bin/bash
# SPEC-056: Dependency & Testing Improvements
# Dependency management script using pip-tools

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REQUIREMENTS_DIR="$ROOT_DIR/requirements"

log() { printf "\033[1;36m[deps]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[error]\033[0m %s\n" "$*"; }
success() { printf "\033[1;32m[ok]\033[0m %s\n" "$*"; }

# Install pip-tools if not available
ensure_pip_tools() {
    if ! command -v pip-compile >/dev/null 2>&1; then
        log "Installing pip-tools..."
        pip install pip-tools
    fi
}

# Compile requirements files
compile_requirements() {
    local target="${1:-all}"
    
    ensure_pip_tools
    
    cd "$REQUIREMENTS_DIR"
    
    case "$target" in
        "base"|"all")
            log "Compiling base requirements..."
            pip-compile --resolver=backtracking --upgrade base.in
            ;;
    esac
    
    case "$target" in
        "dev"|"all")
            log "Compiling development requirements..."
            pip-compile --resolver=backtracking --upgrade dev.in
            ;;
    esac
    
    case "$target" in
        "test"|"all")
            log "Compiling test requirements..."
            pip-compile --resolver=backtracking --upgrade test.in
            ;;
    esac
    
    success "Requirements compilation complete"
}

# Install dependencies
install_requirements() {
    local env="${1:-dev}"
    
    ensure_pip_tools
    
    case "$env" in
        "base"|"prod"|"production")
            log "Installing base/production requirements..."
            pip-sync "$REQUIREMENTS_DIR/base.txt"
            ;;
        "dev"|"development")
            log "Installing development requirements..."
            pip-sync "$REQUIREMENTS_DIR/dev.txt"
            ;;
        "test")
            log "Installing test requirements..."
            pip-sync "$REQUIREMENTS_DIR/test.txt"
            ;;
        *)
            error "Unknown environment: $env"
            error "Valid options: base, dev, test"
            exit 1
            ;;
    esac
    
    success "Dependencies installed for $env environment"
}

# Check for dependency conflicts
check_conflicts() {
    log "Checking for dependency conflicts..."
    
    if command -v pip-check >/dev/null 2>&1; then
        pip-check
    else
        log "Installing pip-check for conflict detection..."
        pip install pip-check
        pip-check
    fi
    
    success "Dependency conflict check complete"
}

# Update all dependencies to latest compatible versions
update_all() {
    log "Updating all dependencies to latest compatible versions..."
    
    compile_requirements "all"
    
    # Install dev requirements by default for development
    install_requirements "dev"
    
    check_conflicts
    
    success "All dependencies updated"
}

# Show dependency tree
show_tree() {
    if command -v pipdeptree >/dev/null 2>&1; then
        pipdeptree
    else
        log "Installing pipdeptree..."
        pip install pipdeptree
        pipdeptree
    fi
}

# Clean up old requirements files
cleanup_old() {
    log "Cleaning up old requirements files..."
    
    # Backup old files
    local backup_dir="$ROOT_DIR/requirements_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Move old files to backup
    for file in "$ROOT_DIR"/requirements*.txt "$ROOT_DIR/server/requirements.txt"; do
        if [[ -f "$file" ]]; then
            log "Backing up $(basename "$file")"
            mv "$file" "$backup_dir/"
        fi
    done
    
    success "Old requirements files backed up to $backup_dir"
}

# Show usage
show_usage() {
    cat << EOF
SPEC-056: Dependency & Testing Improvements

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    compile [TARGET]     Compile requirements files (base|dev|test|all)
    install [ENV]        Install dependencies (base|dev|test)
    update              Update all dependencies to latest versions
    check               Check for dependency conflicts
    tree                Show dependency tree
    cleanup             Clean up old requirements files
    help                Show this help message

Examples:
    $0 compile all      # Compile all requirements files
    $0 install dev      # Install development dependencies
    $0 update           # Update everything to latest versions
    $0 check            # Check for conflicts

EOF
}

# Main function
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    case "${1:-}" in
        "compile")
            compile_requirements "${2:-all}"
            ;;
        "install")
            install_requirements "${2:-dev}"
            ;;
        "update")
            update_all
            ;;
        "check")
            check_conflicts
            ;;
        "tree")
            show_tree
            ;;
        "cleanup")
            cleanup_old
            ;;
        "help"|"--help")
            show_usage
            ;;
        *)
            error "Unknown command: ${1:-}"
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
