# Ninaivalaigal JetBrains Plugin

Native ninaivalaigal integration for JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm, etc.).
Connects to ninaivalaigal's native MCP server for context-aware memory management.

## Features

- **Context Management**: Auto-detect project context or set explicitly
- **Remember/Recall**: Capture and retrieve memories with keyboard shortcuts
- **Multi-Project Support**: Isolated contexts per project
- **Server Integration**: Connects to local or remote mem0 server
- **IDE Integration**: Tool window, context menus, and actions

## Installation

### Option 1: Build from Source
```bash
cd jetbrains-plugin
./gradlew buildPlugin
# Install the generated .zip from build/distributions/
```

### Option 2: JetBrains Marketplace (Future)
```bash
# Will be available once published
# Install directly from IDE: Settings → Plugins → Marketplace → Search "mem0"
```

## Setup

1. **Start mem0 server:**
   ```bash
   cd /path/to/mem0
   ./manage.sh start
   ```

2. **Configure plugin:**
   - Go to: Settings → Tools → Ninaivalaigal
   - Set MCP server path (default: `server/run_mcp_server.py` relative to ninaivalaigal root)
   - Optionally set default context and enable/disable auto-detect

## Usage

### Keyboard Shortcuts
- **Ctrl+Shift+M**: Remember selected text/code to ninaivalaigal
- **Ctrl+Shift+R**: Recall memories from ninaivalaigal for current context

### Context Menu
- Right-click in editor → "Remember Selection"
- Tools menu → Ninaivalaigal actions

### Context Management
```bash
# Via Tools menu:
- Start new ninaivalaigal context
- List all contexts
- Switch between contexts (via settings)
```

## Configuration

### IDE Settings (Settings → Tools → Ninaivalaigal)
```
MCP Server Path: /path/to/ninaivalaigal/server/run_mcp_server.py
Default Context: my-project (optional, if auto-detect disabled)
Auto-detect Context: ✓ (uses project folder name)
```

### Per-Project Context
- Plugin auto-detects context from project folder name
- Override with explicit context in settings
- Each project gets isolated memory

## Examples

### Remember Code Snippet
```java
// Select this code and press Ctrl+Shift+M
public class UserService {
    public User authenticate(String token) {
        // JWT validation logic
        return user;
    }
}
```

### Remember Design Decision
```
Tools → mem0 → Remember
"Using JWT tokens for authentication instead of sessions for better scalability"
```

### Recall Context
```
Ctrl+Shift+R shows:
- "Added JWT authentication"
- "Refactored UserService class"
- "Fixed token validation bug"
```

## Development

### Build Plugin
```bash
./gradlew buildPlugin
# Output: build/distributions/mem0-jetbrains-0.1.0.zip
```

### Run in Development
```bash
./gradlew runIde
# Launches IDE with plugin installed
```

### Publish to Marketplace
```bash
export PUBLISH_TOKEN=your_token
./gradlew publishPlugin
```

## Architecture

```
JetBrains Plugin
    ↓ (Process execution)
mem0 CLI
    ↓ (HTTP API)
mem0 Server
    ↓ (Database)
SQLite/PostgreSQL
```

## Supported IDEs

- IntelliJ IDEA (Community & Ultimate)
- PyCharm (Community & Professional)
- WebStorm
- PhpStorm
- RubyMine
- CLion
- GoLand
- DataGrip
- Rider
- Android Studio

## Troubleshooting

### Plugin Not Working
1. Check ninaivalaigal MCP server: Verify `server/run_mcp_server.py` exists and is executable
2. Verify MCP server path in plugin settings
3. Check IDE logs: Help → Show Log in Finder
4. Ensure Python 3 is available in PATH

### Context Issues
1. Manually set context: Tools → Ninaivalaigal → Start Context
2. Verify project folder name detection (if auto-detect enabled)
3. Check default context in settings

### Server Connection
1. Confirm MCP server path in settings points to ninaivalaigal server
2. Ensure ninaivalaigal server is running and accessible
3. Check Python environment and dependencies

## Distribution

### For Teams
```bash
# Build plugin
./gradlew buildPlugin

# Share build/distributions/mem0-jetbrains-0.1.0.zip
# Team members install: Settings → Plugins → Install from disk
```

### Requirements for Users
- JetBrains IDE (2022.1+)
- mem0 server running (local or remote)
- Java 11+ (usually bundled with IDE)

## License

Same as mem0 project license.
