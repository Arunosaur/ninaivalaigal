# IDE Integration Guide for mem0

This document provides comprehensive guidance for integrating mem0 with various IDEs and development environments.

## Current Integration Status

### ✅ MCP Configuration (Recommended)
- **Supported IDEs**: Windsurf, VS Code, Claude Desktop, Zed, Cursor
- **Status**: Native MCP protocol support via configuration files
- **Features**: Direct MCP server integration, no custom extensions needed
- **Configuration**: `.vscode/mcp.json` or IDE-specific MCP config files

### ✅ Legacy Extensions (Fallback)
- **VS Code Extension**: `vscode-client/` - Custom extension using MCP internally
- **JetBrains Plugin**: `jetbrains-plugin/` - Custom plugin using MCP internally
- **Status**: Available for IDEs without native MCP support

### ✅ Universal Shell Integration (Available)
- **Location**: `client/mem0-universal.sh`, `client/mem0-windows.ps1`, `client/mem0-fish.fish`
- **Status**: Cross-platform shell integration with authentication and sharing
- **Features**: Automatic command capture, multi-context support, user authentication

### ✅ Multi-User Support (Complete)
- **Status**: ✅ FULLY IMPLEMENTED - Complete authentication and user isolation
- **Current**: Full user-scoped context isolation with JWT authentication
- **Features**: User registration, login, secure token  # pragma: allowlist secret management, cross-user data isolation

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
./client/mem0 auth login --username youruser --password  # pragma: allowlist secret yourpass

# Start context
mem0_context_start my-project

# Work normally - commands captured automatically
```

**Windows (PowerShell):**
```powershell
# Load PowerShell integration
. .\client\mem0-windows.ps1

# Authenticate
.\client\mem0.exe auth login --username youruser --password  # pragma: allowlist secret yourpass

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

**Method 1: Terminal Integration (Recommended)**
```bash
# 1. Load shell integration in Zed's terminal
source /Users/asrajag/Workspace/mem0/client/mem0.zsh

# 2. Authenticate
./client/mem0 auth login --username youruser --password  # pragma: allowlist secret yourpass

# 3. Start context
./client/mem0 start zed-project-$(date +%s)

# 4. Work normally - commands captured automatically
```

**Method 2: MCP Server Integration**
```json
// Zed settings.json - Configure MCP server
{
    "language_models": {
        "mcp_servers": {
            "mem0": {
                "command": "/opt/homebrew/anaconda3/bin/python",
                "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
                "env": {
                    "MEM0_SERVER_URL": "http://127.0.0.1:13370"
                }
            }
        }
    },
    "terminal": {
        "shell": {
            "program": "zsh",
            "args": ["-l"]
        }
    }
}
```

**Method 3: Custom Tasks**
```json
// tasks.json in Zed
{
    "tasks": [
        {
            "label": "mem0 Remember",
            "command": "/Users/asrajag/Workspace/mem0/client/mem0",
            "args": ["remember", "${selectedText}", "--context", "${workspaceFolderBasename}"]
        },
        {
            "label": "mem0 Recall",
            "command": "/Users/asrajag/Workspace/mem0/client/mem0",
            "args": ["recall", "--context", "${workspaceFolderBasename}"]
        }
    ]
}
```

### 5. Cursor/Claude Integration

**Method 1: MCP Server Integration (Recommended)**
```json
// Cursor settings - Configure MCP server
{
    "mcp": {
        "servers": {
            "mem0": {
                "command": "/opt/homebrew/anaconda3/bin/python",
                "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
                "env": {
                    "MEM0_SERVER_URL": "http://127.0.0.1:13370"
                }
            }
        }
    }
}
```

**Method 2: Terminal Integration**
```bash
# In Cursor's terminal
source /Users/asrajag/Workspace/mem0/client/mem0.zsh
./client/mem0 auth login --username youruser --password  # pragma: allowlist secret yourpass
./client/mem0 start cursor-session-$(date +%s)
# Commands captured automatically
```

**Method 3: Custom AI Prompts**
Create custom prompts that leverage mem0:
```
Remember this code snippet: [SELECTION]
Context: ${workspaceName}
Command: ./client/mem0 remember "${selection}" --context ${workspaceName}
```

### 6. Warp Terminal Integration

**Setup (Recommended for Warp users):**
```bash
# 1. Add to your ~/.zshrc
echo 'source /Users/asrajag/Workspace/mem0/client/mem0.zsh' >> ~/.zshrc

# 2. Restart Warp or reload config
source ~/.zshrc

# 3. Authenticate
./client/mem0 auth login --username youruser --password  # pragma: allowlist secret yourpass

# 4. Start context
./client/mem0 start warp-session-$(date +%s)

# 5. Enable debug mode (optional)
export MEM0_DEBUG=1
```

**Warp-Specific Features:**
- Shell integration works seamlessly with Warp's command history
- Context switching preserved across Warp sessions
- Compatible with Warp's AI features and workflows
- Command capture works with Warp's autocomplete and suggestions

## User Authentication Implementation ✅ COMPLETE

**Status**: ✅ FULLY IMPLEMENTED - Complete JWT authentication system with user isolation

**Implemented Components:**

1. **Authentication Endpoints**:
```python
# Already implemented in server/main.py
@app.post("/auth/login")      # JWT token  # pragma: allowlist secret-based login
@app.post("/auth/register")   # User registration with bcrypt
@app.get("/auth/me")          # Get current user info
@app.post("/auth/logout")     # Token invalidation
```

2. **Session Management**:
```python
# Implemented in server/auth.py
def get_current_user(token  # pragma: allowlist secret: str = Depends(oauth2_scheme)):
    # Decode JWT, return user with proper isolation
    return decode_jwt_token  # pragma: allowlist secret(token)

def get_current_user_optional(token  # pragma: allowlist secret: Optional[str] = Depends(oauth2_scheme_optional)):
    # Optional authentication for public endpoints
    return decode_jwt_token  # pragma: allowlist secret(token) if token else None
```

3. **Client Authentication**:
```bash
# Complete CLI authentication support
./client/mem0 auth register --username user --email user@domain.com --password  # pragma: allowlist secret pass
./client/mem0 auth login --username user --password  # pragma: allowlist secret pass
./client/mem0 auth me                    # Show current user
./client/mem0 auth logout               # Logout and clear token  # pragma: allowlist secret

# Token stored securely in ~/.mem0/auth.json
# Automatic token  # pragma: allowlist secret refresh and validation
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
- Verify JWT token  # pragma: allowlist secret is valid: `./client/mem0 auth me`
- Check token  # pragma: allowlist secret expiration and refresh if needed
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
