---
title: SPEC-130: Terminal/CLI Auto Context Capture
---

# SPEC-130: Terminal/CLI Auto Context Capture

**Status:** ⚠️ **Partially Implemented** (60% - Core functionality exists)
**Owner:** Platform Team
**Last Updated:** January 2025

> **Automatically captures terminal/CLI commands and context for memory storage and AI context building.**

## 1. Overview

SPEC-130 provides automatic capture of terminal commands and CLI interactions, enabling the Ninaivalaigal platform to build context-aware memories from developer workflows. This includes shell hooks, IDE integration, and automatic context detection.

### Key Features

- **Shell Hooks**: Automatic command capture via zsh/bash hooks
- **Camera Off Protection**: Privacy controls via token/context checks
- **Context-Aware**: Commands grouped by active context
- **Secret Filtering**: Automatic filtering of sensitive commands
- **IDE Integration**: VS Code workspace context detection
- **AutoRecorder**: CCTV-style continuous recording

## 2. Architecture

### 2.1 Components

```
┌─────────────────────────────────────────────────────────┐
│              Terminal/CLI Auto Context Capture          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Shell Hooks │  │ AutoRecorder │  │ IDE Integration│ │
│  │ (zsh/bash)  │  │  (CCTV)      │  │  (VS Code)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            │                            │
│                    ┌───────▼────────┐                  │
│                    │  Memory Service │                  │
│                    │   (API Endpoint)│                  │
│                    └─────────────────┘                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

1. **Command Execution**: User runs command in terminal
2. **Hook Trigger**: Shell hook captures command metadata
3. **Filtering**: Secret/sensitive commands filtered
4. **Context Check**: Verify active context and auth token
5. **API Call**: Send to memory service (non-blocking)
6. **Storage**: Command stored as memory entry

## 3. Implementation

### 3.1 Shell Hooks

**Location**: `adapters/shell_hooks/store_memory.sh`

**Features**:
- ✅ zsh and bash support
- ✅ Non-blocking background capture
- ✅ Camera off protection (token/context checks)
- ✅ Secret filtering (password, token, key commands)
- ✅ Context-aware grouping
- ✅ User control commands

**Installation**:

```bash
# Add to ~/.zshrc or ~/.bashrc
source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh

# Set environment variables
export NINA_MEMORY_SERVICE_URL="http://localhost:13393"
export NINA_AUTH_TOKEN="your-jwt-token-here"
export NINA_CONTEXT="your-active-context"
export NINA_CAPTURE_ENABLED=true
```

**User Commands**:

```bash
nina_capture_on      # Enable capture
nina_capture_off     # Disable capture (camera off)
nina_context <name>  # Set active context
nina_status          # Show current configuration
```

**Filtered Commands**:
- Internal shell commands (`_nina_*`, `source*`, `export*`, `alias*`)
- Password/secret commands (`*password*`, `*secret*`, `*token*`, `*key*`)

### 3.2 AutoRecorder

**Location**: `services/*/lib/auto_recording.py`

**Features**:
- ✅ CCTV-style continuous recording
- ✅ Automatic recording when contexts are active
- ✅ Auto-save loop (30-second intervals)
- ✅ Recording buffer management
- ✅ Start/stop recording functionality
- ✅ Token protection integration

**Usage**:

```python
from lib.auto_recording import AutoRecorder

recorder = AutoRecorder()
recorder.start_recording(context_id="my-context")
# ... commands are automatically recorded
recorder.stop_recording()
```

### 3.3 VS Code Integration

**Location**: `specs/130-terminal-cli-auto-context/vs-code-integration/`

**Features**:
- ✅ Workspace context detection
- ✅ Memory recall within IDE
- ✅ Context isolation per workspace
- ✅ Automatic context switching

**Configuration**:

```json
{
  "ninaivalaigal.context": "workspace-context",
  "ninaivalaigal.autoCapture": true
}
```

## 4. API Contracts

### 4.1 Memory Storage Endpoint

**Endpoint**: `POST /memory`

**Request**:

```json
{
  "type": "terminal_command",
  "source": "shell_hook",
  "data": {
    "context": "my-context",
    "command": "git commit -m 'feat: add feature'",
    "exit_code": 0,
    "working_directory": "/path/to/project",
    "timestamp": "2025-01-15T10:30:00Z",
    "shell": "/bin/zsh"
  }
}
```

**Response**:

```json
{
  "id": "memory-id",
  "message": "Memory stored successfully"
}
```

**Error Responses**:

```json
{
  "message": "Skipped capture - no active context (camera off)",
  "id": null
}
```

### 4.2 Context Detection

**Endpoint**: `GET /contexts`

**Response**:

```json
[
  {
    "id": "context-id",
    "name": "my-context",
    "is_active": true
  }
]
```

## 5. Security & Privacy

### 5.1 Camera Off Protection

- **Token Check**: No capture if `NINA_AUTH_TOKEN` is not set
- **Context Check**: No capture if `NINA_CONTEXT` is not set
- **User Control**: `nina_capture_off` command disables capture

### 5.2 Secret Filtering

Automatic filtering of:
- Password commands
- Secret commands
- Token commands
- Key commands
- Internal shell commands

### 5.3 Data Redaction

All captured data is processed through DLP (Data Loss Prevention) system:
- Email addresses redacted
- Phone numbers redacted
- Credit card numbers redacted
- API keys redacted
- SSNs redacted

## 6. Configuration

### 6.1 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|----------|----------|
| `NINA_MEMORY_SERVICE_URL` | Memory service endpoint | `http://localhost:13393` | No |
| `NINA_AUTH_TOKEN` | JWT authentication token | - | Yes (for capture) |
| `NINA_CONTEXT` | Active context name | `default` | Yes (for capture) |
| `NINA_CAPTURE_ENABLED` | Enable/disable capture | `true` | No |
| `NINA_QUIET` | Suppress welcome message | `false` | No |

### 6.2 Shell Configuration

**zsh** (`~/.zshrc`):

```bash
source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh
export NINA_AUTH_TOKEN="your-token"
export NINA_CONTEXT="my-context"
```

**bash** (`~/.bashrc`):

```bash
source /path/to/ninaivalaigal/adapters/shell_hooks/store_memory.sh
export NINA_AUTH_TOKEN="your-token"
export NINA_CONTEXT="my-context"
```

## 7. Testing

### 7.1 Manual Testing

```bash
# Enable capture
nina_capture_on

# Set context
nina_context test-context

# Run a command
ls -la

# Check status
nina_status

# Disable capture
nina_capture_off
```

### 7.2 Automated Testing

Test cases should verify:
- ✅ Command capture works
- ✅ Secret filtering works
- ✅ Camera off protection works
- ✅ Context switching works
- ✅ Non-blocking capture works
- ✅ API integration works

## 8. Integration Points

### 8.1 Memory Service

- **Endpoint**: `/memory` (POST)
- **Authentication**: Bearer token required
- **Format**: JSON payload with command metadata

### 8.2 Context System

- **Integration**: Active context detection
- **Switching**: Automatic context switching
- **Isolation**: Context-based command grouping

### 8.3 DLP System

- **Integration**: Automatic data redaction
- **Filtering**: Secret detection and filtering
- **Compliance**: GDPR/security compliance

## 9. Future Enhancements

### 9.1 Planned Features

- [ ] Advanced context detection (beyond manual switching)
- [ ] Command pattern analysis
- [ ] Context-aware command suggestions
- [ ] Integration with additional IDEs (JetBrains, etc.)
- [ ] Batch command processing
- [ ] Command history analysis
- [ ] Workflow pattern recognition

### 9.2 CLI Tool

- [ ] Comprehensive CLI tool (beyond shell hooks)
- [ ] Command replay functionality
- [ ] Context management commands
- [ ] Capture statistics and analytics

## 10. Troubleshooting

### 10.1 Commands Not Captured

**Check**:
1. `NINA_CAPTURE_ENABLED` is set to `true`
2. `NINA_AUTH_TOKEN` is set
3. `NINA_CONTEXT` is set
4. Memory service is accessible
5. Command is not filtered (password/secret)

### 10.2 Performance Issues

**Solutions**:
- Capture is non-blocking (background process)
- Commands are filtered before API call
- Use `nina_capture_off` if needed

### 10.3 Privacy Concerns

**Solutions**:
- Use `nina_capture_off` to disable capture
- Unset `NINA_AUTH_TOKEN` to disable capture
- Unset `NINA_CONTEXT` to disable capture
- Secret commands are automatically filtered

## 11. References

- **Shell Hooks**: `adapters/shell_hooks/store_memory.sh`
- **AutoRecorder**: `services/*/lib/auto_recording.py`
- **VS Code Integration**: `specs/130-terminal-cli-auto-context/vs-code-integration/`
- **Comprehensive Analysis**: `docs/spec-analysis/SPEC_130_COMPREHENSIVE_ANALYSIS.md`
- **Related SPECs**: SPEC-001 (Core Memory System), SPEC-007 (Context System)

## 12. Taiga Stories

The following Taiga stories have been created for SPEC-130:

**Phase 1: Foundation**
- **US#1024**: CLI-CAP-001: Terminal Context Capture Foundation

**Phase 2: IDE Integration**
- **US#1036**: CLI-CAP-002: IDE Integration (VS Code & JetBrains)

**Phase 3: Processing**
- **US#1028**: CLI-CAP-003: Context Processing & Storage

**Documentation & Enhancements**
- **US#693**: SPEC-130: Terminal/CLI Auto Context Capture - Documentation & Enhancements

All stories are tagged with `spec-130` and are ready for implementation.
