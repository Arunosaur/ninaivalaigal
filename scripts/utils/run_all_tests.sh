#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#

# Master test runner for all Developer A components
# Runs build tests, functional tests, and integration tests

set -e

echo "🧪 Complete Testing Suite for Developer A Tasks"
echo "==============================================="
echo "Testing Tasks #36, #37, and #38"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

print_header() { echo -e "${BOLD}${BLUE}$1${NC}"; }
print_step() { echo -e "${BLUE}🔄 $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Ensure we're in the right directory
if [ ! -d "go-services" ]; then
    print_error "go-services directory not found. Are you in the right directory?"
    echo "Current directory: $(pwd)"
    echo "Please run from the ninaivalaigal root directory"
    exit 1
fi

# Create testing directory
mkdir -p testing-logs
echo "$(date)" > testing-logs/test_run_timestamp.txt

# Phase 1: Build Tests
print_header "🏗️  Phase 1: Build Testing"
echo "================================"

print_step "Making test scripts executable..."
chmod +x test_builds.sh
chmod +x run_functional_tests.sh
chmod +x integration_test.sh

print_step "Running build tests..."
if ./test_builds.sh 2>&1 | tee testing-logs/build_results.txt; then
    print_success "Build tests completed successfully"
    BUILD_SUCCESS=true
else
    print_error "Build tests failed"
    BUILD_SUCCESS=false
fi

# Phase 2: Functional Tests
print_header "🔧 Phase 2: Functional Testing"
echo "====================================="

if [ "$BUILD_SUCCESS" = true ]; then
    print_step "Running functional tests..."
    if ./run_functional_tests.sh 2>&1 | tee testing-logs/functional_results.txt; then
        print_success "Functional tests completed successfully"
        FUNCTIONAL_SUCCESS=true
    else
        print_error "Functional tests had issues"
        FUNCTIONAL_SUCCESS=false
    fi
else
    print_warning "Skipping functional tests due to build failures"
    FUNCTIONAL_SUCCESS=false
fi

# Phase 3: Integration Tests
print_header "🔗 Phase 3: Integration Testing"
echo "=================================="

if [ "$FUNCTIONAL_SUCCESS" = true ]; then
    print_step "Running integration tests..."
    if ./integration_test.sh 2>&1 | tee testing-logs/integration_results.txt; then
        print_success "Integration tests completed successfully"
        INTEGRATION_SUCCESS=true
    else
        print_error "Integration tests had issues"
        INTEGRATION_SUCCESS=false
    fi
else
    print_warning "Skipping integration tests due to functional test issues"
    INTEGRATION_SUCCESS=false
fi

# Phase 4: Summary Report
print_header "📊 Phase 4: Test Summary Report"
echo "=================================="

# Count test results
TOTAL_PHASES=3
PASSED_PHASES=0

echo ""
echo "Test Phase Results:"
if [ "$BUILD_SUCCESS" = true ]; then
    print_success "Build Tests: PASSED"
    PASSED_PHASES=$((PASSED_PHASES + 1))
else
    print_error "Build Tests: FAILED"
fi

if [ "$FUNCTIONAL_SUCCESS" = true ]; then
    print_success "Functional Tests: PASSED"
    PASSED_PHASES=$((PASSED_PHASES + 1))
else
    print_error "Functional Tests: FAILED/SKIPPED"
fi

if [ "$INTEGRATION_SUCCESS" = true ]; then
    print_success "Integration Tests: PASSED"
    PASSED_PHASES=$((PASSED_PHASES + 1))
else
    print_error "Integration Tests: FAILED/SKIPPED"
fi

echo ""
echo "📈 Overall Test Score: $PASSED_PHASES/$TOTAL_PHASES phases passed"

# Detailed results
echo ""
print_header "📋 Detailed Results"
echo "===================="

echo "Component Status:"
if [ -f "testing-logs/build_results.txt" ]; then
    if grep -q "Task #36 gRPC Gateway.*built successfully" testing-logs/build_results.txt; then
        print_success "Task #36 (gRPC Gateway): Built & Ready"
    else
        print_error "Task #36 (gRPC Gateway): Build Issues"
    fi

    if grep -q "Task #37 Load Tester.*built successfully" testing-logs/build_results.txt; then
        print_success "Task #37 (Load Tester): Built & Ready"
    else
        print_error "Task #37 (Load Tester): Build Issues"
    fi

    if grep -q "Task #38 CLI Tools.*built successfully" testing-logs/build_results.txt; then
        print_success "Task #38 (CLI Tools): Built & Ready"
    else
        print_error "Task #38 (CLI Tools): Build Issues"
    fi
fi

# Final assessment
echo ""
if [ $PASSED_PHASES -eq $TOTAL_PHASES ]; then
    print_header "🎉 COMPLETE SUCCESS!"
    echo "===================="
    echo ""
    print_success "All Developer A tasks tested and validated!"
    echo ""
    echo "✅ Task #36: gRPC Gateway - HTTP-to-gRPC translation layer"
    echo "✅ Task #37: Load Tester - High-performance testing tool"
    echo "✅ Task #38: CLI Tools - Unified service management interface"
    echo ""
    echo "🚀 Ready for Production Deployment!"
    echo ""
    echo "Next Steps:"
    echo "1. Deploy to staging environment"
    echo "2. Run live integration tests with backend services"
    echo "3. Performance validation under realistic loads"
    echo "4. Security audit and compliance checks"

elif [ $PASSED_PHASES -eq 2 ]; then
    print_warning "Mostly Successful - Minor Issues"
    echo "================================="
    echo ""
    echo "Most components are working correctly."
    echo "Check the detailed logs for specific issues to resolve."

elif [ $PASSED_PHASES -eq 1 ]; then
    print_warning "Partial Success - Significant Issues"
    echo "===================================="
    echo ""
    echo "Some core functionality is working, but there are"
    echo "significant issues that need to be addressed."

else
    print_error "Testing Failed - Major Issues"
    echo "============================="
    echo ""
    echo "Fundamental issues prevent the components from working."
    echo "Review build logs and fix basic compilation/configuration issues."
fi

echo ""
echo "📁 Test Logs Location: testing-logs/"
echo "   - build_results.txt: Build test output"
echo "   - functional_results.txt: Functional test output"
echo "   - integration_results.txt: Integration test output"
echo "   - integration/: Detailed integration test files"

# Create summary report
cat > testing-logs/FINAL_TEST_REPORT.md << EOF
# Developer A Tasks - Final Test Report

**Test Run:** $(date)
**Location:** $(pwd)

## Summary
- **Build Tests:** $([ "$BUILD_SUCCESS" = true ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Functional Tests:** $([ "$FUNCTIONAL_SUCCESS" = true ] && echo "✅ PASSED" || echo "❌ FAILED")
- **Integration Tests:** $([ "$INTEGRATION_SUCCESS" = true ] && echo "✅ PASSED" || echo "❌ FAILED")

**Overall Score:** $PASSED_PHASES/$TOTAL_PHASES phases passed

## Component Status

### Task #36: gRPC Gateway
- **Purpose:** HTTP REST API gateway with gRPC backend translation
- **Build Status:** $(grep -q "Task #36.*built successfully" testing-logs/build_results.txt 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED")
- **Features:** Protocol buffers, HTTP handlers, service clients, health checks

### Task #37: Load Testing Tool
- **Purpose:** High-performance concurrent HTTP load testing
- **Build Status:** $(grep -q "Task #37.*built successfully" testing-logs/build_results.txt 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED")
- **Features:** Cobra CLI, scenario support, real-time metrics, Docker support

### Task #38: CLI Tools
- **Purpose:** Unified command-line interface for service management
- **Build Status:** $(grep -q "Task #38.*built successfully" testing-logs/build_results.txt 2>/dev/null && echo "✅ SUCCESS" || echo "❌ FAILED")
- **Features:** Memory ops, graph commands, health monitoring, interactive mode

## Integration Assessment

All three components are designed to work together:
- CLI Tools can manage and monitor the gRPC Gateway
- CLI Tools can control and configure the Load Tester
- Load Tester can validate gRPC Gateway endpoints
- All components use compatible configuration patterns

## Recommendations

$(if [ $PASSED_PHASES -eq $TOTAL_PHASES ]; then
    echo "🚀 **READY FOR PRODUCTION**"
    echo ""
    echo "All components tested successfully. Recommended next steps:"
    echo "1. Deploy to staging environment"
    echo "2. Run integration tests with live backend services"
    echo "3. Performance validation"
    echo "4. Security audit"
elif [ $PASSED_PHASES -ge 2 ]; then
    echo "⚠️ **MOSTLY READY - MINOR FIXES NEEDED**"
    echo ""
    echo "Most functionality works. Address specific issues in logs."
elif [ $PASSED_PHASES -eq 1 ]; then
    echo "🔧 **SIGNIFICANT WORK NEEDED**"
    echo ""
    echo "Core functionality works but major issues remain."
else
    echo "❌ **REQUIRES DEBUGGING**"
    echo ""
    echo "Fundamental issues prevent proper operation."
fi)

## Files Generated
- Build logs: testing-logs/build_results.txt
- Functional logs: testing-logs/functional_results.txt
- Integration logs: testing-logs/integration_results.txt
- Integration scenarios: testing-logs/integration/
- This report: testing-logs/FINAL_TEST_REPORT.md
EOF

echo ""
print_success "Final test report saved: testing-logs/FINAL_TEST_REPORT.md"

# Exit with appropriate code
if [ $PASSED_PHASES -eq $TOTAL_PHASES ]; then
    exit 0
elif [ $PASSED_PHASES -ge 2 ]; then
    exit 1
else
    exit 2
fi
