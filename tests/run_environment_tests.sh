#!/bin/bash
# Environment-specific test runner for mem0
# Usage: ./run_environment_tests.sh [development|docker|production|all]

set -e

ENVIRONMENT=${1:-"development"}
BASE_DIR="/Users/asrajag/Workspace/mem0"
TEST_CONTEXT="env-test-$(date +%s)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Test development environment
test_development() {
    log_info "Testing Development Environment..."
    
    # Test 1: Database connectivity
    log_info "Test 1: Database connectivity"
    cd "$BASE_DIR/server"
    if python -c "from database import DatabaseManager; from main import load_config; db = DatabaseManager(load_config()); session = db.get_session(); session.close(); print('Database connected')" 2>/dev/null; then
        log_success "Database connectivity: PASS"
    else
        log_error "Database connectivity: FAIL"
        return 1
    fi
    
    # Test 2: FastAPI server
    log_info "Test 2: FastAPI server endpoints"
    if curl -s -f "http://127.0.0.1:13370/contexts" > /dev/null; then
        log_success "FastAPI server: PASS"
    else
        log_error "FastAPI server: FAIL - Is server running? (./manage.sh start)"
        return 1
    fi
    
    # Test 3: CLI operations
    log_info "Test 3: CLI operations"
    cd "$BASE_DIR"
    if ./client/mem0 context start "$TEST_CONTEXT" > /dev/null 2>&1; then
        if ./client/mem0 remember "Development test memory" --context "$TEST_CONTEXT" > /dev/null 2>&1; then
            if ./client/mem0 recall --context "$TEST_CONTEXT" | grep -q "Development test memory"; then
                log_success "CLI operations: PASS"
            else
                log_error "CLI operations: FAIL - Memory recall failed"
                return 1
            fi
        else
            log_error "CLI operations: FAIL - Memory storage failed"
            return 1
        fi
    else
        log_error "CLI operations: FAIL - Context creation failed"
        return 1
    fi
    
    # Test 4: MCP server
    log_info "Test 4: MCP server functionality"
    cd "$BASE_DIR/server"
    if timeout 30s python test_mcp.py 2>/dev/null | grep -q "test completed"; then
        log_success "MCP server: PASS"
    else
        log_error "MCP server: FAIL"
        return 1
    fi
    
    # Test 5: Shell integration
    log_info "Test 5: Shell integration"
    cd "$BASE_DIR"
    if bash -c "source client/mem0.zsh && echo 'Shell integration loaded'" 2>/dev/null | grep -q "loaded"; then
        log_success "Shell integration: PASS"
    else
        log_error "Shell integration: FAIL"
        return 1
    fi
    
    log_success "Development environment: ALL TESTS PASSED"
}

# Test Docker environment
test_docker() {
    log_info "Testing Docker Environment..."
    
    # Test 1: Docker availability
    log_info "Test 1: Docker availability"
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed"
        return 1
    fi
    log_success "Docker available"
    
    # Test 2: PostgreSQL container
    log_info "Test 2: PostgreSQL container status"
    if docker ps | grep -q mem0-postgres; then
        log_success "PostgreSQL container: RUNNING"
    else
        log_warning "PostgreSQL container: NOT RUNNING"
        log_info "Starting PostgreSQL container..."
        if docker run --name mem0-postgres -e POSTGRES_DB=mem0db -e POSTGRES_USER=mem0user -e POSTGRES_PASSWORD=mem0pass -p 5432:5432 -d postgres:15 2>/dev/null; then
            log_success "PostgreSQL container started"
            sleep 5  # Wait for startup
        else
            log_info "Container already exists, starting..."
            docker start mem0-postgres 2>/dev/null || true
            sleep 5
        fi
    fi
    
    # Test 3: Database connectivity through Docker
    log_info "Test 3: Database connectivity through Docker"
    if docker exec mem0-postgres pg_isready -U mem0user -d mem0db 2>/dev/null | grep -q "accepting connections"; then
        log_success "Database connectivity through Docker: PASS"
    else
        log_error "Database connectivity through Docker: FAIL"
        return 1
    fi
    
    # Test 4: Docker Compose configuration
    log_info "Test 4: Docker Compose configuration"
    cd "$BASE_DIR/deploy"
    if command -v docker-compose &> /dev/null; then
        if docker-compose -f docker-compose.yml config > /dev/null 2>&1; then
            log_success "Docker Compose configuration: PASS"
        else
            log_error "Docker Compose configuration: FAIL"
            return 1
        fi
    else
        log_warning "docker-compose not available, skipping configuration test"
    fi
    
    log_success "Docker environment: ALL TESTS PASSED"
}

# Test production readiness
test_production() {
    log_info "Testing Production Readiness..."
    
    # Test 1: Required files
    log_info "Test 1: Required deployment files"
    cd "$BASE_DIR"
    required_files=(
        "deploy/Dockerfile"
        "deploy/mem0-complete-deployment.yml"
        "deploy/templates/mem0.config.json.j2"
        "server/requirements.txt"
        "mcp-client-config.json"
    )
    
    all_files_exist=true
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "Required file exists: $file"
        else
            log_error "Missing required file: $file"
            all_files_exist=false
        fi
    done
    
    if [[ "$all_files_exist" == false ]]; then
        return 1
    fi
    
    # Test 2: Ansible playbook syntax (if available)
    log_info "Test 2: Ansible playbook syntax"
    if command -v ansible-playbook &> /dev/null; then
        if ansible-playbook --syntax-check deploy/mem0-complete-deployment.yml > /dev/null 2>&1; then
            log_success "Ansible playbook syntax: PASS"
        else
            log_error "Ansible playbook syntax: FAIL"
            return 1
        fi
    else
        log_warning "Ansible not installed, skipping syntax check"
    fi
    
    # Test 3: Python dependencies
    log_info "Test 3: Python dependencies check"
    cd "$BASE_DIR/server"
    if pip check > /dev/null 2>&1; then
        log_success "Python dependencies: PASS"
    else
        log_warning "Python dependencies: Some issues detected"
    fi
    
    # Test 4: Configuration templates
    log_info "Test 4: Configuration templates validation"
    cd "$BASE_DIR/deploy/templates"
    for template in *.j2; do
        if [[ -f "$template" ]]; then
            log_success "Template exists: $template"
        fi
    done
    
    log_success "Production readiness: ALL TESTS PASSED"
}

# Run comprehensive test suite
test_all() {
    log_info "Running comprehensive test suite..."
    
    if test_development && test_docker && test_production; then
        log_success "ALL ENVIRONMENTS: TESTS PASSED"
        return 0
    else
        log_error "Some tests failed"
        return 1
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "mem0 Environment Test Runner"
    echo "=========================================="
    
    case "$ENVIRONMENT" in
        "development"|"dev")
            test_development
            ;;
        "docker")
            test_docker
            ;;
        "production"|"prod")
            test_production
            ;;
        "all")
            test_all
            ;;
        *)
            echo "Usage: $0 [development|docker|production|all]"
            echo ""
            echo "Available test environments:"
            echo "  development - Test local development setup"
            echo "  docker      - Test Docker containerized setup"
            echo "  production  - Test production deployment readiness"
            echo "  all         - Run all test suites"
            exit 1
            ;;
    esac
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test context: $TEST_CONTEXT"
    cd "$BASE_DIR"
    ./client/mem0 context delete "$TEST_CONTEXT" 2>/dev/null || true
}

# Set up cleanup trap
trap cleanup EXIT

# Run main function
main "$@"
