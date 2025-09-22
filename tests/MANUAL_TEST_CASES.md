# Manual Test Cases for mem0 System

## Prerequisites
1. Ensure mem0 server is running: `./manage.sh start`
2. Open Warp terminal or any terminal emulator
3. Navigate to mem0 project directory: `cd /Users/asrajag/Workspace/mem0`

## Test Suite 1: Basic Server Functionality

### Test 1.1: Server Health Check
```bash
# Test server is responding
curl -s http://localhost:13370/contexts
# Expected: JSON response with contexts array
```

### Test 1.2: Context Management
```bash
# Start a new context
./client/mem0 start test-manual-$(date +%s)

# Check active context
./client/mem0 active
# Expected: "Terminal context: test-manual-TIMESTAMP"

# List all contexts
./client/mem0 contexts
# Expected: List including your new context
```

### Test 1.3: Memory Storage and Recall
```bash
# Store a memory via API
curl -X POST http://localhost:13370/memory \
  -H "Content-Type: application/json" \
  -d '{
    "type": "manual_test",
    "source": "terminal",
    "data": {
      "message": "Manual test memory",
      "timestamp": "'$(date -Iseconds)'",
      "context": "test-manual-'$(date +%s)'"
    }
  }'
# Expected: {"message":"Memory entry recorded.","id":NUMBER}

# Recall memories
./client/mem0 recall --context test-manual-TIMESTAMP
# Expected: Your stored memory displayed
```

## Test Suite 2: Shell Integration

### Test 2.1: Shell Hook Setup
```bash
# Load shell integration
source client/mem0.zsh

# Enable debug mode
export MEM0_DEBUG=1

# Check if hooks are loaded
echo $preexec_functions | grep mem0_preexec
# Expected: Should show mem0_preexec function
```

### Test 2.2: Command Capture
```bash
# Start a context for shell testing
./client/mem0 start shell-test-$(date +%s)

# Run some test commands (one at a time, not pasted)
date
whoami
echo "test command capture"
ls -la

# Check captured commands
./client/mem0 recall --context shell-test-TIMESTAMP
# Expected: Should show captured command executions
```

## Test Suite 3: PostgreSQL Integration

### Test 3.1: Database Connection
```bash
# Test PostgreSQL connectivity
/opt/homebrew/bin/psql postgresql://mem0user:mem0pass@localhost:5432/mem0db -c "\dt"
# Expected: List of mem0 tables (memories, users, contexts, etc.)
```

### Test 3.2: Data Persistence
```bash
# Store memory
./client/mem0 start postgres-test-$(date +%s)
curl -X POST http://localhost:13370/memory \
  -H "Content-Type: application/json" \
  -d '{
    "type": "persistence_test",
    "source": "manual",
    "data": {"test": "PostgreSQL persistence", "context": "postgres-test-'$(date +%s)'"}
  }'

# Restart server
./manage.sh stop
./manage.sh start

# Verify data persisted
./client/mem0 recall --context postgres-test-TIMESTAMP
# Expected: Memory should still be there after restart
```

## Test Suite 4: Multi-User Features

### Test 4.1: User Registration
```bash
# Register a new user
curl -X POST http://localhost:13370/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'
# Expected: JWT token response
```

### Test 4.2: User Authentication
```bash
# Login user
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
# Expected: JWT token response

# Use token to access protected endpoint
TOKEN="YOUR_JWT_TOKEN_HERE"
curl -H "Authorization: Bearer $TOKEN" http://localhost:13370/auth/me
# Expected: User information
```

## Test Suite 5: Performance and Load

### Test 5.1: Bulk Memory Storage
```bash
# Store multiple memories rapidly
for i in {1..10}; do
  curl -X POST http://localhost:13370/memory \
    -H "Content-Type: application/json" \
    -d '{
      "type": "load_test",
      "source": "bulk",
      "data": {"iteration": '$i', "context": "load-test"}
    }' &
done
wait

# Verify all stored
./client/mem0 recall --context load-test | grep -c "load_test"
# Expected: Should show 10 entries
```

### Test 5.2: Context Switching
```bash
# Create multiple contexts and switch between them
./client/mem0 start context-a
echo "In context A"
./client/mem0 start context-b
echo "In context B"
./client/mem0 start context-c
echo "In context C"

# Check each context has its memories
./client/mem0 recall --context context-a
./client/mem0 recall --context context-b
./client/mem0 recall --context context-c
```

## Test Suite 6: Error Handling

### Test 6.1: Invalid Requests
```bash
# Test malformed JSON
curl -X POST http://localhost:13370/memory \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'
# Expected: Error response

# Test missing fields
curl -X POST http://localhost:13370/memory \
  -H "Content-Type: application/json" \
  -d '{"type": "test"}'
# Expected: Validation error
```

### Test 6.2: Non-existent Context
```bash
# Try to recall from non-existent context
./client/mem0 recall --context non-existent-context
# Expected: Empty or appropriate error message
```

## Test Suite 7: CLI Command Coverage

### Test 7.1: All CLI Commands
```bash
# Test all available commands
./client/mem0 contexts
./client/mem0 active
./client/mem0 start test-cli-$(date +%s)
./client/mem0 stop
./client/mem0 recall --context test-cli-TIMESTAMP
./client/mem0 delete test-cli-TIMESTAMP
```

## Expected Results Summary

✅ **Pass Criteria:**
- All API endpoints respond correctly
- Memories persist across server restarts
- Shell integration captures commands
- Multi-user authentication works
- Context isolation functions properly
- PostgreSQL stores and retrieves data correctly

❌ **Failure Indicators:**
- Server returns 500 errors
- Memories disappear after restart
- Shell commands not captured
- Authentication fails
- Cross-context data leakage
- Database connection errors

## Troubleshooting

If tests fail:
1. Check server logs for errors
2. Verify PostgreSQL is running: `brew services list | grep postgresql`
3. Check database connectivity: `psql postgresql://mem0user:mem0pass@localhost:5432/mem0db`
4. Ensure all dependencies installed
5. Verify shell integration loaded: `echo $preexec_functions`
