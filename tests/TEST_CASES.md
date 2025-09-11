# mem0 Test Cases by Environment

## Development Environment Test Cases

### Prerequisites
```bash
# Ensure PostgreSQL is running
docker ps | grep mem0-postgres
# Should show running container

# Ensure FastAPI server is running
./manage.sh start
# Should start server on port 13370
```

### Test Case 1: Authentication System
```bash
# Register a new user
./client/mem0 auth register --username testuser --password testpass --email test@example.com
# Expected: "Registration successful"

# Login with the user
./client/mem0 auth login --username testuser --password testpass
# Expected: "Login successful"

# Check user information
./client/mem0 auth me
# Expected: User details including username, email, ID

# Logout
./client/mem0 auth logout
# Expected: "Logged out successfully"
```

### Test Case 2: Organization Management
```bash
# Login first
./client/mem0 auth login --username testuser --password testpass

# Create organization
./client/mem0 org create --name "Test Corp" --description "Test Organization"
# Expected: Organization created successfully

# List organizations
./client/mem0 org list
# Expected: List including "Test Corp"
```

### Test Case 3: Team Management
```bash
# Create team within organization
./client/mem0 team create --name "Frontend Team" --org-id 1 --description "UI/UX Team"
# Expected: Team created successfully

# Add team member with role
./client/mem0 team add-member --team-id 1 --user-id 2 --role admin
# Expected: User added to team with role

# List team members
./client/mem0 team members --team-id 1
# Expected: List of team members with roles

# List user's teams
./client/mem0 team list
# Expected: List of teams user belongs to
```

### Test Case 4: Context Creation with Ownership
```bash
# Create personal context
./client/mem0 context-create --name "personal-project" --description "My personal project" --visibility private
# Expected: Context created with private visibility

# Create team-shared context
./client/mem0 context-create --name "team-project" --description "Team collaboration" --visibility team
# Expected: Context created with team visibility

# Create organization context
./client/mem0 context-create --name "company-knowledge" --description "Company docs" --visibility organization
# Expected: Context created with organization visibility
```

### Test Case 5: Context Sharing
```bash
# Share context with another user (read permission)
./client/mem0 share --context-id 1 --target-type user --target-id 2 --permission read
# Expected: Context shared successfully

# Share context with team (write permission)
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission write
# Expected: Context shared with team

# Share context with organization (admin permission)
./client/mem0 share --context-id 1 --target-type organization --target-id 1 --permission admin
# Expected: Context shared with organization
```

### Test Case 6: Permission-Based Access
```bash
# Switch to different user (user2)
./client/mem0 auth logout
./client/mem0 auth login --username user2 --password pass2

# Try to access personal context of user1 (should fail)
./client/mem0 recall --context personal-project
# Expected: Permission denied or context not found

# Try to access team-shared context (should succeed if user is team member)
./client/mem0 recall --context team-project
# Expected: Access granted if user has permission

# Try to access organization context (should succeed)
./client/mem0 recall --context company-knowledge
# Expected: Access granted
```

### Test Case 7: Multi-User Collaboration
```bash
# User1 creates and shares context
./client/mem0 auth login --username user1 --password pass1
./client/mem0 context-create --name "joint-project" --visibility team
./client/mem0 share --context-id 3 --target-type team --target-id 1 --permission write

# User2 accesses shared context
./client/mem0 auth login --username user2 --password pass2
./client/mem0 remember "User2 contribution" --context joint-project
# Expected: Memory stored successfully

# User1 sees User2's contribution
./client/mem0 auth login --username user1 --password pass1
./client/mem0 recall --context joint-project
# Expected: Both users' memories visible
```

### Test Case 8: Role-Based Permissions
```bash
# Admin user manages team permissions
./client/mem0 auth login --username admin --password adminpass
./client/mem0 team add-member --team-id 1 --user-id 3 --role viewer
# Expected: User added as viewer

# Viewer tries to write to context (should fail)
./client/mem0 auth login --username viewer --password viewerpass
./client/mem0 remember "Viewer contribution" --context team-project
# Expected: Permission denied

# Member tries to write (should succeed)
./client/mem0 auth login --username member --password memberpass
./client/mem0 remember "Member contribution" --context team-project
# Expected: Memory stored successfully
```

### Test Case 9: Cross-Organization Teams
```bash
# Create cross-organization team
./client/mem0 team create --name "Cross-Org Project" --description "Joint venture team"
# Expected: Team created without org association

# Add members from different organizations
./client/mem0 team add-member --team-id 2 --user-id 4 --role member  # Org A user
./client/mem0 team add-member --team-id 2 --user-id 5 --role member  # Org B user

# Share context with cross-org team
./client/mem0 share --context-id 4 --target-type team --target-id 2 --permission write
# Expected: Context shared successfully
```

### Test Case 10: Context Ownership Transfer
```bash
# Owner transfers context to team
./client/mem0 auth login --username owner --password ownerpass
./client/mem0 context-create --name "transfer-test" --visibility private
# Context owned by user

# Transfer ownership to team (conceptual - would need API enhancement)
# ./client/mem0 context transfer --context-id 5 --new-owner team:1
# Expected: Context ownership transferred to team
```

## Advanced Test Scenarios

### Scenario 1: Enterprise Knowledge Management
```bash
# Company admin creates knowledge base
./client/mem0 auth login --username companyadmin --password adminpass
./client/mem0 context-create --name "company-wiki" --visibility organization

# Department heads create specialized contexts
./client/mem0 context-create --name "engineering-standards" --visibility team
./client/mem0 context-create --name "product-roadmap" --visibility organization

# Employees access appropriate contexts based on permissions
./client/mem0 auth login --username engineer --password engpass
./client/mem0 recall --context engineering-standards  # Access granted
./client/mem0 recall --context product-roadmap     # Access granted
```

### Scenario 2: Open Source Project Collaboration
```bash
# Project maintainer creates public context
./client/mem0 context-create --name "open-source-docs" --visibility public

# Contributors access and contribute
./client/mem0 auth login --username contributor --password contribpass
./client/mem0 remember "Documentation improvement" --context open-source-docs

# Maintainers have admin access
./client/mem0 auth login --username maintainer --password maintpass
./client/mem0 share --context-id 6 --target-type user --target-id 6 --permission admin
```

### Scenario 3: Multi-Project Developer Workflow
```bash
# Developer belongs to multiple teams
./client/mem0 auth login --username developer --password devpass
./client/mem0 team list
# Expected: Shows all teams developer belongs to

# Switch between project contexts
./client/mem0 context start project-alpha
./client/mem0 remember "Working on alpha feature" --context project-alpha

./client/mem0 context start project-beta
./client/mem0 remember "Working on beta feature" --context project-beta

# Access organization-wide resources
./client/mem0 recall --context company-knowledge
```

## Error Handling Tests

### Test Case 1: Authentication Errors
```bash
# Wrong password
./client/mem0 auth login --username user1 --password wrongpass
# Expected: Login failed error

# Non-existent user
./client/mem0 auth login --username nonexistent --password pass
# Expected: Login failed error
```

### Test Case 2: Permission Errors
```bash
# User tries to access private context
./client/mem0 recall --context private-context
# Expected: Permission denied or not found

# User tries to share context they don't own
./client/mem0 share --context-id 10 --target-type user --target-id 2 --permission read
# Expected: Permission denied error
```

### Test Case 3: Invalid Operations
```bash
# Try to add user to non-existent team
./client/mem0 team add-member --team-id 999 --user-id 1 --role member
# Expected: Team not found error

# Try to share non-existent context
./client/mem0 share --context-id 999 --target-type user --target-id 1 --permission read
# Expected: Context not found error
```

## Performance Tests

### Test Case 1: Large Team Operations
```bash
# Add multiple users to team
for i in {1..50}; do
  ./client/mem0 team add-member --team-id 1 --user-id $i --role member
done
# Expected: All operations complete successfully

# Test context access for all team members
for i in {1..50}; do
  ./client/mem0 auth login --username user$i --password pass$i
  ./client/mem0 recall --context team-context
done
# Expected: All users can access team context
```

### Test Case 2: Concurrent Sharing Operations
```bash
# Multiple users sharing contexts simultaneously
./client/mem0 auth login --username user1 --password pass1
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission write &

./client/mem0 auth login --username user2 --password pass2
./client/mem0 share --context-id 2 --target-type team --target-id 1 --permission read &

wait
# Expected: All sharing operations complete successfully
```

## Security Tests

### Test Case 1: Data Isolation
```bash
# User1 creates private context
./client/mem0 auth login --username user1 --password pass1
./client/mem0 context-create --name "user1-private" --visibility private
./client/mem0 remember "Secret data" --context user1-private

# User2 tries to access User1's private context
./client/mem0 auth login --username user2 --password pass2
./client/mem0 recall --context user1-private
# Expected: No access - context not found or permission denied

# Verify User1 can still access their data
./client/mem0 auth login --username user1 --password pass1
./client/mem0 recall --context user1-private
# Expected: User1's data accessible
```

### Test Case 2: Token Security
```bash
# Login and get token
./client/mem0 auth login --username user1 --password pass1

# Try to use API directly with invalid token
curl -H "Authorization: Bearer invalid-token" http://127.0.0.1:13370/contexts
# Expected: 401 Unauthorized

# Try to access another user's data
curl -H "Authorization: Bearer $(cat ~/.mem0/auth.json | jq -r .token)" \
  http://127.0.0.1:13370/memory?context=user2-private
# Expected: No data returned or permission denied
```

## Integration Tests

### Test Case 1: Full Workflow
```bash
# 1. User registration and login
./client/mem0 auth register --username testuser --password testpass
./client/mem0 auth login --username testuser --password testpass

# 2. Organization and team setup
./client/mem0 org create --name "Test Org"
./client/mem0 team create --name "Test Team" --org-id 1

# 3. Context creation and sharing
./client/mem0 context-create --name "test-context" --visibility team
./client/mem0 share --context-id 1 --target-type team --target-id 1 --permission write

# 4. Collaboration workflow
./client/mem0 remember "Test memory" --context test-context
./client/mem0 recall --context test-context

# 5. Clean up
./client/mem0 auth logout
# Expected: Complete workflow executes successfully
```

### Test Case 2: VS Code Integration
```bash
# With VS Code extension running
# @mem0 context start vscode-test
# @mem0 remember "VS Code integration test"
# @mem0 recall --context vscode-test
# Expected: VS Code extension works with authentication and sharing
```

## Monitoring and Health Checks

### Test Case 1: System Health
```bash
# Check server health
curl http://127.0.0.1:13370/
# Expected: Server running response

# Check authentication health
curl -H "Authorization: Bearer $(cat ~/.mem0/auth.json | jq -r .token)" \
  http://127.0.0.1:13370/auth/me
# Expected: User information returned

# Check database connectivity
./client/mem0 contexts
# Expected: Contexts listed without errors
```

### Test Case 2: Load Testing
```bash
# Simulate multiple users
for i in {1..10}; do
  ./client/mem0 auth register --username "loadtest$i" --password "pass$i"
  ./client/mem0 auth login --username "loadtest$i" --password "pass$i"
  ./client/mem0 context-create --name "load-context-$i" --visibility private
  ./client/mem0 remember "Load test memory $i" --context "load-context-$i"
done
# Expected: All operations complete successfully under load
```

### Test Case 2: Shell Integration
```bash
# Source shell integration
source client/mem0.zsh

# Start recording
mem0_on shell-test-$(date +%s)
# Expected: Context started message

# Execute some commands (these should be captured)
echo "Testing shell integration"
ls -la
git status

# Stop recording
mem0_off
# Expected: Recording stopped message

# Verify capture
./client/mem0 recall --context shell-test-$(date +%s)
# Expected: Should show captured commands
```

### Test Case 3: MCP Server Functionality
```bash
# Test MCP server
cd server && python test_mcp.py
# Expected: All tests pass with "MCP server tools test completed!"

# Test MCP server startup
cd server && python run_mcp_server.py &
MCP_PID=$!
sleep 2
kill $MCP_PID
# Expected: No errors, clean startup/shutdown
```

### Test Case 4: Database Operations
```bash
# Test database connectivity
cd server && python -c "
from database import DatabaseManager
from main import load_config
db = DatabaseManager(load_config())
session = db.get_session()
print('Database connected successfully')
session.close()
"
# Expected: "Database connected successfully"

# Test cross-platform test suite
python tests/test_cross_platform.py
# Expected: All tests pass
```

---

## Docker Environment Test Cases

### Prerequisites
```bash
# Ensure Docker is available
docker --version
# Should show Docker version

# Check PostgreSQL container
docker ps | grep mem0-postgres
# Should show running PostgreSQL container
```

### Test Case 1: Container Health Check
```bash
# Test PostgreSQL container health
docker exec mem0-postgres pg_isready -U mem0user -d mem0db
# Expected: "accepting connections"

# Test database connection from host
docker exec mem0-postgres psql -U mem0user -d mem0db -c "SELECT version();"
# Expected: PostgreSQL version information
```

### Test Case 2: Docker Compose Deployment
```bash
# Navigate to deploy directory
cd deploy

# Test Docker Compose configuration
docker compose config
# Expected: Valid YAML configuration output

# Start services (if testing full deployment)
docker compose up -d
# Expected: Services start successfully

# Check service health
docker compose ps
# Expected: All services running

# Test FastAPI through Docker
curl -X GET "http://localhost:13370/contexts"
# Expected: JSON response with contexts

# Cleanup
docker compose down
```

### Test Case 3: Container Networking
```bash
# Test container-to-container communication
docker exec mem0-postgres ping -c 1 localhost
# Expected: Successful ping

# Test port accessibility
docker port mem0-postgres
# Expected: 5432/tcp -> 0.0.0.0:5432
```

---

## Production/VM Environment Test Cases

### Prerequisites
```bash
# Ensure Ansible is available (if testing deployment)
ansible --version
# Should show Ansible version

# Ensure target VM is accessible
ping your-vm-ip
# Should respond successfully
```

### Test Case 1: Ansible Deployment (Dry Run)
```bash
# Test Ansible playbook syntax
ansible-playbook --syntax-check deploy/mem0-complete-deployment.yml
# Expected: "playbook: deploy/mem0-complete-deployment.yml"

# Test Ansible connectivity to target
ansible mem0_servers -m ping -i your-inventory
# Expected: "pong" response from target servers

# Dry run deployment
ansible-playbook deploy/mem0-complete-deployment.yml -i your-inventory --check
# Expected: Shows what would be changed without making changes
```

### Test Case 2: Production Service Validation
```bash
# After deployment, test service status
ssh your-vm "sudo systemctl status supervisor"
# Expected: Active (running)

ssh your-vm "sudo systemctl status nginx"
# Expected: Active (running)

ssh your-vm "sudo systemctl status postgresql"
# Expected: Active (running)
```

### Test Case 3: Production API Testing
```bash
# Test FastAPI endpoint through nginx
curl -X GET "http://your-vm-ip/contexts"
# Expected: JSON response with contexts

# Test health endpoint
curl -X GET "http://your-vm-ip/health"
# Expected: Health status response

# Test memory operations
curl -X POST "http://your-vm-ip/memory" \
  -H "Content-Type: application/json" \
  -d '{"context": "prod-test", "payload": {"type": "note", "source": "test", "data": {"text": "Production test"}}}'
# Expected: Success response
```

### Test Case 4: Production MCP Server
```bash
# Test MCP server on production
ssh your-vm "cd /opt/mem0 && /opt/mem0/venv/bin/python server/test_mcp.py"
# Expected: All MCP tests pass

# Test MCP client configuration
ssh your-vm "cat /opt/mem0/config/mcp-client-config.json"
# Expected: Valid MCP configuration with correct paths
```

---

## Team Deployment Test Cases

### Test Case 1: Multi-User Context Isolation
```bash
# Create contexts for different users/teams
./client/mem0 context start team-alpha-project
./client/mem0 context start team-beta-project

# Add memories to different contexts
./client/mem0 remember "Alpha team working on frontend" --context team-alpha-project
./client/mem0 remember "Beta team working on backend" --context team-beta-project

# Verify isolation
./client/mem0 recall --context team-alpha-project
# Expected: Only alpha team memories

./client/mem0 recall --context team-beta-project
# Expected: Only beta team memories
```

### Test Case 2: Concurrent Usage Simulation
```bash
# Terminal 1 - Team Alpha
export MEM0_CONTEXT=team-alpha-project
source client/mem0.zsh
mem0_on team-alpha-project
echo "Alpha team task 1"
echo "Alpha team task 2"

# Terminal 2 - Team Beta (run simultaneously)
export MEM0_CONTEXT=team-beta-project
source client/mem0.zsh
mem0_on team-beta-project
echo "Beta team task 1"
echo "Beta team task 2"

# Verify separate capture
./client/mem0 recall --context team-alpha-project | grep "Alpha"
./client/mem0 recall --context team-beta-project | grep "Beta"
# Expected: Each context only contains its team's activities
```

### Test Case 3: Load Testing
```bash
# Create multiple contexts rapidly
for i in {1..10}; do
  ./client/mem0 context start load-test-$i &
done
wait

# Add memories concurrently
for i in {1..10}; do
  ./client/mem0 remember "Load test memory $i" --context load-test-$i &
done
wait

# Verify all contexts exist
./client/mem0 contexts | grep "load-test"
# Expected: All 10 contexts listed
```

---

## VS Code Extension Test Cases

### Test Case 1: Extension Activation
```bash
# Open VS Code in mem0 project
code /Users/asrajag/Workspace/mem0

# Check extension activation (in VS Code)
# Expected: Popup notifications showing extension activation
```

### Test Case 2: Chat Participant Testing
```bash
# In VS Code chat panel, test commands:
@mem0 context start vscode-test-project
# Expected: Context creation confirmation

@mem0 remember "Testing VS Code integration"
# Expected: Memory storage confirmation

@mem0 recall --context vscode-test-project
# Expected: Memory recall with debug output
```

---

## Performance Test Cases

### Test Case 1: Response Time Testing
```bash
# Test FastAPI response times
time curl -X GET "http://127.0.0.1:13370/contexts"
# Expected: Response in < 1 second

# Test CLI response times
time ./client/mem0 contexts
# Expected: Response in < 2 seconds

# Test MCP server response times
time (cd server && python -c "
import asyncio
from mcp_server import list_contexts
print(asyncio.run(list_contexts()))
")
# Expected: Response in < 1 second
```

### Test Case 2: Memory Stress Testing
```bash
# Create large number of memories
for i in {1..100}; do
  ./client/mem0 remember "Stress test memory $i" --context stress-test
done

# Test recall performance
time ./client/mem0 recall --context stress-test
# Expected: Response in < 5 seconds even with 100 memories
```

---

## Troubleshooting Test Cases

### Test Case 1: Service Recovery
```bash
# Stop FastAPI server
./manage.sh stop

# Try CLI operations (should fail gracefully)
./client/mem0 contexts
# Expected: Connection error with helpful message

# Restart server
./manage.sh start

# Verify recovery
./client/mem0 contexts
# Expected: Normal operation resumed
```

### Test Case 2: Database Connection Issues
```bash
# Stop PostgreSQL container
docker stop mem0-postgres

# Test fallback behavior
./client/mem0 contexts
# Expected: Should handle gracefully or fall back to SQLite

# Restart PostgreSQL
docker start mem0-postgres

# Verify reconnection
./client/mem0 contexts
# Expected: Normal operation with PostgreSQL
```

---

## Quick Validation Commands

### One-Line Environment Checks
```bash
# Development environment check
python tests/quick_test_environments.py

# Database connectivity check
cd server && python -c "from database import DatabaseManager; from main import load_config; DatabaseManager(load_config()).get_session().close(); print('✅ Database OK')"

# FastAPI health check
curl -s http://127.0.0.1:13370/contexts > /dev/null && echo "✅ FastAPI OK" || echo "❌ FastAPI Failed"

# MCP server check
cd server && timeout 10s python test_mcp.py > /dev/null && echo "✅ MCP OK" || echo "❌ MCP Failed"

# Shell integration check
source client/mem0.zsh && echo "✅ Shell Integration OK" || echo "❌ Shell Integration Failed"
```
