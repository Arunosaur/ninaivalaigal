# IDE Integration Guide for mem0

This document provides comprehensive guidance for integrating mem0 with various IDEs and development environments.

## Current Integration Status

### ✅ VS Code Extension (Available)
- **Location**: `vscode-client/`
- **Status**: Implemented with chat participant
- **Features**: Remember/recall commands via VS Code chat interface

### ✅ Terminal Integration (zsh/bash)
- **Location**: `client/mem0.zsh`
- **Status**: Fully functional
- **Features**: Automatic command capture, context management

### ⚠️ Multi-User Support (Partial)
- **Status**: Database ready, authentication missing
- **Current**: Context isolation by name only
- **Needed**: User authentication system

## Detailed Integration Instructions

### 1. VS Code Extension

**Installation:**
```bash
cd vscode-client
npm install
npm run compile
code --install-extension mem0-*.vsix
```

**Configuration:**
Add to VS Code settings.json:
```json
{
    "mem0.projectRoot": "/absolute/path/to/mem0"
}
```

**Usage:**
- Open VS Code chat panel
- Type `@mem0 remember <memory>`
- Type `@mem0 recall` to retrieve memories
- Type `@mem0 observe` to see chat history

### 2. Terminal Integration

**Zsh Setup (Recommended):**
```bash
# Add to ~/.zshrc
source /path/to/mem0/client/mem0.zsh

# Enable debug logging (optional)
export MEM0_DEBUG=1

# Start recording
./client/mem0 context start my-session
```

**Bash Setup:**
```bash
# Create bash version of mem0.zsh
# Replace zsh-specific hooks with bash equivalents
# Add to ~/.bashrc
```

**Warp Terminal:**
- Uses zsh by default - same integration as above
- Shell hooks work identically
- No special configuration needed

### 3. JetBrains IDEs Integration

**Method 1: External Tools**
1. Go to Settings → Tools → External Tools
2. Add new tool:
   - Name: "mem0 Remember"
   - Program: `/path/to/mem0/client/mem0`
   - Arguments: `remember "$SELECTION$" --context $Prompt$`
   - Working Directory: `$ProjectFileDir$`

**Method 2: Terminal Integration**
- Use built-in terminal with zsh integration
- Commands automatically captured when context is active

**Method 3: Custom Plugin (Future)**
- Create IntelliJ IDEA plugin
- Integrate with IDE's indexing system
- Capture code changes, refactoring actions

### 4. Zed Editor Integration

**Current Options:**
1. **Terminal Integration**: Use Zed's terminal with zsh hooks
2. **External Commands**: Configure custom commands in Zed
3. **Future Plugin**: Zed extension system (when available)

**Setup:**
```json
// Zed settings.json
{
    "terminal": {
        "shell": {
            "program": "zsh",
            "args": ["-l"]
        }
    }
}
```

### 5. Cursor/Claude Integration

**Method 1: Terminal Commands**
- Use terminal integration within Cursor
- Commands captured automatically

**Method 2: Custom Integration**
- Leverage Cursor's AI features
- Create custom prompts that use mem0 CLI

## User Authentication Implementation

**Current Issue**: No user identification system

**Required Components:**

1. **Authentication Endpoints**:
```python
@app.post("/auth/login")
def login(credentials: UserCredentials):
    # Validate user, return JWT token
    pass

@app.post("/auth/register") 
def register(user_data: UserRegistration):
    # Create new user account
    pass
```

2. **Session Management**:
```python
# Add to all endpoints
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decode JWT, return user_id
    pass
```

3. **Client Authentication**:
```bash
# Login command
./client/mem0 auth login --username user --password pass

# Store token locally
echo "token" > ~/.mem0_token
```

## Testing Scripts

### Run Environment Tests:
```bash
./tests/test_environments.sh
```

### Manual Testing:

**1. VS Code Test:**
```bash
# Install extension
cd vscode-client && npm run compile
code --install-extension mem0-*.vsix

# Test in VS Code chat
@mem0 remember "Testing VS Code integration"
@mem0 recall
```

**2. Terminal Test:**
```bash
# Source shell integration
source client/mem0.zsh

# Start context
./client/mem0 context start terminal-test

# Run commands (automatically captured)
ls -la
git status

# Check memories
./client/mem0 recall --context terminal-test
```

**3. Multi-Context Test:**
```bash
# Test context isolation
./client/mem0 context start user1-session
./client/mem0 remember '{"type": "test", "source": "user1", "data": {"user": "user1"}}'
./client/mem0 context stop

./client/mem0 context start user2-session  
./client/mem0 remember '{"type": "test", "source": "user2", "data": {"user": "user2"}}'

# Verify isolation
./client/mem0 contexts
./client/mem0 recall --context user1-session
./client/mem0 recall --context user2-session
```

## Future Enhancements

### 1. IDE-Specific Features
- **VS Code**: Workspace indexing, file change tracking
- **JetBrains**: Refactoring history, debugging sessions
- **Zed**: Real-time collaboration memory sharing

### 2. Advanced Integrations
- Git hook integration (commit messages, branch context)
- CI/CD pipeline memory (build results, deployment logs)
- Code review context (PR discussions, feedback)

### 3. Cross-Platform Support
- Windows PowerShell integration
- Fish shell support
- Vim/Neovim plugin

## Troubleshooting

### Common Issues:

**VS Code Extension Not Working:**
- Check `mem0.projectRoot` setting
- Verify server is running on port 13370
- Check extension logs in Developer Tools

**Shell Integration Not Capturing:**
- Verify `source client/mem0.zsh` was run
- Check if context is active: `./client/mem0 context active`
- Enable debug: `export MEM0_DEBUG=1`

**Context Isolation Issues:**
- Currently contexts are global (no user auth)
- Use unique context names per user
- Implement authentication for true isolation

### Debug Commands:
```bash
# Check server status
curl http://127.0.0.1:13370/

# Test CLI connectivity
./client/mem0 contexts

# Check shell hook
type mem0_preexec

# View debug logs
export MEM0_DEBUG=1
# Run commands and check stderr
```
