#!/bin/bash
# SPEC-054: Secret Management & Environment Hygiene
# Setup script for secure environment configuration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

log() { printf "\033[1;36m[secrets]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[error]\033[0m %s\n" "$*"; }
success() { printf "\033[1;32m[ok]\033[0m %s\n" "$*"; }

# Generate secure random password
generate_password() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Create .env file from template
create_env_file() {
    local env_file="$ROOT_DIR/.env"
    local template_file="$ROOT_DIR/.env.example"

    if [[ -f "$env_file" ]]; then
        warn ".env file already exists. Backing up to .env.backup"
        cp "$env_file" "$env_file.backup"
    fi

    log "Creating .env file from template..."
    cp "$template_file" "$env_file"

    # Generate secure passwords
    local db_password
    local redis_password
    local jwt_secret
    local memory_secret

    db_password=$(generate_password 24)
    redis_password=$(generate_password 24)
    jwt_secret=$(generate_password 48)
    memory_secret=$(generate_password 32)

    # Replace placeholders with secure values
    sed -i.bak \
        -e "s/CHANGE_ME_DB_PASSWORD/$db_password/g" \
        -e "s/CHANGE_ME_REDIS_PASSWORD/$redis_password/g" \
        -e "s/dev-secret-change-in-production/$jwt_secret/g" \
        -e "s/dev-memory-secret-change-in-production/$memory_secret/g" \
        "$env_file"

    # Remove backup file
    rm -f "$env_file.bak"

    success "Created .env file with secure passwords"
    log "Database password: [HIDDEN]"
    log "Redis password: [HIDDEN]"
    log "JWT secret: [HIDDEN]"
    log "Memory secret: [HIDDEN]"
}

# Scan for potential secrets in codebase
scan_for_secrets() {
    log "Scanning for potential hardcoded secrets..."

    local issues_found=0

    # Check for common secret patterns
    local patterns=(
        "password.*=.*[\"'][^\"']{8,}"
        "secret.*=.*[\"'][^\"']{8,}"
        "key.*=.*[\"'][^\"']{8,}"
        "token.*=.*[\"'][^\"']{8,}"
        "change_me_securely"
        "nina_redis_dev_password"
        "test-jwt-secret"
    )

    for pattern in "${patterns[@]}"; do
        local matches
        matches=$(grep -r -E "$pattern" "$ROOT_DIR" \
            --include="*.py" \
            --include="*.sh" \
            --include="*.yml" \
            --include="*.yaml" \
            --include="*.json" \
            --exclude-dir=".git" \
            --exclude-dir="node_modules" \
            --exclude-dir="htmlcov" \
            --exclude-dir="client" \
            2>/dev/null || true)

        if [[ -n "$matches" ]]; then
            warn "Found potential secrets matching pattern: $pattern"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            ((issues_found++))
        fi
    done

    if [[ $issues_found -eq 0 ]]; then
        success "No obvious hardcoded secrets found"
    else
        error "Found $issues_found potential secret issues"
        warn "Review the above matches and replace with environment variables"
    fi
}

# Validate environment configuration
validate_env() {
    local env_file="$ROOT_DIR/.env"

    if [[ ! -f "$env_file" ]]; then
        error ".env file not found. Run with --create-env first"
        return 1
    fi

    log "Validating .env configuration..."

    # Source the .env file
    set -a
    source "$env_file"
    set +a

    # Check required variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
        "NINAIVALAIGAL_JWT_SECRET"
        "MEMORY_SHARED_SECRET"
    )

    local missing_vars=0
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Missing required environment variable: $var"
            ((missing_vars++))
        elif [[ "${!var}" == *"CHANGE_ME"* ]]; then
            error "Environment variable $var still contains placeholder value"
            ((missing_vars++))
        fi
    done

    if [[ $missing_vars -eq 0 ]]; then
        success "Environment configuration is valid"
    else
        error "Found $missing_vars configuration issues"
        return 1
    fi
}

# Show usage
show_usage() {
    cat << EOF
SPEC-054: Secret Management & Environment Hygiene

Usage: $0 [OPTIONS]

Options:
    --create-env     Create .env file from template with secure passwords
    --scan          Scan codebase for hardcoded secrets
    --validate      Validate .env configuration
    --all           Run all operations (scan, create-env, validate)
    --help          Show this help message

Examples:
    $0 --create-env    # Create secure .env file
    $0 --scan          # Scan for hardcoded secrets
    $0 --all           # Complete secret hygiene check

EOF
}

# Main function
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            --create-env)
                create_env_file
                shift
                ;;
            --scan)
                scan_for_secrets
                shift
                ;;
            --validate)
                validate_env
                shift
                ;;
            --all)
                scan_for_secrets
                create_env_file
                validate_env
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

main "$@"
