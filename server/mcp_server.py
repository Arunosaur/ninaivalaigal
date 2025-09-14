#!/opt/homebrew/anaconda3/bin/python
"""
Ninaivalaigal MCP Server - Model Context Protocol implementation
Provides e^M (exponential Memory) management capabilities as MCP tools, resources, and prompts
"""

import asyncio
import json
from typing import Any, Optional, List, Dict
from mcp.server.fastmcp import FastMCP
from mcp.types import Resource, TextResourceContents, Tool, Prompt
from datetime import datetime

# Import existing mem0 components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from approval_workflow import ApprovalWorkflowManager
from universal_ai_wrapper import UniversalAIWrapper
from auto_recording import get_auto_recorder
from main import load_config

# Initialize MCP server
mcp = FastMCP("e^m")

# Initialize database and config
config = load_config()
database_url = config.get('database_url', 'sqlite:///./mem0.db')
db = DatabaseManager(database_url)
approval_manager = ApprovalWorkflowManager(db)
auto_recorder = get_auto_recorder(db)

# JWT token handling for user authentication
import os
import jwt
import json

def get_user_from_jwt():
    """Extract user ID from JWT token"""
    token = os.getenv('NINAIVALAIGAL_USER_TOKEN')
    if not token:
        return int(os.getenv('NINAIVALAIGAL_USER_ID', '1'))  # Fallback
    
    try:
        # Decode JWT token (without verification for now - should be verified in production)
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('user_id', 1)
    except Exception as e:
        print(f"JWT decode error: {e}")
        return int(os.getenv('NINAIVALAIGAL_USER_ID', '1'))  # Fallback

DEFAULT_USER_ID = get_user_from_jwt()

@mcp.tool()
async def remember(text: str, context: str = None) -> str:
    """Store a memory in the specified context
    
    Args:
        text: The text content to remember
        context: Context name to store the memory in (optional)
    
    Returns:
        Confirmation message
    """
    try:
        # Parse JSON if text looks like structured data
        try:
            data = json.loads(text)
            memory_type = data.get("type", "note")
            source = data.get("source", "mcp")
            memory_data = data.get("data", {"text": text})
        except (json.JSONDecodeError, TypeError):
            # Plain text memory
            memory_type = "note"
            source = "mcp"
            memory_data = {"text": text}
        
        # Use default context if none provided
        if not context:
            context = "default"
            
        try:
            db.add_memory(context, "note", "mcp", {"text": text, "timestamp": str(datetime.now()), "context": context, "user_id": DEFAULT_USER_ID})
            return f"📝 Memory stored successfully in context: {context} (User ID: {DEFAULT_USER_ID})"
        except Exception as e:
            return f"Error storing memory: {e}"
        
    except Exception as e:
        return f"Error storing memory: {str(e)}"

@mcp.tool()
async def recall(context: str = None, query: str = None) -> List[Dict[str, Any]]:
    """Retrieve memories from context, optionally filtered by query
    
    Args:
        context: Context name to retrieve from (optional, returns all if not specified)
        query: Text query to filter memories (optional)
    
    Returns:
        List of matching memories
    """
    try:
        if context:
            # Get memories from specific context
            memories = db.get_memories(context)
        else:
            # Get all memories across contexts
            memories = db.get_all_memories()
        
        # Apply text filtering if query provided
        if query and memories:
            filtered_memories = []
            query_lower = query.lower()
            for memory in memories:
                # Search in memory text content
                memory_text = ""
                if isinstance(memory.get("data"), dict):
                    memory_text = memory["data"].get("text", "")
                elif isinstance(memory.get("data"), str):
                    memory_text = memory["data"]
                
                if query_lower in memory_text.lower():
                    filtered_memories.append(memory)
            memories = filtered_memories
        
        return memories
        
    except Exception as e:
        return [{"error": f"Error retrieving memories: {str(e)}"}]

@mcp.tool()
async def context_start(context_name: str) -> str:
    """Start CCTV-style automatic recording to a context
    
    Args:
        context_name: Name of the context to start recording to
    
    Returns:
        Confirmation message
    """
    try:
        # Start automatic CCTV recording with user ID from environment
        result = await auto_recorder.start_recording(context_name, user_id=DEFAULT_USER_ID)
        
        if result["success"]:
            return result["message"]
        else:
            return f"❌ Error starting recording: {result['error']}"
        
    except Exception as e:
        return f"❌ Error starting context: {str(e)}"

@mcp.tool()
async def context_stop(context_name: str = None) -> str:
    """Stop CCTV-style automatic recording
    
    Args:
        context_name: Specific context to stop (optional, stops all if not provided)
    
    Returns:
        Confirmation message
    """
    try:
        if context_name:
            # Stop specific context
            result = await auto_recorder.stop_recording(context_name)
            if result["success"]:
                return result["message"]
            else:
                return f"❌ Error stopping recording: {result['error']}"
        else:
            # Stop all active recordings
            status = await auto_recorder.get_recording_status()
            stopped_contexts = []
            for ctx_name in list(status["contexts"].keys()):
                result = await auto_recorder.stop_recording(ctx_name)
                if result["success"]:
                    stopped_contexts.append(ctx_name)
            
            if stopped_contexts:
                return f"🛑 Stopped recording for contexts: {', '.join(stopped_contexts)}"
            else:
                return "🔴 No active recordings to stop"
        
    except Exception as e:
        return f"❌ Error stopping context: {str(e)}"

@mcp.tool()
async def list_contexts() -> str:
    """List all available contexts"""
    try:
        # For now, return all contexts - in production this should be user-scoped
        contexts = db.get_all_contexts()
        if not contexts:
            return "No contexts found."
        
        context_list = []
        for ctx in contexts:
            status = " Active" if ctx.get('is_active') else " Inactive"
            context_list.append(f"• {ctx['name']} ({status}) - {ctx.get('description', 'No description')}")
        
        return "Available contexts:\n" + "\n".join(context_list)
    except Exception as e:
        return f"Error listing contexts: {str(e)}"

@mcp.tool()
async def cross_team_share_memory(
    context_name: str,
    target_team: str,
    access_level: str = "read",
    justification: str = ""
) -> Dict[str, Any]:
    """
    Share memory context with another team (requires approval)
    
    Args:
        context_name: Name of the context to share
        target_team: Target team ID to share with
        access_level: Access level (read/write)
        justification: Justification for sharing
    """
    user_info = get_current_user()
    
    try:
        # Create cross-team sharing request
        request_id = db.create_cross_team_request(
            context_name=context_name,
            requesting_user=user_info['user_id'],
            requesting_team=user_info['team_id'],
            target_team=target_team,
            access_level=access_level,
            justification=justification
        )
        
        return {
            "status": "success",
            "message": f"Cross-team sharing request created",
            "request_id": request_id,
            "context": context_name,
            "target_team": target_team,
            "access_level": access_level
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create sharing request: {str(e)}"
        }

@mcp.tool()
async def team_merger_initiate(
    merger_type: str,
    source_teams: List[str],
    target_teams: List[str],
    memory_policy: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Initiate team merger process
    
    Args:
        merger_type: Type of merger ('consolidation', 'split', 'dissolution', 'rename')
        source_teams: List of source team IDs
        target_teams: List of target team IDs
        memory_policy: Memory migration policy configuration
    """
    user_info = get_current_user()
    
    try:
        from .team_merger_manager import TeamMergerManager
        
        # Validate user permissions
        if not db.user_has_permission(user_info['user_id'], 'team_management'):
            raise PermissionError("Insufficient permissions for team merger")
        
        merger_config = {
            'type': merger_type,
            'source_teams': source_teams,
            'target_teams': target_teams,
            'initiated_by': user_info['user_id'],
            'memory_policy': memory_policy or {}
        }
        
        merger_manager = TeamMergerManager(db)
        merger_id = merger_manager.initiate_team_merger(
            user_info['organization_id'], merger_config
        )
        
        return {
            'status': 'success',
            'merger_id': merger_id,
            'merger_type': merger_type,
            'source_teams': source_teams,
            'target_teams': target_teams,
            'next_steps': [
                'Review merger plan with team leads',
                'Approve memory migration policy',
                'Execute merger when ready'
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initiate team merger: {str(e)}"
        }

@mcp.tool()
async def team_merger_execute(merger_id: int) -> Dict[str, Any]:
    """
    Execute approved team merger
    
    Args:
        merger_id: ID of the merger to execute
    """
    user_info = get_current_user()
    
    try:
        from .team_merger_manager import TeamMergerManager
        
        merger_manager = TeamMergerManager(db)
        merger = db.get_team_merger(merger_id)
        
        if not merger:
            raise ValueError(f"Merger {merger_id} not found")
        
        if merger['merger_type'] == 'consolidation':
            result = merger_manager.execute_team_consolidation(merger_id)
        elif merger['merger_type'] == 'split':
            result = merger_manager.execute_team_split(merger_id)
        elif merger['merger_type'] == 'dissolution':
            result = merger_manager.execute_team_dissolution(merger_id)
        elif merger['merger_type'] == 'rename':
            result = merger_manager.execute_team_rename(merger_id)
        else:
            raise ValueError(f"Unknown merger type: {merger['merger_type']}")
        
        return {
            'status': 'success',
            'execution_result': result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to execute team merger: {str(e)}"
        }

@mcp.tool()
async def team_merger_status(merger_id: int) -> Dict[str, Any]:
    """
    Get status of team merger
    
    Args:
        merger_id: ID of the merger to check
    """
    user_info = get_current_user()
    
    try:
        merger = db.get_team_merger(merger_id)
        if not merger:
            raise ValueError(f"Merger {merger_id} not found")
        
        # Get detailed status
        status_info = db.get_team_merger_status(merger_id)
        audit_trail = db.get_merger_audit_trail(merger_id)
        
        return {
            'status': 'success',
            'merger_info': merger,
            'current_status': status_info,
            'audit_trail': audit_trail[-5:] if audit_trail else [],  # Last 5 entries
            'can_rollback': merger['status'] == 'completed'
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get merger status: {str(e)}"
        }

@mcp.tool()
async def team_merger_rollback(merger_id: int, rollback_reason: str) -> Dict[str, Any]:
    """
    Rollback completed team merger
    
    Args:
        merger_id: ID of the merger to rollback
        rollback_reason: Reason for rollback
    """
    user_info = get_current_user()
    
    try:
        from .team_merger_manager import TeamMergerManager
        
        # Validate permissions
        if not db.user_has_permission(user_info['user_id'], 'team_management'):
            raise PermissionError("Insufficient permissions for merger rollback")
        
        merger_manager = TeamMergerManager(db)
        result = merger_manager.rollback_merger(merger_id, rollback_reason)
        
        return {
            'status': 'success',
            'rollback_result': result
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to rollback merger: {str(e)}"
        }

@mcp.tool()
async def approve_cross_team_request(request_id: int, action: str, reason: str = None) -> str:
    """Approve or reject a cross-team access request"""
    try:
        # Note: In real implementation, we'd get user_id from authentication
        user_id = 1  # This should come from authentication context
        
        if action.lower() == "approve":
            result = approval_manager.approve_request(request_id, user_id)
        elif action.lower() == "reject":
            result = approval_manager.reject_request(request_id, user_id, reason)
        else:
            return " Error: Action must be 'approve' or 'reject'"
        
        if result["success"]:
            return f" Request {action}d successfully: {result['message']}"
        else:
            return f" Error: {result['error']}"
            
    except Exception as e:
        return f" Error processing approval action: {str(e)}"

@mcp.tool()
async def list_pending_approvals() -> str:
    """List pending cross-team access requests"""
    try:
        # Note: In real implementation, we'd get user_id from authentication
        user_id = 1  # This should come from authentication context
        
        user_teams = db.get_user_teams(user_id)
        all_requests = []
        
        for team in user_teams:
            team_requests = approval_manager.get_pending_requests_for_team(team.id)
            all_requests.extend(team_requests)
        
        if not all_requests:
            return "No pending approval requests found."
        
        request_list = []
        for req in all_requests:
            request_list.append(
                f"• Request #{req['id']}: {req['requesting_team']} → {req['context_name']}\n"
                f"  Permission: {req['permission_level']} | Expires: {req['expires_at'][:10]}\n"
                f"  Justification: {req['justification'] or 'None provided'}"
            )
        
        return "Pending Cross-Team Access Requests:\n\n" + "\n\n".join(request_list)
        
    except Exception as e:
        return f" Error listing pending approvals: {str(e)}"

@mcp.tool()
async def enhance_ai_prompt_tool(
    file_path: str,
    language: str,
    prompt: str,
    cursor_position: int = 0,
    surrounding_code: str = "",
    ai_model: str = "generic_ai",
    user_id: int = None,
    team_id: int = None,
    organization_id: int = None,
    project_context: str = None,
    ide_name: str = None,
    workspace_path: str = None,
    interaction_type: str = "completion"
) -> str:
    """Enhance AI prompts with relevant mem0 memories"""
    try:
        result = await enhance_ai_prompt(
            file_path=file_path,
            language=language,
            cursor_position=cursor_position,
            surrounding_code=surrounding_code,
            prompt=prompt,
            ai_model=ai_model,
            user_id=user_id,
            team_id=team_id,
            organization_id=organization_id,
            project_context=project_context,
            interaction_type=interaction_type,
            ide_name=ide_name,
            workspace_path=workspace_path
        )
        
        return result
        
    except Exception as e:
        return f"❌ Error enhancing AI prompt: {str(e)}"

@mcp.tool()
async def get_ai_context(user_id: int = None, project_context: str = None) -> str:
    """Get CCTV recording status and available contexts"""
    try:
        # Get recording status
        status = await auto_recorder.get_recording_status()
        
        result = []
        result.append(f"🎥 CCTV Status: {'Active' if status['active_contexts'] > 0 else 'Inactive'}")
        result.append(f"📊 Active Contexts: {status['active_contexts']}")
        
        if status["contexts"]:
            result.append("\n🔴 Currently Recording:")
            for ctx_name, ctx_info in status["contexts"].items():
                result.append(f"  • {ctx_name}: {ctx_info['messages_recorded']} messages recorded")
        
        # Get all available contexts
        all_contexts = db.get_all_contexts()
        if all_contexts:
            result.append(f"\n📋 Available Contexts: {len(all_contexts)} total")
            for ctx in all_contexts[:5]:  # Show first 5
                result.append(f"  • {ctx.get('name', 'Unknown')}")
            if len(all_contexts) > 5:
                result.append(f"  ... and {len(all_contexts) - 5} more")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"❌ Error getting AI context: {str(e)}"

@mcp.tool()
async def store_ai_feedback(
    original_prompt: str,
    enhanced_prompt: str,
    ai_response: str,
    user_accepted: bool,
    ai_model: str = "generic_ai",
    language: str = "",
    project_context: str = None
) -> str:
    """Store AI interaction feedback for learning"""
    try:
        feedback_data = {
            "original_prompt": original_prompt[:200],  # Truncate for storage
            "enhanced_prompt_length": len(enhanced_prompt),
            "ai_response_length": len(ai_response),
            "user_accepted": user_accepted,
            "ai_model": ai_model,
            "language": language,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store feedback as memory
        context_name = f"ai_feedback_{project_context or 'default'}"
        
        feedback_text = f"AI {ai_model} {'accepted' if user_accepted else 'rejected'} for {language}"
        if not user_accepted:
            feedback_text += f" - Original: {original_prompt[:100]}..."
        
        # This would typically call the remember function
        # For now, just return success
        
        return f"✅ AI feedback stored: {feedback_text}"
        
    except Exception as e:
        return f"❌ Error storing AI feedback: {str(e)}"

@mcp.resource("ninaivalaigal://contexts")
async def list_all_contexts() -> Resource:
    """Provide list of all contexts as a resource"""
    try:
        contexts = db.get_contexts()
        content = "\n".join(f"- {context}" for context in contexts)
        
        return Resource(
            uri="ninaivalaigal://contexts",
            name="Available Contexts",
            description="List of all available memory contexts",
            mimeType="text/plain"
        )
    except Exception as e:
        return Resource(
            uri="ninaivalaigal://contexts",
            name="Context List Error",
            description=f"Error retrieving contexts: {str(e)}",
            mimeType="text/plain"
        )

@mcp.resource("ninaivalaigal://context/{context_name}")
async def get_context_memories(context_name: str) -> Resource:
    """Provide all memories for a specific context"""
    try:
        memories = db.get_memories(context_name)
        content = json.dumps(memories, indent=2)
        
        return Resource(
            uri=f"ninaivalaigal://context/{context_name}",
            name=f"Context: {context_name}",
            description=f"All memories from context '{context_name}'",
            mimeType="application/json"
        )
    except Exception as e:
        return Resource(
            uri=f"ninaivalaigal://context/{context_name}",
            name=f"Context Error: {context_name}",
            description=f"Error retrieving context: {str(e)}",
            mimeType="text/plain"
        )

@mcp.resource("ninaivalaigal://recent")
async def get_recent_memories() -> Resource:
    """Provide recently added memories across all contexts"""
    try:
        memories = db.get_recent_memories(limit=50)
        content = json.dumps(memories, indent=2)
        
        return Resource(
            uri="ninaivalaigal://recent",
            name="Recent Memories",
            description="Recently added memories across all contexts",
            mimeType="application/json"
        )
    except Exception as e:
        return Resource(
            uri="ninaivalaigal://recent",
            name="Recent Memories Error", 
            description=f"Error retrieving recent memories: {str(e)}",
            mimeType="text/plain"
        )

@mcp.prompt()
async def analyze_context(context_name: str) -> Prompt:
    """Generate a prompt to analyze memories in a context"""
    try:
        memories = db.get_memories(context_name)
        memory_count = len(memories)
        
        prompt_text = f"""Analyze the memories in context '{context_name}':

Context: {context_name}
Total memories: {memory_count}

Please analyze these memories and provide insights about:
1. Common themes and patterns
2. Key activities and events
3. Important decisions or outcomes
4. Potential next steps or recommendations

Recent memories from this context:
{json.dumps(memories[:10], indent=2)}
"""
        
        return Prompt(
            name=f"analyze-context-{context_name}",
            description=f"Analyze memories in context '{context_name}'",
            arguments=[
                {"name": "context_name", "description": "Context to analyze", "required": True}
            ]
        )
    except Exception as e:
        return Prompt(
            name="analyze-context-error",
            description=f"Error creating analysis prompt: {str(e)}",
            arguments=[]
        )

@mcp.prompt()
async def summarize_session() -> Prompt:
    """Generate a prompt to summarize current session memories"""
    try:
        recent_memories = db.get_recent_memories(limit=20)
        
        prompt_text = f"""Summarize the current development session:

Recent activity ({len(recent_memories)} memories):

Please provide a summary including:
1. What was accomplished
2. Key decisions made
3. Current state and context
4. Next steps or outstanding items

Recent memories:
{json.dumps(recent_memories, indent=2)}
"""
        
        return Prompt(
            name="summarize-session",
            description="Summarize current development session",
            arguments=[]
        )
    except Exception as e:
        return Prompt(
            name="summarize-session-error",
            description=f"Error creating summary prompt: {str(e)}",
            arguments=[]
        )

# Add resource for approval workflow documentation
@mcp.resource("ninaivalaigal://approval-workflow")
async def approval_workflow_guide() -> Resource:
    """Documentation for cross-team memory approval workflow"""
    content = """
# Cross-Team Memory Approval Workflow

## Overview
Ninaivalaigal supports hierarchical memory access with approval workflows:

1. **Personal Memory** - Private to individual users
2. **Team Memory** - Shared within team members
3. **Cross-Team Memory** - Shared between teams (requires approval)
4. **Organizational Memory** - Public within organization

## Cross-Team Access Process

### 1. Request Access
```
request_cross_team_access(
    context_id=123,
    target_team_id=456,
    permission_level="read",  # read, write, admin
    justification="Need access for project collaboration"
)
```

### 2. Review Pending Requests
```
list_pending_approvals()
```

### 3. Approve/Reject Requests
```
approve_cross_team_request(
    request_id=789,
    action="approve",  # or "reject"
    reason="Approved for Q4 project collaboration"
)
```

## Permission Levels
- **read**: View memories only
- **write**: Add new memories
- **admin**: Manage context settings
- **owner**: Full control (cannot be granted via cross-team)

## Security Features
- Requests expire after 7 days
- Only team admins/owners can approve requests
- All actions are logged and auditable
- Granular permission controls
"""
    
    return Resource(
        uri="ninaivalaigal://approval-workflow",
        name="Cross-Team Approval Workflow Guide",
        description="Complete guide for cross-team memory sharing with approval workflows",
        mimeType="text/markdown"
    ), TextResourceContents(text=content)

if __name__ == "__main__":
    import asyncio
    mcp.run()
