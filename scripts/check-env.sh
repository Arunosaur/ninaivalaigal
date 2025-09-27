#!/bin/bash
set -e

# Foundation Test Environment Validation Script
# This script validates the test environment for Foundation SPEC tests

echo "🔍 Foundation Test Environment Validation"
echo "========================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

# Function to check command availability
check_command() {
    local cmd=$1
    local name=$2
    if command -v $cmd >/dev/null 2>&1; then
        print_status "SUCCESS" "$name is available"
        return 0
    else
        print_status "ERROR" "$name is not available"
        return 1
    fi
}

# Function to check Docker container accessibility
check_container() {
    local image=$1
    local name=$2
    local test_cmd=$3
    
    print_status "INFO" "Testing $name container..."
    if docker run --rm $image $test_cmd >/dev/null 2>&1; then
        print_status "SUCCESS" "$name container is accessible"
        return 0
    else
        print_status "ERROR" "$name container is not accessible"
        return 1
    fi
}

# Initialize error counter
error_count=0

echo ""
echo "🐳 Docker Environment Check"
echo "-------------------------"

# Check Docker availability
if check_command "docker" "Docker"; then
    # Check if Docker daemon is running
    if docker ps >/dev/null 2>&1; then
        print_status "SUCCESS" "Docker daemon is running"
        
        # Test PostgreSQL container
        if check_container "postgres:15" "PostgreSQL" "pg_isready --help"; then
            true
        else
            ((error_count++))
        fi
        
        # Test Redis container
        if check_container "redis:7-alpine" "Redis" "redis-cli --version"; then
            true
        else
            ((error_count++))
        fi
        
    else
        print_status "ERROR" "Docker daemon is not running"
        ((error_count++))
    fi
else
    print_status "ERROR" "Docker is not installed"
    ((error_count++))
fi

echo ""
echo "🌐 Network Configuration"
echo "----------------------"

# Check network configuration
print_status "INFO" "Host: $(hostname)"
if command -v hostname >/dev/null 2>&1; then
    local_ip=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "N/A")
    print_status "INFO" "Local IP: $local_ip"
else
    print_status "WARNING" "Cannot determine local IP"
fi

# Check DNS configuration
if [ -f /etc/resolv.conf ]; then
    nameserver=$(grep nameserver /etc/resolv.conf | head -1 | awk '{print $2}' || echo "N/A")
    print_status "INFO" "DNS Server: $nameserver"
else
    print_status "WARNING" "Cannot access DNS configuration"
fi

# Test localhost connectivity
if curl -s --connect-timeout 5 http://localhost:80 >/dev/null 2>&1; then
    print_status "SUCCESS" "Localhost connectivity available"
elif command -v curl >/dev/null 2>&1; then
    print_status "INFO" "Localhost not responding (expected for fresh environment)"
else
    print_status "WARNING" "curl not available for connectivity test"
fi

echo ""
echo "🔐 Environment Variables"
echo "----------------------"

# Check required environment variables
check_env_var() {
    local var_name=$1
    local var_value=${!var_name}
    if [ -n "$var_value" ]; then
        print_status "SUCCESS" "$var_name is set"
    else
        print_status "WARNING" "$var_name is not set"
    fi
}

# Check common test environment variables
check_env_var "POSTGRES_PASSWORD"
check_env_var "REDIS_PASSWORD"
check_env_var "DATABASE_URL"
check_env_var "REDIS_URL"

# Check CI-specific variables
if [ -n "$GITHUB_ACTIONS" ]; then
    print_status "INFO" "Running in GitHub Actions environment"
    check_env_var "GITHUB_REPOSITORY"
    check_env_var "GITHUB_RUN_ID"
    check_env_var "GITHUB_SHA"
else
    print_status "INFO" "Running in local environment"
fi

echo ""
echo "🧪 Test Dependencies"
echo "------------------"

# Check Python and testing tools
if check_command "python3" "Python 3"; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_status "INFO" "Python version: $python_version"
    
    # Check if pytest is available
    if python3 -c "import pytest" 2>/dev/null; then
        pytest_version=$(python3 -c "import pytest; print(pytest.__version__)" 2>/dev/null || echo "unknown")
        print_status "SUCCESS" "pytest is available (version: $pytest_version)"
    else
        print_status "WARNING" "pytest is not available"
    fi
    
    # Check if coverage is available
    if python3 -c "import coverage" 2>/dev/null; then
        coverage_version=$(python3 -c "import coverage; print(coverage.__version__)" 2>/dev/null || echo "unknown")
        print_status "SUCCESS" "coverage is available (version: $coverage_version)"
    else
        print_status "WARNING" "coverage is not available"
    fi
else
    print_status "ERROR" "Python 3 is not available"
    ((error_count++))
fi

# Check if make is available
if check_command "make" "Make"; then
    if [ -f "Makefile" ]; then
        print_status "SUCCESS" "Makefile found"
        
        # Check for test targets
        if grep -q "test-foundation" Makefile 2>/dev/null; then
            print_status "SUCCESS" "test-foundation target available"
        else
            print_status "WARNING" "test-foundation target not found in Makefile"
        fi
    else
        print_status "WARNING" "Makefile not found"
    fi
fi

echo ""
echo "📊 Test Infrastructure"
echo "--------------------"

# Check for test directories
test_dirs=("tests" "tests/foundation" "tests/foundation/spec_007" "tests/foundation/spec_012" "tests/foundation/spec_049" "tests/foundation/spec_052" "tests/foundation/spec_058")

for dir in "${test_dirs[@]}"; do
    if [ -d "$dir" ]; then
        test_count=$(find "$dir" -name "test_*.py" | wc -l)
        print_status "SUCCESS" "$dir exists ($test_count test files)"
    else
        print_status "WARNING" "$dir does not exist"
    fi
done

# Check for configuration files
config_files=("tests/foundation/conftest.py" "tests/foundation/__init__.py" ".github/workflows/foundation-tests.yml")

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        print_status "SUCCESS" "$file exists"
    else
        print_status "WARNING" "$file does not exist"
    fi
done

echo ""
echo "📋 Summary"
echo "--------"

if [ $error_count -eq 0 ]; then
    print_status "SUCCESS" "Environment validation completed successfully"
    print_status "INFO" "Ready to run Foundation SPEC tests"
    exit 0
else
    print_status "ERROR" "Environment validation failed with $error_count error(s)"
    print_status "INFO" "Please resolve the errors before running Foundation SPEC tests"
    exit 1
fi
