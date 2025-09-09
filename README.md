# mem0 - Universal Memory Layer for AI Agents

mem0 is a system designed to provide a universal, cross-platform, and shareable memory layer for AI agents and human developers. It captures the iterative development process and transforms it into structured, machine-readable data for automation and team collaboration.

## Architecture

### Core Components

- **Server**: FastAPI-based headless API server (Python)
- **Client**: CLI tool with shell integration for command capture
- **VS Code Extension**: IDE integration for development workflows
- **Data Storage**: JSON file-based persistence with context management

### Key Features

- **Command Capture**: Automatic shell command recording via zsh integration
- **Context Management**: Session-based memory organization
- **Performance Optimized**: Intelligent caching to minimize API calls
- **Debug Support**: Comprehensive logging for troubleshooting
- **Cross-Platform**: Works across different development environments

## Quick Start

### 1. Start the Server

```bash
./manage.sh start
```

The server will start on `http://127.0.0.1:13370`

### 2. Start Recording Session

```bash
./client/mem0 context start my-session
```

### 3. Enable Shell Integration

```bash
source client/mem0.zsh
```

### 4. Optional: Enable Debug Logging

```bash
export MEM0_DEBUG=1
```

### 5. View Captured Memories

```bash
./client/mem0 recall --context my-session
```

### 6. Stop Recording

```bash
./client/mem0 context stop
```

## CLI Commands

### Context Management
- `./client/mem0 context start <name>` - Start recording to a context
- `./client/mem0 context stop` - Stop current recording session
- `./client/mem0 context active` - Show active recording context

### Memory Operations
- `./client/mem0 remember '<json>'` - Store a memory entry
- `./client/mem0 recall [--context <name>]` - Retrieve memories
- `./client/mem0 export <filename> [--context <name>]` - Export memories to file

### Server Management
- `./manage.sh start` - Start the mem0 server
- `./manage.sh stop` - Stop the mem0 server

## Shell Integration Features

### Performance Optimization
- **Context Caching**: Reduces API calls by caching active context for 30 seconds
- **Background Processing**: Command capture runs asynchronously
- **Smart Filtering**: Only captures commands when recording is active

### Cache Management
- `mem0_clear_cache` - Clear the context cache manually
- Cache automatically expires after 30 seconds
- Cache is updated when context changes

### Debug Mode
Enable debug logging to troubleshoot shell integration:

```bash
export MEM0_DEBUG=1
source client/mem0.zsh
```

Debug output shows:
- Hook triggers
- Cache hits/misses
- API responses
- Payload construction
- Command submission status

## VS Code Extension

The VS Code extension provides IDE integration through a chat participant.

### Setup
1. Configure the project root in VS Code settings:
   ```json
   {
     "mem0.projectRoot": "/absolute/path/to/mem0/project"
   }
   ```

2. Use the `@mem0` chat participant in VS Code

### Available Commands
- `@mem0 remember <data>` - Store a memory
- `@mem0 recall` - Retrieve memories
- `@mem0 observe` - Observe chat history

## Configuration

### Environment Variables
- `MEM0_PORT` - Server port (default: 13370)
- `MEM0_DEBUG` - Enable debug logging (set to 1)

### Shell Integration Settings
- `MEM0_CACHE_TTL` - Context cache duration in seconds (default: 30)

## Development

### Dependencies

**Server:**
- FastAPI
- Uvicorn

**Client:**
- requests

**VS Code Extension:**
- TypeScript
- VS Code API

### Testing

Run the test suite:

```bash
# Basic functionality test
./tests/run_test.sh

# Context management test
./tests/run_context_test.sh

# Session recording test
./tests/run_session_test.sh
```

### Project Structure

```
mem0/
├── server/           # FastAPI server
│   ├── main.py      # Server implementation
│   └── requirements.txt
├── client/          # CLI tool and shell integration
│   ├── mem0         # Python CLI script
│   ├── mem0.zsh     # Zsh integration
│   └── requirements.txt
├── vscode-client/   # VS Code extension
│   ├── src/
│   └── package.json
├── tests/           # Test scripts
├── docs/           # Documentation
│   ├── STATE.md    # Development state tracking
│   └── VISION.md   # Project vision and goals
└── manage.sh       # Server management script
```

## Vision

mem0 transforms the messy, iterative development process into structured data that can be used for:

1. **Automation Generation**: Convert development sessions into Ansible playbooks
2. **Team Collaboration**: Share development context across team members
3. **AI Agent Memory**: Provide persistent memory for AI development assistants

## Contributing

The system is designed with three key principles:

1. **From Developer to Automation**: Capture development workflows for automation
2. **From Individual to Team**: Scale from personal use to team collaboration
3. **From UI to CLI**: API-first design with thin client interfaces

## License

[Add your license information here]
