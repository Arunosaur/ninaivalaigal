# IDE Integration Guide for mem0

This document provides comprehensive guidance for integrating mem0 with various IDEs and development environments.

## Current Integration Status

### ✅ VS Code Extension (Available)
- **Location**: `vscode-client/`
- **Status**: Full context management with chat participant and authentication
- **Features**: Auto-context detection, explicit context commands, remember/recall, user authentication

### ✅ JetBrains Plugin (Available)
- **Location**: `jetbrains-plugin/`
- **Status**: Native plugin with full IDE integration and sharing support
- **Features**: Keyboard shortcuts, tool window, context menus, settings, multi-user support

### ✅ Universal Shell Integration (Available)
- **Location**: `client/mem0-universal.sh`, `client/mem0-windows.ps1`, `client/mem0-fish.fish`
- **Status**: Cross-platform shell integration with authentication and sharing
- **Features**: Automatic command capture, multi-context support, user authentication

### ✅ Multi-User Support (Complete)
- **Status**: ✅ FULLY IMPLEMENTED - Complete authentication and user isolation
- **Current**: Full user-scoped context isolation with JWT authentication
- **Features**: User registration, login, secure token management, cross-user data isolation

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

### 2. Universal Shell Integration

**Cross-Platform Setup:**

**Linux/Unix (Bash/Zsh/Fish):**
```bash
# Add to your shell configuration (~/.bashrc, ~/.zshrc, or ~/.config/fish/config.fish)
source /path/to/mem0/client/mem0-universal.sh  # For bash/zsh
# or
source /path/to/mem0/client/mem0-fish.fish     # For fish

# Authenticate
./client/mem0 auth login --username youruser --password yourpass

# Start context
mem0_context_start my-project

# Work normally - commands captured automatically
```

**Windows (PowerShell):**
```powershell
# Load PowerShell integration
. .\client\mem0-windows.ps1

# Authenticate
.\client\mem0.exe auth login --username youruser --password yourpass

# Start context
Start-Mem0Context -ContextName "my-project"

# Work normally - commands captured automatically
```

**Warp Terminal:**
- Uses zsh by default - same integration as Linux/Unix
- Shell hooks work identically
- No special configuration needed

**Windows Terminal:**
- Supports multiple shells (PowerShell, WSL, Command Prompt)
- Use appropriate integration script for each shell
- Context isolation works across different terminal profiles

### 3. JetBrains IDEs Integration

**Method 1: Native Plugin (Recommended)**
```bash
# Install the mem0 JetBrains plugin
cd jetbrains-plugin
./gradlew buildPlugin
# Install from: Settings → Plugins → Install from disk → mem0-jetbrains-0.1.0.zip
```

**Features:**
- **Keyboard shortcuts**: Ctrl+Shift+M (remember), Ctrl+Shift+R (recall)
- **Context menu**: Right-click → "Remember Selection"
- **Tool window**: View → Tool Windows → mem0
- **Auto-context detection**: Uses project folder name
- **Settings**: Configure server URL, CLI path, default context

**Method 2: External Tools (Alternative)**
1. Go to Settings → Tools → External Tools
2. Add new tool:
   - Name: "mem0 Remember"
   - Program: `/path/to/mem0/client/mem0`
   - Arguments: `remember "$SELECTION$" --context $Prompt$`
   - Working Directory: `$ProjectFileDir$`

**Method 3: Terminal Integration**
- Use built-in terminal with zsh integration
- Commands automatically captured when context is active

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

## User Authentication Implementation ✅ COMPLETE

**Status**: ✅ FULLY IMPLEMENTED - Complete JWT authentication system with user isolation

**Implemented Components:**

1. **Authentication Endpoints**:
```python
# Already implemented in server/main.py
@app.post("/auth/login")      # JWT token-based login
@app.post("/auth/register")   # User registration with bcrypt
@app.get("/auth/me")          # Get current user info
@app.post("/auth/logout")     # Token invalidation
```

2. **Session Management**:
```python
# Implemented in server/auth.py
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Decode JWT, return user with proper isolation
    return decode_jwt_token(token)

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional)):
    # Optional authentication for public endpoints
    return decode_jwt_token(token) if token else None
```

3. **Client Authentication**:
```bash
# Complete CLI authentication support
./client/mem0 auth register --username user --email user@domain.com --password pass
./client/mem0 auth login --username user --password pass
./client/mem0 auth me                    # Show current user
./client/mem0 auth logout               # Logout and clear token

# Token stored securely in ~/.mem0/auth.json
# Automatic token refresh and validation
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

### 3. Cross-Platform Support ✅ COMPLETE
- ✅ Windows PowerShell integration (mem0-windows.ps1)
- ✅ Fish shell support (mem0-fish.fish)
- ✅ Universal shell integration (mem0-universal.sh)
- ✅ Vim/Neovim plugin framework ready
- ✅ Cross-platform context isolation and authentication

## Troubleshooting

### Common Issues:

**Authentication Issues:**
- Verify JWT token is valid: `./client/mem0 auth me`
- Check token expiration and refresh if needed
- Ensure server is running and accessible

**VS Code Extension Not Working:**
- Check `mem0.projectRoot` setting in VS Code settings
- Verify server is running on port 13370
- Check extension logs in VS Code Developer Tools
- Ensure user is authenticated: `./client/mem0 auth login`

**Shell Integration Not Capturing:**
- Verify shell integration script is sourced
- Check if context is active: `mem0_context_active` or `Get-Mem0Context`
- Enable debug logging: `export MEM0_DEBUG=1` (bash/zsh) or `$env:MEM0_DEBUG = "1"` (PowerShell)
- Ensure user authentication is working

**Context Isolation Issues:**
- ✅ RESOLVED: Full user authentication provides true isolation
- Contexts are now properly scoped to authenticated users
- Cross-user data access is cryptographically prevented
- Use unique context names within your user scope

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
