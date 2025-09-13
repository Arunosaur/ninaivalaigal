#!/bin/bash

# test-shell-integration.sh - Comprehensive shell integration test script
# This script validates that mem0 shell integration is working correctly

set -e

echo "🧪 mem0 Shell Integration Test Suite"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
TEST_CONTEXT="shell-test-$(date +%s)"
MEM0_DIR="$HOME/Workspace/mem0"
CLIENT_PATH="$MEM0_DIR/client/mem0"

# Helper functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

cleanup() {
    echo ""
    echo "🧹 Cleaning up test context..."
    $CLIENT_PATH delete --context "$TEST_CONTEXT" 2>/dev/null || true
}

# Set up cleanup trap
trap cleanup EXIT

# Environment setup
export NINAIVALAIGAL_DEBUG=1
export NINAIVALAIGAL_USER_ID=test-user
export NINAIVALAIGAL_SERVER_URL=http://localhost:13370

echo ""
echo "📋 Pre-flight checks..."
echo "Testing with NINAIVALAIGAL_DEBUG=$NINAIVALAIGAL_DEBUG"
echo "NINAIVALAIGAL_USER_ID: $NINAIVALAIGAL_USER_ID"
echo "NINAIVALAIGAL_SERVER_URL: $NINAIVALAIGAL_SERVER_URL"

# Check if mem0 directory exists
if [ ! -d "$MEM0_DIR" ]; then
    log_error "mem0 directory not found at $MEM0_DIR"
    exit 1
fi
log_info "mem0 directory found"

# Check if client exists
if [[ ! -f "$CLIENT_PATH" ]]; then
    log_error "mem0 client not found at $CLIENT_PATH"
    exit 1
fi
log_info "mem0 client found"

# Check if shell integration exists
if [[ ! -f "$MEM0_DIR/client/mem0.zsh" ]]; then
    log_error "Shell integration not found at $MEM0_DIR/client/mem0.zsh"
    exit 1
fi
log_info "Shell integration file found"

# Check environment variables
if [ -z "$NINAIVALAIGAL_USER_ID" ]; then
    log_error "NINAIVALAIGAL_USER_ID not set"
    exit 1
fi

if [ -z "$NINAIVALAIGAL_SERVER_URL" ]; then
    log_error "NINAIVALAIGAL_SERVER_URL not set"
    exit 1
fi

# Check if server is running
if ! curl -s "$NINAIVALAIGAL_SERVER_URL/health" >/dev/null; then
    log_error "Server not responding at $NINAIVALAIGAL_SERVER_URL"
    exit 1
fi
log_info "Server responding at $NINAIVALAIGAL_SERVER_URL"

echo ""
echo "🚀 Starting shell integration tests..."

# Test 1: Create test context
echo ""
echo "Test 1: Creating test context..."
if $CLIENT_PATH start --context "$TEST_CONTEXT" &>/dev/null; then
    log_info "Test context '$TEST_CONTEXT' created successfully"
else
    log_error "Failed to create test context"
    exit 1
fi

# Test 2: Verify context is active
echo ""
echo "Test 2: Verifying context is active..."
ACTIVE_OUTPUT=$($CLIENT_PATH active 2>/dev/null)
if echo "$ACTIVE_OUTPUT" | grep -q "$TEST_CONTEXT"; then
    log_info "Test context is active"
else
    log_error "Test context is not active. Output: $ACTIVE_OUTPUT"
    exit 1
fi

# Test 3: Test direct remember command
echo ""
echo "Test 3: Testing direct remember command..."
TEST_PAYLOAD='{"type": "test_entry", "source": "test_script", "data": {"message": "Direct test from script", "timestamp": "'$(date -Iseconds)'"}}'
if $CLIENT_PATH remember "$TEST_PAYLOAD" --context "$TEST_CONTEXT" &>/dev/null; then
    log_info "Direct remember command works"
else
    log_error "Direct remember command failed"
    exit 1
fi

# Test 4: Verify memory was stored
echo ""
echo "Test 4: Verifying memory was stored..."
RECALL_OUTPUT=$($CLIENT_PATH recall --context "$TEST_CONTEXT" 2>/dev/null)
if echo "$RECALL_OUTPUT" | grep -q "test_entry"; then
    log_info "Memory was stored and recalled successfully"
else
    log_error "Memory was not stored properly. Output: $RECALL_OUTPUT"
    exit 1
fi

# Test 5: Shell integration syntax check
echo ""
echo "Test 5: Checking shell integration syntax..."
if zsh -n "$MEM0_DIR/client/mem0.zsh"; then
    log_info "Shell integration syntax is valid"
else
    log_error "Shell integration has syntax errors"
    exit 1
fi

# Test 6: Shell integration loading test
echo ""
echo "Test 6: Testing shell integration loading..."
LOAD_TEST=$(zsh -c "source $MEM0_DIR/client/mem0.zsh && type mem0_preexec" 2>&1)
if echo "$LOAD_TEST" | grep -q "shell function"; then
    log_info "Shell integration loads and defines functions correctly"
else
    log_error "Shell integration failed to load properly. Output: $LOAD_TEST"
    exit 1
fi

# Test 7: Context detection test
echo ""
echo "Test 7: Testing context detection..."
CONTEXT_TEST=$(zsh -c "
    source $MEM0_DIR/client/mem0.zsh
    mem0_get_active_context
" 2>&1)
if echo "$CONTEXT_TEST" | grep -q "$TEST_CONTEXT"; then
    log_info "Context detection works correctly"
else
    log_warn "Context detection may have issues. Output: $CONTEXT_TEST"
fi

echo ""
echo "🎉 Shell Integration Test Results"
echo "================================="
log_info "All critical tests passed!"
echo ""
echo "📝 Manual Testing Instructions:"
echo "1. In your terminal, run: source $MEM0_DIR/client/mem0.zsh"
echo "2. Enable debug: export NINAIVALAIGAL_DEBUG=1"
echo "3. Set context: export NINAIVALAIGAL_CONTEXT=$TEST_CONTEXT"
echo "4. Run test commands: date, whoami, echo 'test'"
echo "5. Check capture: $CLIENT_PATH recall --context $TEST_CONTEXT"
echo ""
echo "Expected debug output should show:"
echo "  [ninaivalaigal-debug] preexec hook triggered for command: <your_command>"
echo "  [ninaivalaigal-debug] using NINAIVALAIGAL_CONTEXT env var: '$TEST_CONTEXT'"
echo "  [ninaivalaigal-debug] command queued for capture: '<your_command>' in context '$TEST_CONTEXT'"
echo "  [ninaivalaigal-debug] precmd hook triggered, exit code: 0"
echo ""
log_info "Test context '$TEST_CONTEXT' will be cleaned up automatically"
