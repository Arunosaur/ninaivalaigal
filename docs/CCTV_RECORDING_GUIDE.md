# CCTV-Style Automatic Recording Guide

## Overview

The mem0 system now features **CCTV-style automatic recording** that captures AI interactions without requiring manual `remember` commands. This system follows the "simple like CCTV" philosophy - just turn it on/off like a switch.

## 🎥 CCTV Philosophy

- **Observer Mode**: Records AI interactions automatically when activated
- **Simple Control**: On/off switch functionality - no complex workflows
- **Background Operation**: Captures context without interrupting your work
- **Hierarchical Recall**: Retrieves memories across Personal → Team → Organization levels

## Quick Start

### 1. Start Recording (Turn CCTV On)
```bash
# Via FastAPI
curl -X POST "http://localhost:8000/context/start" \
  -H "Content-Type: application/json" \
  -d '{"context": "my-project"}'

# Via MCP (in VS Code or compatible IDE)
@mem0 context_start my-project
```

### 2. Work Normally
The system automatically captures:
- AI prompts and responses
- Code changes and decisions
- Project context and discussions
- Error resolutions and solutions

### 3. Stop Recording (Turn CCTV Off)
```bash
# Via FastAPI
curl -X POST "http://localhost:8000/context/stop" \
  -H "Content-Type: application/json" \
  -d '{"context": "my-project"}'

# Via MCP
@mem0 context_stop my-project
```

### 4. Recall Memories
```bash
# Hierarchical recall across all levels
curl "http://localhost:8000/memory/recall?query=authentication&context=my-project"

# Via MCP
@mem0 recall authentication my-project
```

## FastAPI Endpoints

### Recording Control
- `POST /context/start` - Start CCTV recording for a context
- `POST /context/stop` - Stop recording (specific context or all)
- `GET /context/status` - Check recording status

### Memory Operations
- `POST /memory/record` - Manual interaction recording (usually automatic)
- `GET /memory/recall` - Hierarchical memory retrieval

### Status Monitoring
- `GET /context/status` - View all active recordings
- `GET /context/active` - Legacy endpoint for active context

## MCP Tools (IDE Integration)

### Core Recording Tools
- `context_start(context_name)` - Start CCTV recording
- `context_stop(context_name?)` - Stop recording (all if no context specified)
- `get_ai_context()` - View recording status and available contexts

### Memory Tools
- `remember(text, context?)` - Manual memory storage
- `recall(query, context?)` - Search and retrieve memories
- `list_contexts()` - View all available contexts

### AI Enhancement Tools
- `enhance_ai_prompt()` - Enhance prompts with context
- `store_ai_feedback()` - Store AI interaction feedback

## Recording Behavior

### Automatic Capture
When CCTV recording is active, the system automatically captures:
- **AI Interactions**: Prompts, responses, and context
- **Code Changes**: Modifications and their reasoning
- **Problem Solving**: Error messages and solutions
- **Decision Making**: Architecture choices and trade-offs

### Message Buffering
- Messages are buffered in memory during active recording
- Auto-save occurs every 10 messages or 5 minutes
- Manual flush happens when recording stops
- No data loss during normal operation

### Context Isolation
- Each context maintains separate recording state
- Multiple contexts can record simultaneously
- User isolation prevents cross-user access
- Hierarchical access: Personal → Team → Organization

## Hierarchical Memory Recall

### Memory Levels
1. **Personal**: Your individual memories and context
2. **Team**: Shared team knowledge and decisions
3. **Organization**: Company-wide standards and practices

### Recall Strategy
```python
# System automatically searches in order:
# 1. Personal context memories
# 2. Team context memories
# 3. Organization context memories
# Returns combined results with source attribution
```

### Example Recall Response
```json
{
  "query": "authentication implementation",
  "results": {
    "personal": [
      {"content": "Used JWT tokens for API auth", "timestamp": "2024-01-15"}
    ],
    "team": [
      {"content": "Team standard: OAuth 2.0 for external APIs", "timestamp": "2024-01-10"}
    ],
    "organization": [
      {"content": "Security policy: Multi-factor auth required", "timestamp": "2024-01-01"}
    ]
  },
  "total_memories": 3
}
```

## VS Code Integration

### Configuration
Ensure your VS Code MCP configuration includes mem0:

```json
{
  "mcpServers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python3.11",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "MEM0_DATABASE_URL": "postgresql://mem0user:mem0pass@localhost:5432/mem0db",
        "MEM0_JWT_SECRET": "your-secure-jwt-secret"
      }
    }
  }
}
```

### Usage in VS Code
1. Open command palette (`Cmd+Shift+P`)
2. Type `@mem0` to access MCP tools
3. Use `context_start project-name` to begin recording
4. Work normally - interactions are captured automatically
5. Use `recall query` to retrieve relevant memories
6. Use `context_stop` when finished

## CLI Integration

### Shell Wrapper
The mem0 shell wrapper automatically detects active recording contexts:

```bash
# Commands are automatically captured when CCTV is active
git commit -m "Add authentication"
# → Automatically recorded to active context

# Manual memory storage still available
mem0 remember "Fixed authentication bug by updating JWT secret rotation"
```

### Environment Variables
```bash
export MEM0_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"
export MEM0_JWT_SECRET="your-secure-jwt-secret"
export MEM0_DEBUG=1  # Enable debug logging
```

## Security & Privacy

### User Isolation
- JWT-based authentication prevents cross-user access
- Each user's recordings are completely isolated
- Context permissions enforced at database level

### Data Control
- Recording is explicit - must be manually started
- No background recording without user activation
- Complete control over what contexts are recorded
- Easy to stop recording and clear buffers

### Environment Security
- No hardcoded credentials in source code
- Database URLs and secrets via environment variables
- Secure token-based authentication for multi-user deployments

## Troubleshooting

### Recording Not Working
1. Check if context is active: `GET /context/status`
2. Verify database connection
3. Ensure environment variables are set
4. Check MCP server logs for errors

### Memory Recall Issues
1. Verify context exists and has recordings
2. Check user permissions for context access
3. Ensure database contains memories for the query
4. Try broader search terms

### VS Code MCP Issues
1. Verify Python path in MCP configuration
2. Check environment variables are properly set
3. Restart VS Code after configuration changes
4. Review MCP server logs for connection errors

## Best Practices

### Context Organization
- Use descriptive context names: `project-auth`, `bug-fix-session`
- Keep contexts focused on specific tasks or features
- Start new contexts for different work sessions
- Stop recording when switching between unrelated tasks

### Memory Management
- Let the system auto-record during active development
- Use manual `remember` for important decisions or insights
- Regularly review and organize contexts
- Archive completed project contexts

### Team Collaboration
- Use shared context names for team projects
- Document important architectural decisions
- Share context names with team members
- Maintain consistent naming conventions

---

## Next Steps

With CCTV-style recording now active, you can:
1. **Start Recording**: Begin capturing your AI development sessions
2. **Work Naturally**: Let the system observe and learn from your interactions
3. **Recall Context**: Use hierarchical memory to enhance future AI interactions
4. **Scale Up**: Deploy for team usage with PostgreSQL backend

The system is now production-ready for seamless AI alignment and context preservation across all your development work.
