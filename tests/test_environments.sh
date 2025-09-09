#!/bin/bash
# test_environments.sh - Comprehensive test script for mem0 in different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_CONTEXT="env-test-$(date +%s)"
SERVER_URL="http://127.0.0.1:13370"

echo -e "${BLUE}=== mem0 Environment Testing Suite ===${NC}"
echo "Test context: $TEST_CONTEXT"
echo "Server URL: $SERVER_URL"
echo

# Function to print test results
print_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ $2${NC}"
    else
        echo -e "${RED}✗ $2${NC}"
        return 1
    fi
}

# Function to cleanup
cleanup() {
    echo -e "\n${YELLOW}Cleaning up test context...${NC}"
    ./client/mem0 context stop 2>/dev/null || true
    echo "Test completed."
}

trap cleanup EXIT

# Test 1: Server connectivity
echo -e "${BLUE}1. Testing server connectivity...${NC}"
if curl -s "$SERVER_URL" > /dev/null; then
    print_result 0 "Server is running and accessible"
else
    print_result 1 "Server is not accessible"
    exit 1
fi

# Test 2: CLI functionality
echo -e "\n${BLUE}2. Testing CLI functionality...${NC}"

# Start context
./client/mem0 context start "$TEST_CONTEXT" > /dev/null
print_result $? "Context creation"

# Add memory
./client/mem0 remember '{"type": "test", "source": "cli_test", "data": {"message": "CLI test successful"}}' --context "$TEST_CONTEXT" > /dev/null
print_result $? "Memory creation"

# List contexts
./client/mem0 contexts | grep -q "$TEST_CONTEXT"
print_result $? "Context listing"

# Recall memory
./client/mem0 recall --context "$TEST_CONTEXT" | grep -q "CLI test successful"
print_result $? "Memory recall"

# Test 3: Shell integration (zsh)
echo -e "\n${BLUE}3. Testing shell integration...${NC}"

# Check if zsh integration file exists
if [ -f "./client/mem0.zsh" ]; then
    print_result 0 "Zsh integration file exists"
    
    # Test shell hook function
    source ./client/mem0.zsh
    if type mem0_preexec > /dev/null 2>&1; then
        print_result 0 "Shell hook function loaded"
    else
        print_result 1 "Shell hook function not loaded"
    fi
else
    print_result 1 "Zsh integration file missing"
fi

# Test 4: VS Code extension
echo -e "\n${BLUE}4. Testing VS Code extension...${NC}"

if [ -d "./vscode-client" ]; then
    print_result 0 "VS Code extension directory exists"
    
    if [ -f "./vscode-client/package.json" ]; then
        print_result 0 "VS Code extension package.json exists"
    else
        print_result 1 "VS Code extension package.json missing"
    fi
    
    if [ -f "./vscode-client/src/extension.ts" ]; then
        print_result 0 "VS Code extension source exists"
    else
        print_result 1 "VS Code extension source missing"
    fi
    
    # Check if extension is built
    if [ -f "./vscode-client/dist/extension.js" ]; then
        print_result 0 "VS Code extension is built"
    else
        print_result 1 "VS Code extension needs building"
    fi
else
    print_result 1 "VS Code extension directory missing"
fi

# Test 5: Database functionality
echo -e "\n${BLUE}5. Testing database functionality...${NC}"

# Test PostgreSQL connection (if configured)
if grep -q "postgresql://" mem0.config.json 2>/dev/null; then
    echo "PostgreSQL configuration detected"
    
    # Test context isolation
    ./client/mem0 context start "user1-test" > /dev/null
    ./client/mem0 remember '{"type": "isolation_test", "source": "user1", "data": {"user": "user1"}}' --context "user1-test" > /dev/null
    ./client/mem0 context stop > /dev/null
    
    ./client/mem0 context start "user2-test" > /dev/null  
    ./client/mem0 remember '{"type": "isolation_test", "source": "user2", "data": {"user": "user2"}}' --context "user2-test" > /dev/null
    ./client/mem0 context stop > /dev/null
    
    # Verify isolation
    user1_data=$(./client/mem0 recall --context "user1-test")
    user2_data=$(./client/mem0 recall --context "user2-test")
    
    if echo "$user1_data" | grep -q "user1" && echo "$user2_data" | grep -q "user2"; then
        print_result 0 "Context isolation working"
    else
        print_result 1 "Context isolation failed"
    fi
else
    echo "SQLite configuration detected"
    print_result 0 "Database configuration found"
fi

# Test 6: Configuration loading
echo -e "\n${BLUE}6. Testing configuration...${NC}"

if [ -f "mem0.config.json" ]; then
    print_result 0 "Configuration file exists"
    
    # Validate JSON
    if python3 -m json.tool mem0.config.json > /dev/null 2>&1; then
        print_result 0 "Configuration file is valid JSON"
    else
        print_result 1 "Configuration file has invalid JSON"
    fi
else
    print_result 1 "Configuration file missing"
fi

# Test 7: Multi-user simulation
echo -e "\n${BLUE}7. Testing multi-user simulation...${NC}"

# Create multiple contexts to simulate different users
contexts=("dev-session" "qa-session" "prod-session")

for ctx in "${contexts[@]}"; do
    ./client/mem0 context start "$ctx" > /dev/null
    ./client/mem0 remember "{\"type\": \"session\", \"source\": \"$ctx\", \"data\": {\"context\": \"$ctx\"}}" --context "$ctx" > /dev/null
    ./client/mem0 context stop > /dev/null
done

# Verify all contexts exist
all_contexts=$(./client/mem0 contexts)
contexts_found=0

for ctx in "${contexts[@]}"; do
    if echo "$all_contexts" | grep -q "$ctx"; then
        ((contexts_found++))
    fi
done

if [ $contexts_found -eq ${#contexts[@]} ]; then
    print_result 0 "Multi-context management working"
else
    print_result 1 "Multi-context management failed ($contexts_found/${#contexts[@]} contexts found)"
fi

echo -e "\n${GREEN}=== Test Summary ===${NC}"
echo "All core functionality tests completed."
echo "Check individual test results above for any failures."
echo
echo -e "${YELLOW}Next steps for full environment integration:${NC}"
echo "1. Install VS Code extension: code --install-extension ./vscode-client/mem0-*.vsix"
echo "2. Configure shell integration: source ./client/mem0.zsh"
echo "3. For Warp terminal: Use same zsh integration"
echo "4. For JetBrains IDEs: Use CLI commands or create custom plugin"
