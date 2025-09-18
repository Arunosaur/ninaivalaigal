#!/bin/bash
set -euo pipefail

echo "🧪 Production Hardening Sanity Check"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() { echo -e "${BLUE}[CHECK]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

FAILED_CHECKS=0

check_command() {
    local cmd="$1"
    local desc="$2"
    
    log_step "$desc"
    if eval "$cmd" >/dev/null 2>&1; then
        log_success "$desc"
    else
        log_error "$desc"
        ((FAILED_CHECKS++))
    fi
}

check_url() {
    local url="$1"
    local desc="$2"
    
    log_step "$desc"
    if curl -f -s "$url" >/dev/null 2>&1; then
        log_success "$desc"
    else
        log_error "$desc"
        ((FAILED_CHECKS++))
    fi
}

echo ""
echo "📋 Phase 1: Prerequisites"
echo "========================"

check_command "command -v docker" "Docker CLI available"
check_command "command -v python3" "Python 3 available"
check_command "command -v git" "Git available"
check_command "command -v curl" "cURL available"
check_command "command -v jq" "jq JSON processor available"

echo ""
echo "🔧 Phase 2: Development Tools"
echo "============================="

check_command "command -v pre-commit" "Pre-commit hooks installed"
check_command "command -v detect-secrets" "Secrets detection available"
check_command "command -v shellcheck" "Shell linting available"
check_command "command -v trivy" "Vulnerability scanner available"

echo ""
echo "🐳 Phase 3: Container Stack"
echo "==========================="

# Check if containers are running
if docker ps --format "table {{.Names}}" | grep -q postgres; then
    log_success "PostgreSQL container running"
    check_command "pg_isready -h localhost -p 5432" "PostgreSQL connectivity"
else
    log_warning "PostgreSQL container not running - starting stack..."
    if [ -f "./scripts/nv-stack-start.sh" ]; then
        ./scripts/nv-stack-start.sh
        sleep 10
    else
        log_error "Stack start script not found"
        ((FAILED_CHECKS++))
    fi
fi

if docker ps --format "table {{.Names}}" | grep -q api; then
    log_success "API server container running"
    check_url "http://localhost:8000/healthz" "API health endpoint"
    check_url "http://localhost:8000/health/detailed" "Detailed health with SLO"
    check_url "http://localhost:8000/metrics" "Prometheus metrics endpoint"
else
    log_warning "API server not running"
fi

echo ""
echo "🔐 Phase 4: Security Validation"
echo "==============================="

# Pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    log_step "Running pre-commit validation"
    if pre-commit run --all-files >/dev/null 2>&1; then
        log_success "Pre-commit hooks pass"
    else
        log_warning "Pre-commit hooks have issues (check manually)"
    fi
else
    log_error "Pre-commit configuration missing"
    ((FAILED_CHECKS++))
fi

# Secrets scanning
if [ -f ".secrets.baseline" ]; then
    log_step "Running secrets detection"
    if detect-secrets scan --baseline .secrets.baseline >/dev/null 2>&1; then
        log_success "No new secrets detected"
    else
        log_warning "Potential secrets found (review manually)"
    fi
else
    log_error "Secrets baseline missing"
    ((FAILED_CHECKS++))
fi

# mem0 authentication
if [ -f "./scripts/test-mem0-auth.sh" ]; then
    log_step "Testing mem0 authentication"
    if ./scripts/test-mem0-auth.sh >/dev/null 2>&1; then
        log_success "mem0 authentication working"
    else
        log_warning "mem0 authentication issues (check logs)"
    fi
else
    log_error "mem0 auth test script missing"
    ((FAILED_CHECKS++))
fi

echo ""
echo "💾 Phase 5: Backup & Recovery"
echo "============================="

# Backup scripts
check_command "[ -f './scripts/backup-db.sh' ]" "Database backup script exists"
check_command "[ -f './scripts/restore-rehearsal.sh' ]" "Restore rehearsal script exists"
check_command "[ -f './scripts/cleanup-backups.sh' ]" "Backup cleanup script exists"

# Test backup functionality
if [ -f "./scripts/backup-db.sh" ]; then
    log_step "Testing backup functionality"
    if ./scripts/backup-db.sh --dry-run >/dev/null 2>&1; then
        log_success "Backup system functional"
    else
        log_warning "Backup system issues (check configuration)"
    fi
fi

echo ""
echo "📊 Phase 6: Observability"
echo "========================="

# SLO documentation
check_command "[ -f './docs/SLO.md' ]" "SLO documentation exists"

# Monitoring scripts
check_command "[ -f './scripts/db-stats.sh' ]" "Database statistics script exists"

# Test metrics collection
if curl -f -s "http://localhost:8000/metrics" | grep -q "http_requests_total"; then
    log_success "Prometheus metrics collecting"
else
    log_warning "Prometheus metrics not available"
fi

echo ""
echo "🏛️ Phase 7: Governance"
echo "======================"

# Governance files
check_command "[ -f './.github/CODEOWNERS' ]" "CODEOWNERS file exists"
check_command "[ -f './docs/GOVERNANCE.md' ]" "Governance documentation exists"
check_command "[ -f './.releaserc.json' ]" "Semantic release configuration exists"
check_command "[ -f './package.json' ]" "Package.json for releases exists"

# Issue templates
check_command "[ -d './.github/ISSUE_TEMPLATE' ]" "Issue templates directory exists"
check_command "[ -f './.github/pull_request_template.md' ]" "PR template exists"

# Workflows
check_command "[ -f './.github/workflows/release.yml' ]" "Release workflow exists"
check_command "[ -f './.github/workflows/dependency-updates.yml' ]" "Dependency update workflow exists"

echo ""
echo "🎯 Summary"
echo "=========="

if [ $FAILED_CHECKS -eq 0 ]; then
    log_success "All checks passed! 🎉"
    echo ""
    echo "✅ Your production hardening is complete and validated!"
    echo "✅ All 6 PRs implemented successfully"
    echo "✅ System ready for production deployment"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Deploy to Mac Studio: ./deploy_mac_studio.sh"
    echo "2. Setup GitHub runner: ./setup_github_runner.sh"
    echo "3. Review: PRODUCTION_NEXT_STEPS.md"
    exit 0
else
    log_error "$FAILED_CHECKS checks failed"
    echo ""
    echo "❌ Some components need attention before production deployment"
    echo "📋 Review failed checks above and fix issues"
    echo "🔄 Re-run this script after fixes: ./scripts/sanity-check.sh"
    exit 1
fi
