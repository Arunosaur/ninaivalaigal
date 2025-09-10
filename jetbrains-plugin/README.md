# mem0 JetBrains Plugin

A memory layer for JetBrains IDEs (IntelliJ IDEA, PyCharm, WebStorm, etc.) that integrates with the mem0 system.

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
   - Go to: Settings → Tools → mem0
   - Set server URL (default: `http://127.0.0.1:13370`)
   - Optionally set mem0 CLI path and default context

## Usage

### Keyboard Shortcuts
- **Ctrl+Shift+M**: Remember selected text/code
- **Ctrl+Shift+R**: Recall memories for current context

### Context Menu
- Right-click in editor → "Remember Selection"
- Tools menu → mem0 actions

### Tool Window
- View → Tool Windows → mem0
- Shows current context and recent memories

### Context Management
```bash
# Via Tools menu or tool window:
- Start new context
- Switch between contexts  
- List all contexts
```

## Configuration

### IDE Settings (Settings → Tools → mem0)
```
Server URL: http://127.0.0.1:13370
mem0 CLI Path: /path/to/mem0/client/mem0 (auto-detected)
Default Context: my-project (optional)
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
1. Check mem0 server: `curl http://127.0.0.1:13370/`
2. Verify mem0 CLI path in settings
3. Check IDE logs: Help → Show Log in Finder

### Context Issues
1. Check current context in tool window
2. Manually set context: Tools → mem0 → Start Context
3. Verify project folder name detection

### Server Connection
1. Confirm server URL in settings
2. Test network connectivity
3. Check firewall settings

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
