#!/bin/bash

# Test script for all Developer A components
# This script tests build process for all three tasks

set -e  # Exit on any error

echo "🧪 Testing All Developer A Components"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_COMPONENTS=()

# Function to test a component
test_component() {
    local component=$1
    local dir=$2
    local description=$3

    echo ""
    print_step "Testing $component - $description"
    echo "----------------------------------------------"

    if [ ! -d "$dir" ]; then
        print_error "$component directory not found: $dir"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_COMPONENTS+=("$component (directory missing)")
        return 1
    fi

    cd "$dir" || exit

    # Check if Makefile exists
    if [ ! -f "Makefile" ]; then
        print_error "$component: Makefile not found"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_COMPONENTS+=("$component (no Makefile)")
        cd - > /dev/null || exit
        return 1
    fi

    # Check if go.mod exists for Go projects
    if [ -f "go.mod" ]; then
        print_step "Checking Go module for $component..."
        if ! go mod verify; then
            print_error "$component: Go module verification failed"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            FAILED_COMPONENTS+=("$component (go mod verify failed)")
            cd - > /dev/null || exit
            return 1
        fi
        print_success "Go module verified"

        # Try to download dependencies
        print_step "Downloading dependencies for $component..."
        if ! go mod download; then
            print_error "$component: Failed to download dependencies"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            FAILED_COMPONENTS+=("$component (dependency download failed)")
            cd - > /dev/null || exit
            return 1
        fi
        print_success "Dependencies downloaded"
    fi

    # Try to build
    print_step "Building $component..."
    if make build > build.log 2>&1; then
        print_success "$component built successfully"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        print_error "$component: Build failed"
        echo "Build log:"
        cat build.log | head -20
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILED_COMPONENTS+=("$component (build failed)")
        cd - > /dev/null || exit
        return 1
    fi

    # Clean up build log
    rm -f build.log

    cd - > /dev/null || exit
    return 0
}

# Start testing
echo "Starting comprehensive test of Developer A deliverables..."
echo "Current directory: $(pwd)"
echo ""

# Test Task #36: gRPC Gateway
test_component "Task #36 gRPC Gateway" "go-services/grpc-gateway" "HTTP gateway to gRPC services"

# Test Task #37: Load Testing Tool
test_component "Task #37 Load Tester" "go-services/load-tester" "High-performance load testing tool"

# Test Task #38: CLI Tools
test_component "Task #38 CLI Tools" "go-services/cli-tools" "Unified service management CLI"

# Summary
echo ""
echo "🏁 Test Summary"
echo "==============="
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "All components built successfully! 🎉"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Start backend services (Memory, GraphOps)"
    echo "2. Test gRPC Gateway: cd go-services/grpc-gateway && make run"
    echo "3. Test Load Tester: cd go-services/load-tester && ./load-tester validate"
    echo "4. Test CLI Tools: cd go-services/cli-tools && ./nina --help"
else
    print_error "Some components failed to build:"
    for component in "${FAILED_COMPONENTS[@]}"; do
        echo "  - $component"
    done
    echo ""
    echo "📋 Troubleshooting:"
    echo "1. Check Go version: go version (requires Go 1.21+)"
    echo "2. Check Go modules: go mod tidy in each directory"
    echo "3. Check build logs in each component directory"
    exit 1
fi
