# VS Code mem0 Recording Guide

## Quick Answer: mem0 is NOT automatically recording

Based on your VS Code conversation, mem0 is working but **not actively recording**. Here's how to enable it:

## Current Status
- ✅ MCP Server: Working (11 tools available)
- ✅ Database: SQLite with 17 existing memories
- ❌ Recording: No active contexts
- ❌ Auto-capture: Not enabled

## Enable Recording in VS Code

### Step 1: Start Recording Context
In VS Code chat, use the mem0 MCP tools:

```
@mem0 context_start CIP-Analysis
```

This creates and activates the "CIP-Analysis" context for recording.

### Step 2: Verify Recording Status
```
@mem0 get_ai_context
```

Should show your active context and memory counts.

### Step 3: Manual Memory Storage
```
@mem0 remember "OPCIGP vs OPCIGD3 analysis: OPCIGP more precomputed with cursor logic, OPCIGD3 more dynamic with runtime determination"
```

### Step 4: Test Recall
```
@mem0 recall "OPCIGP analysis"
```

## Why It Wasn't Recording

1. **Manual Activation Required**: mem0 follows "CCTV when turned on" philosophy
2. **Context Not Created**: The "CIP Analysis" context from your screenshot wasn't persisted
3. **No Auto-Capture**: VS Code conversations aren't automatically stored

## Database Issue Explained

The recall error you saw:
```
"There was an error retrieving memories from mem0 for the context 'CIP Analysis' due to a database column issue"
```

This happened because:
- Context "CIP Analysis" was started but not properly saved
- Recall tried to query non-existent context
- Database schema mismatch between expected and actual structure

## Working Configuration

Your VS Code MCP configuration is correct:
```json
{
  "mcp.servers": {
    "mem0": {
      "command": "/opt/homebrew/anaconda3/bin/python3.11",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "cwd": "/Users/asrajag/Workspace/mem0",
      "env": {
        "MEM0_DATABASE_URL": "postgresql://mem0user:mem0pass@  # pragma: allowlist secretlocalhost:5432/mem0db",
        "MEM0_JWT_SECRET": "your-jwt-secret"
      }
    }
  }
}
```

## Test Workflow

1. **Start Context**: `@mem0 context_start ProjectAnalysis`
2. **Store Memory**: `@mem0 remember "Key insight about project"`
3. **Check Status**: `@mem0 get_ai_context`
4. **Recall Info**: `@mem0 recall "project insight"`
5. **Stop Recording**: `@mem0 context_stop`

## Auto-Recording Setup (Future Enhancement)

For automatic conversation capture, you would need:
- VS Code extension enhancement to auto-capture chat messages
- Background process to monitor VS Code activity
- Configuration to specify which conversations to record

Currently, mem0 requires **explicit activation** for each recording session.

## Database Status

- **Type**: PostgreSQL only (no SQLite support)
- **Connection**: Configured via MEM0_DATABASE_URL environment variable
- **Tables**: All required tables present
- **Memories**: Stored in PostgreSQL database
- **Contexts**: No active recording contexts currently

## Next Steps

1. Use `@mem0 context_start <name>` to begin recording
2. Manually store important insights with `@mem0 remember`
3. Use `@mem0 recall` to retrieve stored information
4. Consider implementing auto-capture for seamless recording
