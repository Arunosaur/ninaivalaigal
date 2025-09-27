# IDE-Agnostic MCP Testing Guide for Multi-Level Memory

This guide covers testing the complete hierarchical memory system across different IDEs using MCP protocol.

## Prerequisites

1. **PostgreSQL Database Updated:**
```bash
psql -d mem0_db -f scripts/update_schema_approval.sql
```

2. **MCP Server Running:**
```bash
cd /Users/asrajag/Workspace/mem0/server
python mcp_server.py
```

3. **FastAPI Server Running (for CLI/web):**
```bash
cd /Users/asrajag/Workspace/mem0/server
python main.py
```

## IDE Configuration

### Windsurf IDE
**File:** `.vscode/mcp.json`
```json
{
  "servers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "type": "stdio"
    }
  }
}
```

### VS Code
**File:** `.vscode/settings.json` or global settings
```json
{
  "mcp": {
    "servers": {
      "mem0": {
        "command": "/opt/homebrew/anaconda3/bin/python",
        "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
        "type": "stdio"
      }
    }
  }
}
```

### Claude Desktop
**File:** `~/.config/claude-desktop/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"]
    }
  }
}
```

### Zed Editor
**File:** `~/.config/zed/settings.json`
```json
{
  "language_models": {
    "mcp_servers": {
      "mem0": {
        "command": "/opt/homebrew/anaconda3/bin/python",
        "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
        "type": "stdio"
      }
    }
  }
}
```

## Testing Multi-Level Memory Architecture

### 1. Personal Memory Testing
```
# Start personal context
@mem0 context_start personal-coding-session

# Store personal memories
@mem0 remember "I prefer using TypeScript interfaces over types for better readability"
@mem0 remember "My coding style: always use async/await instead of .then() chains"
@mem0 remember "Personal preference: 2-space indentation for JavaScript/TypeScript"

# Recall personal memories
@mem0 recall
```

### 2. Team Memory Testing
```
# Start team context (requires team setup via FastAPI)
@mem0 context_start team-frontend-standards

# Store team-level memories
@mem0 remember "Team standard: Use React hooks pattern, avoid class components"
@mem0 remember "Team decision: Tailwind CSS for styling, no custom CSS files"
@mem0 remember "Team workflow: All PRs require 2 approvals before merge"

# List team contexts
@mem0 list_contexts
```

### 3. Cross-Team Memory Testing (NEW!)
```
# Request access to another team's context
@mem0 request_cross_team_access context_id=5 target_team_id=3 permission_level="read" justification="Need backend API patterns for frontend integration"

# Check pending approval requests
@mem0 list_pending_approvals

# Approve a request (as team admin)
@mem0 approve_cross_team_request request_id=1 action="approve" reason="Approved for Q4 integration project"

# Reject a request (as team admin)
@mem0 approve_cross_team_request request_id=2 action="reject" reason="Sensitive internal patterns, use public documentation instead"
```

### 4. Organizational Memory Testing
```
# Access organizational-wide memories
@mem0 context_start org-coding-standards

# Store org-level memories (accessible by all teams)
@mem0 remember "Organization standard: All APIs must follow REST conventions"
@mem0 remember "Security policy: Never commit API keys, use environment variables"
@mem0 remember "Code review policy: Security-sensitive changes require security team review"
```

## AI Alignment Testing

### Test AI Knowledge Continuity
1. **Store Context in One IDE:**
```
# In VS Code
@mem0 remember "Working on user authentication module using JWT token  # pragma: allowlist secrets"
@mem0 remember "Current issue: Token refresh logic needs optimization"
```

2. **Access Same Context in Different IDE:**
```
# In Windsurf
@mem0 recall
# Should return the JWT and token  # pragma: allowlist secret refresh memories
```

3. **Cross-Team Knowledge Sharing:**
```
# Backend team shares API patterns
@mem0 remember "API Response Format: {success: boolean, data: any, error?: string}"

# Frontend team requests access
@mem0 request_cross_team_access context_id=10 target_team_id=2 permission_level="read" justification="Need consistent API response handling"

# After approval, frontend team can access
@mem0 recall
```

## Expected Behaviors

### ✅ Success Indicators:
- **Personal memories** only visible to individual user
- **Team memories** accessible by all team members
- **Cross-team requests** require approval workflow
- **Organizational memories** visible to all organization members
- **Context switching** works across different IDEs
- **AI alignment** maintained across IDE switches

### ❌ Failure Indicators:
- Personal memories visible to other users
- Team memories accessible without team membership
- Cross-team access granted without approval
- MCP connection errors in any IDE
- Context loss when switching IDEs

## Troubleshooting

### MCP Connection Issues
```bash
# Check MCP server logs
python /Users/asrajag/Workspace/mem0/server/mcp_server.py

# Verify database connection
psql -d mem0_db -c "SELECT COUNT(*) FROM users;"
```

### Permission Issues
```bash
# Check user team memberships via FastAPI
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:13370/users/me/teams

# Check context permissions
curl -H "Authorization: Bearer YOUR_JWT" http://localhost:13370/users/me/contexts
```

### Database Issues
```bash
# Verify approval workflow table exists
psql -d mem0_db -c "\d cross_team_approval_requests"

# Check pending requests
psql -d mem0_db -c "SELECT * FROM cross_team_approval_requests WHERE status = 'pending';"
```

## Team Collaboration Scenarios

### Scenario 1: Frontend-Backend Collaboration
1. Backend team creates API documentation context
2. Frontend team requests read access
3. Backend team approves request
4. Both teams can now reference shared API patterns in their IDEs

### Scenario 2: Security Review Process
1. Development team creates security-sensitive context
2. Security team gets automatic read access (organizational level)
3. Security team provides feedback via shared context
4. All teams learn from security patterns

### Scenario 3: Cross-Project Knowledge Transfer
1. Project A team documents lessons learned
2. Project B team requests access to specific contexts
3. Approval workflow ensures controlled knowledge sharing
4. Organization builds institutional knowledge base

## Performance Testing

### Load Testing Commands
```bash
# Test concurrent MCP connections
for i in {1..10}; do
  echo "@mem0 remember 'Load test memory $i'" | python test_mcp_client.py &
done

# Test approval workflow performance
curl -X POST "http://localhost:13370/cross-team-request" \
  -H "Authorization: Bearer $JWT" \
  -d '{"context_id": 1, "target_team_id": 2, "permission_level": "read"}' &
```

This guide ensures your multi-level memory architecture works seamlessly across all IDEs while maintaining proper security boundaries and approval workflows.
