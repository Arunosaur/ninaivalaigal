# mem0 User Guide

## Overview

mem0 is a simple CCTV-like observer that helps AI agents stay on target during development. It quietly watches and records your terminal activity when turned on.

## Quick Start

### Prerequisites
- PostgreSQL database (Docker recommended):
  ```bash
  docker run --name mem0-postgres -e POSTGRES_DB=mem0db -e POSTGRES_USER=mem0user -e POSTGRES_PASSWORD=mem0pass -p 5432:5432 -d postgres:15
  ```

### Starting mem0

1. **Start the FastAPI server:**
   ```bash
   ./manage.sh start
   ```

2. **Start the MCP server (for AI tools like Claude Desktop):**
   ```bash
   cd server && python run_mcp_server.py
   ```

3. **Source shell integration (once per terminal):**
   ```bash
   source client/mem0.zsh
   ```

4. **Turn on recording (like flipping a switch):**
   ```bash
   mem0_on my-project
   # or just: mem0_on (uses current directory name)
   ```

5. **Work normally - commands are captured silently:**
   ```bash
   git status
   npm install
   ./run-tests.sh
   ```

6. **Turn off when done:**
   ```bash
   mem0_off
   ```

7. **Let AI agents recall your session:**
   ```bash
   ./client/mem0 recall --context my-project
   ```

## Architecture Overview

mem0 now runs a **dual-server architecture**:

### FastAPI Server (Port 13370)
- **Purpose**: REST API for CLI, shell integration, and VS Code extension
- **Endpoints**: `/contexts`, `/memory`, `/memory/all`, etc.
- **Usage**: Traditional HTTP clients and existing integrations

### MCP Server (stdio transport)
- **Purpose**: Model Context Protocol server for AI tools
- **Clients**: Claude Desktop, VS Code with MCP support, other MCP-compatible tools
- **Tools**: `remember`, `recall`, `context_start`, `context_stop`, `list_contexts`
- **Resources**: Context listings, memory feeds, recent memories
- **Prompts**: Analysis templates for AI consumption

### Database Backend
- **PostgreSQL**: Production database with full multi-user support
- **SQLite fallback**: Development mode when PostgreSQL unavailable
- **Schema**: User isolation, context-based memory organization

## Multi-Context Workflows

### Working on Multiple Projects Simultaneously

**Terminal 1 - Frontend Work:**
```bash
source client/mem0.zsh
mem0_on frontend-app
npm run dev
git commit -m "Add new component"
mem0_off
```

**Terminal 2 - Backend Work:**
```bash
source client/mem0.zsh
mem0_on backend-api
python manage.py migrate
pytest tests/
mem0_off
```

**Terminal 3 - DevOps Work:**
```bash
source client/mem0.zsh
mem0_on infrastructure
docker build -t myapp .
kubectl apply -f deployment.yaml
mem0_off
```

### Simple Commands

#### Turn Recording On/Off
```bash
mem0_on [project-name]    # Start recording (uses directory name if not specified)
mem0_off                  # Stop recording
```

#### For AI Agents - Context Management
```bash
# List all contexts
./client/mem0 contexts

# Recall memories for AI agents
./client/mem0 recall --context <project-name>

# Check what's currently recording
./client/mem0 context active
```

### Per-Terminal Context Selection

Set the `MEM0_CONTEXT` environment variable to specify which context should receive commands in that terminal:

```bash
# Terminal captures to 'project-alpha'
export MEM0_CONTEXT=project-alpha
echo "Working on alpha features"

# Terminal captures to 'project-beta'  
export MEM0_CONTEXT=project-beta
echo "Testing beta functionality"
```

**Fallback Behavior:** If `MEM0_CONTEXT` is not set, commands are captured to the most recently created active context.

## Memory Operations

### Recall Commands
```bash
# Recall from active context
./client/mem0 recall

# Recall from specific context
./client/mem0 recall --context project-name

# Export memories to file
./client/mem0 export --context project-name --output project-history.json
```

### Manual Memory Addition
```bash
# Add a custom memory entry
./client/mem0 remember "Deployed version 2.1.0 to production" --context deployment-log
```

## Best Practices

### 1. Context Naming
- Use descriptive names: `frontend-redesign`, `api-v2`, `bug-fix-auth`
- Avoid spaces: Use hyphens or underscores
- Include version/iteration: `mobile-app-v1`, `database-migration-2024`

### 2. Multi-Project Workflows
- **One context per project/feature**: Keep work isolated
- **Use environment variables**: Set `MEM0_CONTEXT` in each terminal
- **Regular cleanup**: Delete old contexts when projects are complete

### 3. Team Collaboration
- **Consistent naming**: Agree on context naming conventions
- **Export/share**: Use export feature to share command histories
- **Documentation**: Include context names in project documentation

## Troubleshooting

### Commands Not Being Captured
1. **Check if context is active:**
   ```bash
   ./client/mem0 contexts
   ```

2. **Verify shell integration:**
   ```bash
   echo $MEM0_DEBUG
   # Should show debug output if set to 1
   ```

3. **Re-source shell wrapper:**
   ```bash
   source ~/Workspace/mem0/client/mem0.zsh
   ```

### Multiple Active Contexts
This is normal! You can have multiple active contexts simultaneously. Use `MEM0_CONTEXT` to control which context receives commands in each terminal.

### Server Connection Issues
1. **Check server status:**
   ```bash
   ./manage.sh status
   ```

2. **Restart server:**
   ```bash
   ./manage.sh restart
   ```

3. **Check port availability:**
   ```bash
   lsof -i :13370
   ```

### Context Not Found
- Verify context exists: `./client/mem0 contexts`
- Check spelling and case sensitivity
- Create context if needed: `./client/mem0 context start <name>`

## Advanced Configuration

### Environment Variables
- `MEM0_CONTEXT`: Specify context for current terminal
- `MEM0_DEBUG`: Enable debug logging (set to 1)
- `MEM0_PORT`: Override server port (default: 13370)

### Configuration File
Edit `mem0.config.json` to customize:
- Server host/port settings
- Cache TTL for context lookups
- Command capture patterns
- Storage options

## Examples

### Daily Development Workflow
```bash
# Morning setup
./manage.sh start
source ~/Workspace/mem0/client/mem0.zsh

# Start working on feature
export MEM0_CONTEXT=user-authentication
./client/mem0 context start user-authentication

# Development work
git checkout -b feature/auth
npm install passport
# ... more commands ...

# End of day - review work
./client/mem0 recall --context user-authentication
```

### Bug Investigation
```bash
# Create investigation context
export MEM0_CONTEXT=bug-login-issue
./client/mem0 context start bug-login-issue

# Investigation commands
grep -r "login" logs/
docker logs app-container
curl -X POST /api/login

# Later - recall investigation steps
./client/mem0 recall --context bug-login-issue
```

### Code Review Preparation
```bash
# Export command history for code review
./client/mem0 export --context feature-implementation --output review-commands.json

# Share with team or include in PR description
```

## Editor Integration

### Terminal Integration
**Setup (once per terminal):**
```bash
source client/mem0.zsh
```

**Commands:**
```bash
mem0_on [project-name]    # Start recording (uses directory name if not specified)
mem0_off                  # Stop recording
export MEM0_CONTEXT=name  # Set context for this terminal
```

### VS Code Integration
**Setup:**
1. Install mem0 VS Code extension from marketplace
2. Set workspace environment variable in `.vscode/settings.json`:
```json
{
  "terminal.integrated.env.osx": {
    "MEM0_CONTEXT": "my-project"
  },
  "terminal.integrated.env.linux": {
    "MEM0_CONTEXT": "my-project"
  },
  "terminal.integrated.env.windows": {
    "MEM0_CONTEXT": "my-project"
  }
}
```

**What gets captured:**
- File operations (create, edit, delete, rename)
- Git operations (commit, push, pull, branch)
- Debug sessions (breakpoints, variable inspection)
- Terminal commands within VS Code
- Extension installations and configurations

**Commands:**
```bash
# In VS Code integrated terminal
mem0_on my-vscode-project
# Work normally - all actions captured
mem0_off
```

### JetBrains Integration (IntelliJ, PyCharm, WebStorm)
**Setup:**
1. Install mem0 plugin from JetBrains marketplace
2. Configure project-specific context in Settings > Tools > mem0:
   - Context Name: `my-jetbrains-project`
   - Auto-start recording: ✓

**What gets captured:**
- Build operations (compile, package, deploy)
- Test runs (unit tests, integration tests)
- Refactoring operations (rename, extract method, move class)
- Code generation (templates, auto-completion usage)
- VCS operations (commit, merge, rebase)
- Plugin installations and configurations

**Commands:**
```bash
# Set context for JetBrains project
export MEM0_CONTEXT=my-jetbrains-project

# Or use IDE settings to auto-set context
# Tools > mem0 > Start Recording
```

## Integration with Development Tools

### Git Integration
mem0 works seamlessly with git workflows:
```bash
export MEM0_CONTEXT=feature-branch-name
git checkout -b feature/new-api
# Commands automatically captured to context
```

### Docker Development
```bash
export MEM0_CONTEXT=docker-setup
docker build -t myapp .
docker run -p 8080:8080 myapp
docker logs myapp
# All docker commands captured for later reference
```

### Testing Workflows
```bash
export MEM0_CONTEXT=test-suite-run
pytest tests/ -v
npm test
coverage report
# Test commands and results captured
```
