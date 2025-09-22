"""
MCP Resources for ninaivalaigal
Extracted from monolithic mcp_server.py for better organization

This addresses external code review feedback:
- Break down monolithic files (mcp_server.py 929 lines → focused modules)
- Improve code organization and maintainability
"""

import json

from .server import get_initialized_components, mcp

# Try to import MCP types, fallback if not available
try:
    from mcp.types import Resource, TextResourceContents
except ImportError:

    class Resource:
        def __init__(self, uri, name, description, mimeType, text):
            self.uri = uri
            self.name = name
            self.description = description
            self.mimeType = mimeType
            self.text = text

    class TextResourceContents:
        def __init__(self, text):
            self.text = text


# Get initialized components
components = get_initialized_components()
db = components["db"]
DEFAULT_USER_ID = components["DEFAULT_USER_ID"]


@mcp.resource("ninaivalaigal://contexts")
async def list_all_contexts() -> Resource:
    """Provide list of all contexts as a resource"""
    try:
        contexts = db.get_all_contexts(user_id=DEFAULT_USER_ID)

        context_data = {
            "total_contexts": len(contexts),
            "contexts": contexts,
            "user_id": DEFAULT_USER_ID,
        }

        return Resource(
            uri="ninaivalaigal://contexts",
            name="All Contexts",
            description="Complete list of all available contexts",
            mimeType="application/json",
            text=json.dumps(context_data, indent=2),
        )
    except Exception as e:
        return Resource(
            uri="ninaivalaigal://contexts",
            name="All Contexts (Error)",
            description="Error retrieving contexts",
            mimeType="application/json",
            text=json.dumps({"error": str(e)}, indent=2),
        )


@mcp.resource("ninaivalaigal://context/{context_name}")
async def get_context_memories(context_name: str) -> Resource:
    """Provide all memories for a specific context"""
    try:
        memories = db.get_memories(context_name, user_id=DEFAULT_USER_ID)

        memory_data = {
            "context": context_name,
            "total_memories": len(memories),
            "memories": memories,
            "user_id": DEFAULT_USER_ID,
        }

        return Resource(
            uri=f"ninaivalaigal://context/{context_name}",
            name=f"Context: {context_name}",
            description=f"All memories in context '{context_name}'",
            mimeType="application/json",
            text=json.dumps(memory_data, indent=2),
        )
    except Exception as e:
        return Resource(
            uri=f"ninaivalaigal://context/{context_name}",
            name=f"Context: {context_name} (Error)",
            description="Error retrieving context memories",
            mimeType="application/json",
            text=json.dumps({"error": str(e), "context": context_name}, indent=2),
        )


@mcp.resource("ninaivalaigal://recent")
async def get_recent_memories() -> Resource:
    """Provide recently added memories across all contexts"""
    try:
        recent_memories = db.get_recent_memories(limit=50, user_id=DEFAULT_USER_ID)

        recent_data = {
            "total_recent": len(recent_memories),
            "limit": 50,
            "memories": recent_memories,
            "user_id": DEFAULT_USER_ID,
        }

        return Resource(
            uri="ninaivalaigal://recent",
            name="Recent Memories",
            description="Recently added memories across all contexts",
            mimeType="application/json",
            text=json.dumps(recent_data, indent=2),
        )
    except Exception as e:
        return Resource(
            uri="ninaivalaigal://recent",
            name="Recent Memories (Error)",
            description="Error retrieving recent memories",
            mimeType="application/json",
            text=json.dumps({"error": str(e)}, indent=2),
        )


@mcp.resource("ninaivalaigal://approval-workflow")
async def approval_workflow_guide() -> Resource:
    """Documentation for cross-team memory approval workflow"""
    content = """
# Cross-Team Memory Approval Workflow

## Overview
The approval workflow enables secure cross-team memory sharing with proper authorization and audit trails.

## Process Flow

### 1. Request Cross-Team Access
Use the `cross_team_share_memory` tool to request access:
```
cross_team_share_memory(
    context_name="project-alpha",
    target_team="engineering",
    permission_level="read",
    justification="Need access for code review"
)
```

### 2. Approval Process
- Request is sent to team administrators
- Administrators can approve/deny using `approve_cross_team_request`
- All actions are logged with timestamps and reasons

### 3. Access Granted
- Upon approval, target team gains specified permissions
- Access can be revoked at any time
- Full audit trail is maintained

## Permission Levels
- **read**: View memories only
- **write**: Add new memories to context
- **admin**: Full control including sharing permissions

## Team Merger Workflow

### Initiate Merger
```
team_merger_initiate(
    merger_type="consolidation",
    source_teams=["team-a", "team-b"],
    justification="Organizational restructuring"
)
```

### Execute Approved Merger
```
team_merger_execute(merger_id=123)
```

### Rollback if Needed
```
team_merger_rollback(
    merger_id=123,
    rollback_reason="Business requirements changed"
)
```

## Best Practices
1. Always provide clear justification for requests
2. Review permissions regularly
3. Use least-privilege principle
4. Document business reasons for team changes
5. Test access after approval before relying on it

## Monitoring
- Use `list_pending_approvals` to see pending requests
- Use `team_merger_status` to track merger progress
- All actions are automatically logged for compliance
"""

    return Resource(
        uri="ninaivalaigal://approval-workflow",
        name="Approval Workflow Guide",
        description="Complete guide for cross-team memory sharing and team merger workflows",
        mimeType="text/markdown",
        text=content,
    )


@mcp.resource("ninaivalaigal://ai-enhancement-guide")
async def ai_enhancement_guide() -> Resource:
    """Documentation for AI prompt enhancement features"""
    content = """
# AI Prompt Enhancement Guide

## Overview
The AI enhancement system provides intelligent context injection and prompt optimization for better AI interactions.

## Features

### 1. Context-Aware Enhancement
The system automatically includes relevant memories and context when enhancing prompts:
```
enhance_ai_prompt_tool(
    file_path="/path/to/code.py",
    language="python",
    enhancement_type="comprehensive",
    user_context="Working on authentication system"
)
```

### 2. Enhancement Types
- **comprehensive**: Full context with related memories, patterns, and best practices
- **focused**: Targeted enhancement for specific task
- **debug**: Enhanced with debugging context and error patterns

### 3. CCTV Integration
When CCTV recording is active, the system automatically captures:
- Tool usage patterns
- Context switches
- Memory access patterns
- User interaction flows

### 4. Feedback Loop
Store feedback to improve future enhancements:
```
store_ai_feedback(
    original_prompt="Fix this bug",
    enhanced_prompt="Fix authentication bug in login.py considering...",
    effectiveness_rating=8,
    feedback_notes="Good context but could include more error examples"
)
```

## Getting AI Context
Use `get_ai_context()` to see:
- Active CCTV recordings
- Available contexts
- Recent activity patterns

## Best Practices
1. Start CCTV recording before complex tasks
2. Use descriptive context names
3. Provide feedback on enhancement quality
4. Review context regularly for relevance
5. Use appropriate enhancement types for different tasks

## Integration with Memory System
- Enhanced prompts automatically reference relevant memories
- Context patterns are learned and applied
- User preferences are remembered and applied
- Project-specific knowledge is included automatically
"""

    return Resource(
        uri="ninaivalaigal://ai-enhancement-guide",
        name="AI Enhancement Guide",
        description="Complete guide for AI prompt enhancement and CCTV recording features",
        mimeType="text/markdown",
        text=content,
    )
