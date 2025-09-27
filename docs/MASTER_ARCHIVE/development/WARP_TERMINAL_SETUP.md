# Warp Terminal Setup Guide for mem0

## Quick Setup for Warp Terminal

### 1. Install Shell Integration
```bash
# Add mem0 shell integration to your zsh config
echo 'source /Users/asrajag/Workspace/mem0/client/mem0.zsh' >> ~/.zshrc

# Reload your shell configuration
source ~/.zshrc
```

### 2. Start mem0 Server
```bash
# Navigate to mem0 directory
cd /Users/asrajag/Workspace/mem0

# Start the server (PostgreSQL-enabled)
./manage.sh start
```

### 3. Authenticate (Optional - for multi-user)
```bash
# Register a new user (first time)
./client/mem0 auth register --username yourname --email your@email.com --password yourpass

# Or login with existing user
./client/mem0 auth login --username yourname --password yourpass

# Verify authentication
./client/mem0 auth me
```

### 4. Start Using mem0
```bash
# Start a new context for your work session
./client/mem0 start warp-session-$(date +%s)

# Verify context is active
./client/mem0 active
# Should show: "Terminal context: warp-session-TIMESTAMP"

# Enable debug mode to see what's being captured
export MEM0_DEBUG=1

# Now work normally - all commands are captured automatically
ls -la
git status
npm install
# etc...

# Recall your session memories
./client/mem0 recall --context warp-session-TIMESTAMP
```

## Warp-Specific Features

### Command History Integration
- mem0 captures commands alongside Warp's built-in history
- Context-aware command recall across sessions
- Works with Warp's AI command suggestions

### Workflow Integration
- Use with Warp's workflows and saved commands
- Context switching preserves state across Warp restarts
- Compatible with Warp's team sharing features

### AI Assistant Integration
- mem0 memories can inform Warp AI suggestions
- Historical context improves command recommendations
- Session continuity across different projects

## Testing Your Setup

### Basic Functionality Test
```bash
# 1. Check server is running
curl -s http://127.0.0.1:13370/contexts

# 2. Test context creation
./client/mem0 start test-warp-$(date +%s)

# 3. Run some commands
date
whoami
echo "testing mem0 in Warp"

# 4. Check memories were captured
./client/mem0 recall --context test-warp-TIMESTAMP

# 5. Clean up test context
./client/mem0 delete test-warp-TIMESTAMP
```

### Advanced Features Test
```bash
# Test context switching
./client/mem0 start project-a
echo "Working on project A"
./client/mem0 start project-b
echo "Working on project B"

# Check both contexts exist
./client/mem0 contexts

# Recall specific context
./client/mem0 recall --context project-a
./client/mem0 recall --context project-b
```

## Troubleshooting

### Shell Integration Not Working
```bash
# Check if mem0 functions are loaded
type mem0_preexec
# Should show function definition

# Check if hooks are registered
echo $preexec_functions | grep mem0
# Should show mem0_preexec

# Reload shell integration
source /Users/asrajag/Workspace/mem0/client/mem0.zsh
```

### Commands Not Being Captured
```bash
# Enable debug mode
export MEM0_DEBUG=1

# Check if context is active
./client/mem0 active

# Verify server connectivity
curl -s http://localhost:13370/contexts

# Check server logs for errors
# (in server terminal window)
```

### Authentication Issues
```bash
# Check current user
./client/mem0 auth me

# Re-authenticate if needed
./client/mem0 auth login --username yourname --password yourpass

# Check token file exists
ls -la ~/.mem0/auth.json
```

## Pro Tips for Warp Users

1. **Use descriptive context names**: `./client/mem0 start frontend-debugging-session`
2. **Context per project**: Keep different projects in separate contexts
3. **Regular recall**: Use `./client/mem0 recall` to review your work session
4. **Debug mode**: Keep `MEM0_DEBUG=1` enabled while learning the system
5. **Combine with Warp AI**: Use mem0 memories to provide context to Warp's AI features

## Integration with Warp Workflows

### Save Common Commands as Warp Workflows
```bash
# Create Warp workflow for starting mem0 session
# Name: "Start mem0 Session"
# Command: ./client/mem0 start $(basename $PWD)-$(date +%s)

# Create workflow for recalling memories
# Name: "Recall mem0 Memories"
# Command: ./client/mem0 recall --context $(./client/mem0 active | cut -d: -f2 | xargs)
```

### Team Collaboration
- Share context names with team members
- Use consistent naming conventions
- Leverage mem0's multi-user features for team contexts
- Combine with Warp's team features for comprehensive collaboration
