# IDE Testing Quickstart - Universal AI Integration

**Version:** 1.0.0  
**Date:** 2025-09-12  
**Status:** Ready for Testing  

## Prerequisites ✅

All documentation is now version controlled and committed. The universal AI integration system is ready for IDE testing.

## Quick Setup (5 minutes)

### 1. Start mem0 Servers
```bash
# Terminal 1: Start MCP Server
cd /Users/asrajag/Workspace/mem0/server
python mcp_server.py

# Terminal 2: Start FastAPI Server (for CLI)
python main.py
```

### 2. Verify Database Schema
```bash
# Apply latest schema updates
psql -d mem0_db -f /Users/asrajag/Workspace/mem0/scripts/update_schema_approval.sql
```

## IDE Testing Options

### Option 1: VS Code (Recommended - Easiest)

**Setup:**
1. Create `.vscode/mcp.json` in your workspace:
```json
{
  "servers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "type": "stdio",
      "env": {
        "MEM0_AI_ENHANCEMENT": "true"
      }
    }
  }
}
```

2. Restart VS Code
3. Test with: `@mem0 enhance_ai_prompt_tool file_path="test.js" language="javascript" prompt="Create a function" ai_model="generic_ai"`

### Option 2: Claude Desktop (Best for AI Testing)

**Setup:**
1. Edit `~/.config/claude-desktop/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_AI_ENHANCEMENT": "true"
      }
    }
  }
}
```

2. Restart Claude Desktop
3. Test with: "Help me write a React component" (mem0 will automatically enhance with memories)

### Option 3: Windsurf IDE (Your Current IDE)

**Setup:**
1. Same as VS Code - create `.vscode/mcp.json`
2. Restart Windsurf
3. Test MCP tools in chat panel

## Testing Scenarios

### Scenario 1: Basic AI Enhancement
```bash
# Store some memories first
@mem0 remember "I prefer using const over let in JavaScript"
@mem0 context_start "test-project"
@mem0 remember "This project uses React with TypeScript"

# Test enhancement
@mem0 enhance_ai_prompt_tool file_path="component.tsx" language="typescript" prompt="Create a React component" project_context="test-project" ai_model="generic_ai"
```

**Expected Result:**
```
✅ Enhanced prompt with 2 memories:

# Personal Coding Preferences:
- I prefer using const over let in JavaScript

# Project Context (test-project):
- This project uses React with TypeScript

# Current Task (generic_ai):
Create a React component

# Context Metadata:
- Language: typescript
- File: component.tsx
```

### Scenario 2: Hierarchical Memory Testing
```bash
# Set up different memory levels
@mem0 remember "Personal: I like functional components"
@mem0 context_start "team-project" --team-id 1
@mem0 remember "Team: We use styled-components for CSS"
@mem0 context_start "org-project" --organization-id 1  
@mem0 remember "Org: All components must have PropTypes"

# Test with all levels
@mem0 enhance_ai_prompt_tool file_path="Button.tsx" language="typescript" prompt="Create a button component" user_id=1 team_id=1 organization_id=1 ai_model="copilot"
```

### Scenario 3: Performance Testing
```bash
# Test response time
time @mem0 enhance_ai_prompt_tool file_path="test.py" language="python" prompt="Create a function" ai_model="generic_ai"
```

**Target:** < 200ms response time

## Troubleshooting

### MCP Server Not Starting
```bash
# Check Python path
which python
# Should be: /opt/homebrew/anaconda3/bin/python

# Test server directly
cd /Users/asrajag/Workspace/mem0/server
python mcp_server.py
# Should show: MCP server listening on stdio
```

### No Memories Retrieved
```bash
# Check database connection
@mem0 list_contexts
# Should show available contexts

# Store test memory
@mem0 remember "Test memory for debugging"
@mem0 recall "test"
# Should return the test memory
```

### IDE Not Recognizing MCP
1. **VS Code/Windsurf:** Ensure `.vscode/mcp.json` is in workspace root
2. **Claude Desktop:** Check config file path and JSON syntax
3. **All IDEs:** Restart after configuration changes

## Advanced Testing

### Test Cross-Team Approval Workflow
```bash
# Request cross-team access
@mem0 request_cross_team_access context_id=1 target_team_id=2 permission_level="read" justification="Need access for collaboration"

# Approve request (as team admin)
@mem0 approve_cross_team_request request_id=1

# Test enhanced prompt with cross-team memories
@mem0 enhance_ai_prompt_tool file_path="shared.js" language="javascript" prompt="Implement shared function" user_id=1 team_id=1
```

### Test Multiple AI Models
```bash
# Test different AI model contexts
@mem0 enhance_ai_prompt_tool prompt="Create auth function" ai_model="github_copilot"
@mem0 enhance_ai_prompt_tool prompt="Create auth function" ai_model="claude"  
@mem0 enhance_ai_prompt_tool prompt="Create auth function" ai_model="openai_gpt"
@mem0 enhance_ai_prompt_tool prompt="Create auth function" ai_model="google_gemini"
```

## Success Criteria

### ✅ Basic Functionality
- [ ] MCP server starts without errors
- [ ] IDE recognizes mem0 MCP tools
- [ ] `enhance_ai_prompt_tool` returns enhanced prompts
- [ ] Memories are retrieved and ranked correctly

### ✅ Performance
- [ ] Enhancement completes in < 200ms
- [ ] Memory retrieval in < 100ms
- [ ] No memory leaks or crashes

### ✅ Integration
- [ ] Works across multiple IDEs
- [ ] Hierarchical memory system functions
- [ ] Cross-team approval workflow works
- [ ] AI model abstraction layer works

## Next Steps After Testing

1. **Report Issues:** Document any bugs or performance issues
2. **Real AI Integration:** Connect to actual Copilot, Claude, GPT APIs
3. **Production Deployment:** Scale for team usage
4. **Performance Optimization:** Based on real-world usage patterns

## Quick Commands Reference

```bash
# Start servers
python server/mcp_server.py &
python server/main.py &

# Basic testing
@mem0 enhance_ai_prompt_tool file_path="test.js" language="javascript" prompt="test" ai_model="generic_ai"

# Store memories
@mem0 remember "Your coding preference"
@mem0 context_start "project-name"

# Check status
@mem0 list_contexts
@mem0 recall "search term"
```

The system is ready for comprehensive IDE testing with all documentation version controlled and committed!
