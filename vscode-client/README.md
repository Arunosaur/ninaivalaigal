# mem0 VS Code Extension

A memory layer for your development environment that integrates with VS Code chat.

## Installation & Setup

### For Personal Use (Local Development)

1. **Install the extension:**
   ```bash
   cd vscode-client
   npm install
   npm run package
   code --install-extension mem0-vscode-0.1.0.vsix
   ```

2. **Start mem0 server:**
   ```bash
   # In your mem0 project root
   ./manage.sh start
   ```

3. **Use in VS Code chat:**
   - Open VS Code chat panel (Ctrl+Shift+I or Cmd+Shift+I)
   - Type `@mem0` commands

### For Distribution to Others

**Prerequisites for users:**
1. **mem0 server running** - Users need their own mem0 installation
2. **Network access** - Extension connects to `http://127.0.0.1:13370` by default

**Distribution options:**

#### Option 1: VS Code Marketplace (Recommended)
```bash
# Publish to marketplace (requires publisher account)
npm install -g vsce
vsce publish
```

#### Option 2: Direct .vsix Distribution
```bash
# Build extension
npm run package

# Share mem0-vscode-0.1.0.vsix file
# Users install with: code --install-extension mem0-vscode-0.1.0.vsix
```

#### Option 3: Standalone Installation Script
Create `install-mem0-vscode.sh`:
```bash
#!/bin/bash
# Download and install mem0 + VS Code extension
git clone https://github.com/your-org/mem0.git
cd mem0/vscode-client
npm install && npm run package
code --install-extension mem0-vscode-0.1.0.vsix
echo "mem0 VS Code extension installed!"
```

## Usage

### Context Management
```bash
# In VS Code chat:
@mem0 context start my-project     # Start new context
@mem0 context switch frontend      # Switch to existing context
@mem0 context list                 # List all contexts
```

### Memory Operations
```bash
@mem0 remember "Added user authentication with JWT"
@mem0 recall                       # Show recent memories
@mem0 observe                      # View chat history
```

### Configuration Options

#### Workspace Settings (.vscode/settings.json)
```json
{
  "mem0.context": "my-explicit-context",
  "mem0.projectRoot": "/custom/path/to/mem0",
  "mem0.serverUrl": "http://remote-server:13370"
}
```

#### Context Priority (highest to lowest):
1. `@mem0 context start <name>` - Explicit command
2. `mem0.context` setting - Workspace setting
3. Auto-detected from workspace folder name
4. Default: `vscode-session`

## For Distributed Use

### Server Setup for Teams
```bash
# Each user needs mem0 server running
git clone https://github.com/your-org/mem0.git
cd mem0
./manage.sh start

# Or use Docker
docker run -p 13370:13370 mem0-server
```

### Multi-User Considerations
- **Current limitation**: No authentication (single-user only)
- **Workaround**: Separate server instances per user/team
- **Future**: JWT/OAuth authentication planned

### Network Configuration
```json
// For remote servers
{
  "mem0.serverUrl": "https://mem0.company.com"
}
```

## Development

### Build Commands
```bash
npm install          # Install dependencies
npm run compile      # Compile TypeScript
npm run watch        # Watch mode for development
npm run package      # Build production .vsix
```

### Testing
```bash
# Test extension locally
code --extensionDevelopmentPath=. --new-window

# Test with different contexts
@mem0 context start test-context
@mem0 remember "Test memory"
@mem0 recall
```

## Troubleshooting

### Extension Not Working
1. Check mem0 server is running: `curl http://127.0.0.1:13370/`
2. Verify extension is installed: VS Code → Extensions → Search "mem0"
3. Check VS Code Developer Console for errors

### Context Issues
```bash
# Check available contexts
@mem0 context list

# Reset to workspace context
# Remove mem0.context from settings.json
```

### Server Connection Issues
```bash
# Check server URL in settings
# Default: http://127.0.0.1:13370
# Verify firewall/network access
```

## Architecture

```
VS Code Extension
    ↓ (HTTP API calls)
mem0 Server (FastAPI)
    ↓ (Database queries)
SQLite/PostgreSQL Database
```

The extension is a thin client that:
1. Auto-detects project context from workspace
2. Passes commands to mem0 CLI/server
3. Displays results in VS Code chat interface

## Security Notes

- **Local use**: Secure (localhost communication)
- **Team use**: Requires proper server authentication
- **Public distribution**: Users need their own mem0 server

## License

Same as mem0 project license.
