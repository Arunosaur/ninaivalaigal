# Universal AI Integration Configuration Guide

**Version:** 1.0.0
**Date:** 2025-09-12
**Status:** Production Ready

## Overview

This guide provides configuration examples for integrating mem0's universal AI enhancement system with any IDE via clean MCP architecture. No IDE-specific extensions required.

## Quick Start

### 1. Update PostgreSQL Schema
```bash
psql -d mem0_db -f scripts/update_schema_approval.sql
```

### 2. Start mem0 Servers
```bash
# Terminal 1: MCP Server (for IDEs)
cd /Users/asrajag/Workspace/mem0/server
python mcp_server.py

# Terminal 2: FastAPI Server (for CLI/web)
python main.py
```

### 3. Configure Your IDE
Choose your IDE configuration below.

## IDE Configurations

### VS Code
**File:** `.vscode/mcp.json` (workspace) or global settings

```json
{
  "servers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "type": "stdio",
      "env": {
        "MEM0_AI_ENHANCEMENT": "true",
        "MEM0_DATABASE_URL": "postgresql://user:pass@localhost/mem0_db"
      }
    }
  }
}
```

### Windsurf IDE
**File:** `.vscode/mcp.json` (same as VS Code)

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

### Claude Desktop
**File:** `~/.config/claude-desktop/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_AI_ENHANCEMENT": "true",
        "MEM0_DATABASE_URL": "postgresql://user:pass@localhost/mem0_db"
      }
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
        "type": "stdio",
        "env": {
          "MEM0_AI_ENHANCEMENT": "true"
        }
      }
    }
  }
}
```

### JetBrains IDEs (IntelliJ, PyCharm, WebStorm)
**Note:** Requires custom plugin update (coming soon)

For now, use HTTP proxy mode:
```json
{
  "mem0": {
    "endpoint": "http://localhost:13371/enhance-prompt",
    "enabled": true
  }
}
```

## MCP Tools Available

### `enhance_ai_prompt_tool`
Enhance any AI prompt with relevant mem0 memories.

**Usage in IDE:**
```
@mem0 enhance_ai_prompt_tool file_path="auth.ts" language="typescript" prompt="Complete authentication function" ai_model="github_copilot" user_id=1 team_id=1 project_context="auth-system"
```

**Parameters:**
- `file_path`: Current file path
- `language`: Programming language
- `prompt`: Original AI prompt
- `cursor_position`: Cursor position (optional)
- `surrounding_code`: Code around cursor (optional)
- `ai_model`: AI model being used (copilot, claude, gpt, gemini)
- `user_id`: User ID for personal memories
- `team_id`: Team ID for team memories
- `organization_id`: Organization ID for org memories
- `project_context`: Project context name
- `ide_name`: IDE name for analytics
- `interaction_type`: Type of interaction (completion, chat, review)

### `get_ai_context`
Get available contexts and memory counts.

**Usage:**
```
@mem0 get_ai_context user_id=1 project_context="my-project"
```

### `store_ai_feedback`
Store AI interaction feedback for learning.

**Usage:**
```
@mem0 store_ai_feedback original_prompt="Complete function" enhanced_prompt="Enhanced with memories" ai_response="Generated code" user_accepted=true ai_model="copilot"
```

## AI Model Integration Examples

### GitHub Copilot Enhancement
```typescript
// In VS Code with Copilot
// 1. Copilot generates suggestion
// 2. mem0 enhances with relevant memories
// 3. Enhanced suggestion considers:
//    - Personal coding preferences
//    - Team standards
//    - Project patterns
//    - Organizational guidelines
```

### Claude Desktop Enhancement
```markdown
# In Claude Desktop chat
User: Help me write a React component

# mem0 automatically enhances with:
- Personal React patterns you prefer
- Team component standards
- Project-specific conventions
- Organizational React guidelines
```

### Generic AI Enhancement
```python
# Works with any AI model
enhanced_prompt = await enhance_ai_prompt(
    file_path="component.tsx",
    language="typescript",
    prompt="Create a user profile component",
    ai_model="generic_ai",
    user_id=1,
    team_id=1,
    project_context="user-dashboard"
)
```

## Memory Hierarchy in Action

### Example Enhancement Flow

**Original Prompt:**
```
"Complete the user authentication function"
```

**Enhanced Prompt with mem0:**
```
# Personal Coding Preferences:
- Always validate JWT token  # pragma: allowlist secrets before processing
- Prefer async/await over .then() chains
- Use TypeScript interfaces for better type safety

# Team Standards & Patterns:
- Team standard: Use bcrypt for password  # pragma: allowlist secret hashing
- All auth functions must return standardized response format
- Follow team's error handling patterns

# Cross-Team Best Practices:
- Backend team pattern: Always log authentication attempts
- Security team requirement: Rate limiting on auth endpoints

# Organizational Guidelines:
- Organization policy: All auth functions must have error handling
- Security standard: Never log sensitive data
- Compliance requirement: Audit all authentication events

# Current Task (github_copilot):
Complete the user authentication function

# Context Metadata:
- Language: typescript
- File: auth.ts
- IDE: vscode
```

## Performance Configuration

### Environment Variables
```bash
# Performance tuning
export MEM0_MAX_MEMORIES_PER_PROMPT=10
export MEM0_MEMORY_CACHE_TTL=300
export MEM0_AI_ENHANCEMENT_TIMEOUT=5

# Database optimization
export MEM0_DATABASE_POOL_SIZE=20
export MEM0_DATABASE_MAX_OVERFLOW=30

# Logging
export MEM0_LOG_LEVEL=INFO
export MEM0_AI_INTERACTION_LOGGING=true
```

### Performance Targets
- Memory retrieval: < 100ms
- Prompt enhancement: < 200ms
- End-to-end latency: < 500ms

## Testing Your Configuration

### 1. Test MCP Connection
```bash
# Test MCP server directly
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python server/mcp_server.py
```

### 2. Test AI Enhancement
```bash
# Test enhancement tool
@mem0 enhance_ai_prompt_tool file_path="test.js" language="javascript" prompt="Create a function" ai_model="generic_ai"
```

### 3. Test Memory Retrieval
```bash
# Store some memories first
@mem0 remember "I prefer using const over let in JavaScript"
@mem0 context_start "test-project"
@mem0 remember "This project uses React with TypeScript"

# Test enhancement
@mem0 enhance_ai_prompt_tool file_path="component.tsx" language="typescript" prompt="Create a React component" project_context="test-project"
```

## Troubleshooting

### Common Issues

#### MCP Server Not Starting
```bash
# Check Python path
which python
/opt/homebrew/anaconda3/bin/python

# Test server directly
cd server && python mcp_server.py
```

#### No Memories Retrieved
```bash
# Check database connection
psql -d mem0_db -c "SELECT COUNT(*) FROM memories;"

# Verify user context
@mem0 list_contexts
```

#### Performance Issues
```bash
# Check database indexes
psql -d mem0_db -c "\d+ memories"

# Monitor query performance
export MEM0_LOG_LEVEL=DEBUG
```

### Debug Mode
```bash
# Enable debug logging
export MEM0_DEBUG=true
export MEM0_LOG_LEVEL=DEBUG

# Start server with debug
python server/mcp_server.py --debug
```

## Security Configuration

### Authentication
```bash
# Set JWT secret
export MEM0_JWT_SECRET="your-secure-secret-key"

# Enable authentication
export MEM0_REQUIRE_AUTH=true
```

### Access Control
```json
{
  "mem0": {
    "access_control": {
      "personal_memories": "user_only",
      "team_memories": "team_members_only",
      "cross_team_memories": "approval_required",
      "org_memories": "organization_members"
    }
  }
}
```

## Advanced Configuration

### Custom Memory Ranking
```python
# Custom relevance scoring
def custom_memory_ranking(memory, context):
    score = 0

    # Language match (high priority)
    if context.language in memory.content.lower():
        score += 3

    # Project-specific patterns
    if context.project_context in memory.content.lower():
        score += 2

    # AI model specific
    if context.ai_model.value in memory.content.lower():
        score += 2

    return score
```

### Multi-Project Configuration
```json
{
  "servers": {
    "mem0-project-a": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/path/to/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_PROJECT_CONTEXT": "project-a"
      }
    },
    "mem0-project-b": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/path/to/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_PROJECT_CONTEXT": "project-b"
      }
    }
  }
}
```

## Migration from Extensions

### From VS Code Extension
1. Remove old extension: `code --uninstall-extension mem0.mem0-vscode`
2. Add MCP configuration above
3. Restart VS Code
4. Test with `@mem0 enhance_ai_prompt_tool`

### From JetBrains Plugin
1. Disable old plugin in IDE settings
2. Configure HTTP proxy mode (temporary)
3. Wait for updated plugin with MCP support

## Support

### Getting Help
- **Documentation:** `/docs/UNIVERSAL_AI_CONFIGURATION.md`
- **Issues:** GitHub Issues for bug reports
- **Testing:** Run `python tests/test_universal_ai_wrapper.py`

### Performance Monitoring
```bash
# Monitor enhancement latency
curl -X GET "http://localhost:13370/metrics" | grep ai_enhancement_latency

# Check memory usage
ps aux | grep mcp_server.py
```

This configuration enables seamless AI enhancement across any IDE with mem0's hierarchical memory system, providing intelligent, context-aware AI assistance without requiring IDE-specific extensions.
