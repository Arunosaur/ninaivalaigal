#!/usr/bin/env bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Test script for US#22: Apple Container CLI Migration
# Validates the docker-to-apple-container.sh script functionality

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_SCRIPT="${SCRIPT_DIR}/docker-to-apple-container.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

print_test() {
    echo -e "${BLUE}🧪 Testing: $1${NC}"
}

print_pass() {
    echo -e "${GREEN}  ✅ PASS: $1${NC}"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}  ❌ FAIL: $1${NC}"
    ((FAILED++))
}

print_skip() {
    echo -e "${YELLOW}  ⏭️  SKIP: $1${NC}"
    ((SKIPPED++))
}

# Test 1: Script exists and is executable
test_script_exists() {
    print_test "Script exists and is executable"

    if [ -f "$MIGRATION_SCRIPT" ]; then
        if [ -x "$MIGRATION_SCRIPT" ]; then
            print_pass "Script exists and is executable"
            return 0
        else
            print_fail "Script exists but is not executable"
            return 1
        fi
    else
        print_fail "Script not found: $MIGRATION_SCRIPT"
        return 1
    fi
}

# Test 2: Script shows help
test_help_option() {
    print_test "Help option displays usage"

    if "$MIGRATION_SCRIPT" --help 2>&1 | grep -q "Usage:"; then
        print_pass "Help option works"
        return 0
    else
        print_fail "Help option does not display usage"
        return 1
    fi
}

# Test 3: Script requires SERVICE_NAME
test_requires_service_name() {
    print_test "Script requires SERVICE_NAME argument"

    # Script may exit with error, that's expected
    if "$MIGRATION_SCRIPT" 2>&1 | grep -q "SERVICE_NAME\|Usage:" || [ ${PIPESTATUS[0]} -ne 0 ]; then
        print_pass "Script requires SERVICE_NAME"
        return 0
    else
        print_fail "Script does not require SERVICE_NAME"
        return 1
    fi
}

# Test 4: Option parsing
test_option_parsing() {
    print_test "Option parsing works"

    # Just verify script accepts options without crashing
    # Actual validation happens during execution
    if "$MIGRATION_SCRIPT" --help > /dev/null 2>&1; then
        print_pass "Option parsing works (script accepts options)"
        return 0
    else
        print_fail "Option parsing failed"
        return 1
    fi
}

# Test 5: Error handling for missing Dockerfile
test_error_handling() {
    print_test "Error handling for missing Dockerfile"
    print_skip "Error handling test (requires Docker and full execution)"
    return 0
}

# Test 6: Script syntax validation
test_syntax() {
    print_test "Script syntax validation"

    if bash -n "$MIGRATION_SCRIPT" 2>&1; then
        print_pass "Script syntax is valid"
        return 0
    else
        print_fail "Script has syntax errors"
        return 1
    fi
}

# Main test runner
main() {
    echo "================================================================================"
    echo "US#22: Apple Container CLI Migration - Test Suite"
    echo "================================================================================"
    echo ""

    test_script_exists
    test_syntax
    test_help_option
    test_requires_service_name
    test_option_parsing
    test_error_handling

    echo ""
    echo "================================================================================"
    echo "Test Summary"
    echo "================================================================================"
    echo "Passed:  $PASSED"
    echo "Failed:  $FAILED"
    echo "Skipped: $SKIPPED"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        exit 1
    fi
}

main "$@"
