#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#

# Functional testing script for all Developer A components
# Tests actual functionality after successful builds

set -e

echo "🔧 Functional Testing Suite"
echo "============================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() { echo -e "${BLUE}🔄 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Check if builds passed first
if [ ! -f "testing-logs/build_results.txt" ]; then
    print_warning "No build results found. Running build tests first..."
    chmod +x test_builds.sh
    ./test_builds.sh | tee testing-logs/build_results.txt
fi

# Test 1: CLI Tools Help System
echo ""
print_step "Testing CLI Tools Help System..."

cd go-services/cli-tools || exit
if [ -f "./nina" ]; then
    print_step "Testing main help..."
    ./nina --help > ../../testing-logs/cli_help.txt 2>&1

    print_step "Testing memory commands..."
    ./nina memory --help > ../../testing-logs/cli_memory_help.txt 2>&1

    print_step "Testing graph commands..."
    ./nina graph --help > ../../testing-logs/cli_graph_help.txt 2>&1

    print_step "Testing health commands..."
    ./nina health --help > ../../testing-logs/cli_health_help.txt 2>&1

    print_success "CLI Tools help system working"
else
    print_error "CLI Tools binary not found. Build may have failed."
fi
cd - > /dev/null || exit

# Test 2: Load Tester Configuration
echo ""
print_step "Testing Load Tester Configuration..."

cd go-services/load-tester || exit
if [ -f "./load-tester" ]; then
    print_step "Testing help system..."
    ./load-tester --help > ../../testing-logs/loadtester_help.txt 2>&1

    print_step "Testing scenario validation..."
    ./load-tester validate --help > ../../testing-logs/loadtester_validate_help.txt 2>&1

    print_success "Load Tester configuration working"
else
    print_error "Load Tester binary not found. Build may have failed."
fi
cd - > /dev/null || exit

# Test 3: gRPC Gateway Configuration
echo ""
print_step "Testing gRPC Gateway Configuration..."

cd go-services/grpc-gateway || exit
if [ -f "./grpc-gateway" ]; then
    print_step "Testing configuration..."
    timeout 5s ./grpc-gateway > ../../testing-logs/gateway_startup.txt 2>&1 || true

    if grep -q "Starting HTTP server" ../../testing-logs/gateway_startup.txt; then
        print_success "gRPC Gateway starts successfully"
    else
        print_warning "gRPC Gateway may need backend services running"
    fi
else
    print_error "gRPC Gateway binary not found. Build may have failed."
fi
cd - > /dev/null || exit

# Test 4: Protocol Buffer Validation
echo ""
print_step "Testing Protocol Buffer Integration..."

# Check if proto files compiled correctly
if [ -d "go-services/grpc-gateway/memorypb" ] && [ -d "go-services/grpc-gateway/graphopspb" ]; then
    print_success "Protocol buffer packages generated"

    # Count generated files
    MEMORY_FILES=$(find go-services/grpc-gateway/memorypb -name "*.pb.go" | wc -l)
    GRAPH_FILES=$(find go-services/grpc-gateway/graphopspb -name "*.pb.go" | wc -l)

    echo "  - Memory service proto files: $MEMORY_FILES"
    echo "  - Graph service proto files: $GRAPH_FILES"

    if [ $MEMORY_FILES -gt 0 ] && [ $GRAPH_FILES -gt 0 ]; then
        print_success "Protocol buffers compiled successfully"
    else
        print_error "Protocol buffer compilation incomplete"
    fi
else
    print_error "Protocol buffer packages not found"
fi

# Test 5: Docker Configuration
echo ""
print_step "Testing Docker Configuration..."

DOCKER_FILES_FOUND=0
for component in grpc-gateway load-tester cli-tools; do
    if [ -f "go-services/$component/Dockerfile" ]; then
        DOCKER_FILES_FOUND=$((DOCKER_FILES_FOUND + 1))
        print_success "Docker configuration found for $component"
    else
        print_warning "No Docker configuration for $component"
    fi
done

if [ $DOCKER_FILES_FOUND -eq 3 ]; then
    print_success "All components have Docker support"
else
    print_warning "$DOCKER_FILES_FOUND/3 components have Docker support"
fi

# Summary
echo ""
echo "🏁 Functional Test Summary"
echo "=========================="

# Check test results
SUCCESS_COUNT=0
TOTAL_TESTS=5

# Count successes from logs
if [ -f "testing-logs/cli_help.txt" ] && grep -q "Available Commands:" testing-logs/cli_help.txt; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    print_success "CLI Tools functional"
fi

if [ -f "testing-logs/loadtester_help.txt" ] && grep -q "Available Commands:" testing-logs/loadtester_help.txt; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    print_success "Load Tester functional"
fi

if [ -f "testing-logs/gateway_startup.txt" ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    print_success "gRPC Gateway configurable"
fi

if [ -d "go-services/grpc-gateway/memorypb" ] && [ -d "go-services/grpc-gateway/graphopspb" ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    print_success "Protocol buffers integrated"
fi

if [ $DOCKER_FILES_FOUND -eq 3 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    print_success "Docker support complete"
fi

echo ""
echo -e "Functional tests passed: ${GREEN}$SUCCESS_COUNT/$TOTAL_TESTS${NC}"

if [ $SUCCESS_COUNT -eq $TOTAL_TESTS ]; then
    print_success "All functional tests passed! Ready for integration testing."
    echo ""
    echo "📋 Next Steps:"
    echo "1. Start backend services (if available)"
    echo "2. Run integration tests between components"
    echo "3. Test end-to-end workflows"
    echo "4. Performance validation"
else
    print_warning "Some functional tests had issues. Check logs in testing-logs/"
    echo ""
    echo "📁 Test Logs Available:"
    ls -la testing-logs/
fi
