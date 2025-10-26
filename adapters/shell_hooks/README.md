# Shell Hooks for Ninaivalaigal Memory Capture

**Purpose**: Automatic terminal command capture for AI context persistence
**SPEC**: SPEC-001 FR-010 (Shell Integration for Auto-Capture)
**Status**: Production Ready

---

## Overview

Shell hooks enable automatic capture of terminal commands to Ninaivalaigal's memory system, providing persistent context for AI agents and development workflows.

### Features

- ✅ **Auto-Capture**: Commands automatically recorded with metadata
- ✅ **Camera Off Protection**: Capture disabled when no context active
- ✅ **Multi-Shell Support**: Works with zsh and bash
- ✅ **Non-Blocking**: Background capture doesn't slow down terminal
- ✅ **Context-Aware**: Commands grouped by active context
- ✅ **Secret Filtering**: Automatically skips sensitive commands
- ✅ **User Control**: Easy enable/disable and context switching

---

## Quick Start

### 1. Prerequisites

```bash
# Ensure Nina stack is running
make stack-up

# Verify memory service is healthy
curl http://localhost:13393/health
```

### 2. Obtain Authentication Token

```bash
# Login to get JWT token
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"  # pragma: allowlist secret
  }' | jq -r '.access_token'

# Export token
export NINA_AUTH_TOKEN="<your-jwt-token>"
```

### 3. Configure Environment

Add to your shell RC file (`~/.zshrc` or `~/.bashrc`):

```bash
# Nina Memory Capture Configuration
export NINA_MEMORY_SERVICE_URL="http://localhost:13393"
export NINA_AUTH_TOKEN="<your-jwt-token>"
export NINA_CONTEXT="default"
export NINA_CAPTURE_ENABLED=true

# Source the hook script
source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh
```

### 4. Reload Shell

```bash
# For zsh
source ~/.zshrc

# For bash
source ~/.bashrc
```

---

## Usage

### Basic Commands

#### View Status
```bash
nina_status
```
Output:
```
Nina Memory Shell Hook Status:
  Capture Enabled: true
  Active Context: default
  Memory Service: http://localhost:13393
  Auth Token: <set>
  Shell: /bin/zsh
```

#### Switch Context
```bash
nina_context project-alpha
# Output: 📁 Nina context set to: project-alpha
```

#### Disable Capture (Camera Off)
```bash
nina_capture_off
# Output: 🔒 Nina memory capture disabled (camera off)
```

#### Enable Capture
```bash
nina_capture_on
# Output: ✅ Nina memory capture enabled
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NINA_MEMORY_SERVICE_URL` | `http://localhost:13393` | Memory service endpoint |
| `NINA_AUTH_TOKEN` | *(required)* | JWT authentication token |
| `NINA_CONTEXT` | `default` | Active memory context |
| `NINA_CAPTURE_ENABLED` | `true` | Enable/disable capture |
| `NINA_QUIET` | `false` | Suppress welcome message |

### Token Management

**Security Best Practice**: Store tokens securely

```bash
# Option 1: Use a token management file (gitignored)
echo "export NINA_AUTH_TOKEN='your-token-here'" > ~/.nina/auth_token
source ~/.nina/auth_token

# Option 2: Use system keychain (macOS)
security add-generic-password \
  -a "$USER" \
  -s "nina_auth_token" \
  -w "your-token-here"

# Retrieve from keychain in RC file
export NINA_AUTH_TOKEN=$(security find-generic-password \
  -a "$USER" \
  -s "nina_auth_token" \
  -w 2>/dev/null)
```

---

## How It Works

### Command Flow

```
1. User executes command in terminal
   ↓
2. Shell hook captures command + metadata
   ↓
3. Background process sends to memory service
   ↓
4. Memory service stores with context association
   ↓
5. AI agents can recall commands by context
```

### Captured Metadata

Each command is stored with:
- Command text
- Exit code (success/failure)
- Working directory
- Timestamp (UTC)
- Shell type
- Context name

### Example Payload

```json
{
  "type": "terminal_command",
  "source": "shell_hook",
  "data": {
    "context": "project-alpha",
    "command": "npm test",
    "exit_code": 0,
    "working_directory": "/Users/dev/project-alpha",
    "timestamp": "2025-10-25T20:35:00Z",
    "shell": "/bin/zsh"
  }
}
```

---

## Security

### Command Filtering

Commands containing these keywords are **automatically skipped**:
- `password`, `secret`, `token`, `key`
- Internal shell commands (`source`, `export`, `alias`)
- Nina hook commands (`_nina_*`)

### Camera Off Protection

Capture is **disabled** when:
- `NINA_CAPTURE_ENABLED=false`
- `NINA_AUTH_TOKEN` is not set
- `NINA_CONTEXT` is empty

### Token Security

⚠️ **Never commit tokens to git**

```bash
# Add to .gitignore
echo "~/.nina/auth_token" >> .gitignore
```

---

## Troubleshooting

### Commands Not Capturing

**Check status**:
```bash
nina_status
```

**Common issues**:
1. **No auth token**: `export NINA_AUTH_TOKEN="<token>"`
2. **Capture disabled**: `nina_capture_on`
3. **No context**: `nina_context default`
4. **Memory service down**: `curl http://localhost:13393/health`

### View Captured Commands

```bash
# Using memory service API
curl -X GET "http://localhost:13393/memory?context=default" \
  -H "Authorization: Bearer $NINA_AUTH_TOKEN"
```

### Debug Mode

Enable debug logging:
```bash
# Temporary debug
export NINA_DEBUG=true

# View capture attempts
tail -f ~/.nina/capture.log  # If logging enabled
```

---

## Performance

### Impact

- **Capture Latency**: <5ms per command (background)
- **Terminal Lag**: None (async execution)
- **Memory Overhead**: ~1KB per command
- **Network**: Single POST request per command

### Optimization

For high-frequency commands, consider:
```bash
# Batch capture every N seconds
export NINA_BATCH_INTERVAL=10

# Reduce captured metadata
export NINA_MINIMAL_CAPTURE=true
```

---

## Examples

### Development Workflow

```bash
# Start a new feature
nina_context feature/user-auth

# Work on feature
git checkout -b feature/user-auth
npm install
npm test
git commit -m "Add user auth"

# AI can recall all these commands in context "feature/user-auth"
```

### Debug Session

```bash
# Enable capture for debugging
nina_context debug/memory-leak
nina_capture_on

# Debug commands captured
valgrind ./app
gdb ./app
strace ./app

# Disable after debugging
nina_capture_off
```

### Multi-Project Context

```bash
# Switch between projects
nina_context project-A
cd ~/projects/project-A
make build

nina_context project-B
cd ~/projects/project-B
cargo build

# Each project's commands isolated by context
```

---

## Integration with SPEC-001

### Functional Requirements Satisfied

| FR | Requirement | Status |
|----|-------------|--------|
| FR-001 | Auto-capture terminal commands | ✅ Complete |
| FR-004 | Start/stop recording contexts | ✅ `nina_capture_on/off` |
| FR-005 | Camera off protection | ✅ Token/context checks |
| FR-010 | Shell integration | ✅ zsh/bash hooks |

### Architecture Integration

```
Shell Hook (store_memory.sh)
    ↓
Memory Service (Rust, port 13393)
    ↓
PostgreSQL 15 + pgvector
    ↓
Graph Intelligence (Apache AGE)
    ↓
AI Context Engine
```

---

## Maintenance

### Update Token

```bash
# Obtain new token
NEW_TOKEN=$(curl -X POST http://localhost:13390/auth/refresh \
  -H "Authorization: Bearer $NINA_AUTH_TOKEN" \
  | jq -r '.access_token')

# Update environment
export NINA_AUTH_TOKEN="$NEW_TOKEN"
```

### Uninstall

```bash
# Remove from RC file
# Remove these lines from ~/.zshrc or ~/.bashrc:
# - source /path/to/store_memory.sh
# - NINA_* environment variables

# Reload shell
source ~/.zshrc  # or ~/.bashrc
```

---

## Support

**Documentation**: `/specs/001-core-memory-system/`
**Issues**: File issue with tag `shell-hooks`
**Tests**: `tests/adapters/test_shell_hooks.sh`

---

## Changelog

### v1.0.0 (2025-10-25)
- ✅ Initial release
- ✅ zsh and bash support
- ✅ Auto-capture with metadata
- ✅ Camera off protection
- ✅ Secret filtering
- ✅ User control commands
- ✅ SPEC-001 FR-010 implementation
