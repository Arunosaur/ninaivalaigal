# mem0 User Guide

## Overview

mem0 is a universal memory layer that captures and recalls your terminal commands, enabling powerful context-aware workflows across multiple projects and terminals.

## Quick Start

### 1. Start the Server
```bash
./manage.sh start
```

### 2. Source the Shell Integration
```bash
source ~/Workspace/mem0/client/mem0.zsh
export MEM0_DEBUG=1  # Optional: Enable debug logging
```

### 3. Create and Start a Context
```bash
./client/mem0 context start my-project
```

### 4. Work Normally
Your commands are now automatically captured:
```bash
git status
npm install
python main.py
```

### 5. Recall Your Work
```bash
./client/mem0 recall
# or recall from a specific context
./client/mem0 recall --context my-project
```

## Multi-Context Workflows

### Working on Multiple Projects Simultaneously

**Terminal 1 - Frontend Work:**
```bash
export MEM0_CONTEXT=frontend-app
./client/mem0 context start frontend-app
npm run dev
git commit -m "Add new component"
```

**Terminal 2 - Backend Work:**
```bash
export MEM0_CONTEXT=backend-api
./client/mem0 context start backend-api
python manage.py migrate
pytest tests/
```

**Terminal 3 - DevOps Work:**
```bash
export MEM0_CONTEXT=infrastructure
./client/mem0 context start infrastructure
docker build -t myapp .
kubectl apply -f deployment.yaml
```

### Context Management Commands

#### Start a New Context
```bash
./client/mem0 context start <context-name>
```

#### List All Contexts
```bash
# List all contexts with status
./client/mem0 contexts

# List only active contexts
./client/mem0 contexts active
```

#### Stop a Context
```bash
# Stop specific context
./client/mem0 context stop <context-name>

# Stop currently active context
./client/mem0 context stop
```

#### Delete a Context
```bash
./client/mem0 context delete <context-name>
```
**Warning:** This permanently deletes the context and all its memories.

#### Check Terminal Context
```bash
./client/mem0 context active
```
Shows the context set for the current terminal session (via MEM0_CONTEXT environment variable).

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
