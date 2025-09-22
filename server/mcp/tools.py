"""
MCP Tools for ninaivalaigal
Extracted from monolithic mcp_server.py for better organization

This addresses external code review feedback:
- Break down monolithic files (mcp_server.py 929 lines → focused modules)
- Improve code organization and maintainability
"""

import json
from datetime import datetime
from typing import Any
from .server import mcp, get_initialized_components

# Try to import secret redaction, fallback if not available
try:
    from secret_redaction import redact_memory_before_storage
except ImportError:
    def redact_memory_before_storage(data):
        return data

# Get initialized components lazily
def get_components():
    """Get components lazily to avoid import issues"""
    return get_initialized_components()

# Helper to get specific component safely
def get_component(name, default=None):
    """Get a specific component safely"""
    components = get_components()
    return components.get(name, default)

# Helper functions
async def auto_record_tool_usage(tool_name: str, description: str, result=None):
    """Record tool usage in active contexts"""
    try:
        auto_recorder = get_component('auto_recorder')
        if auto_recorder and hasattr(auto_recorder, 'active_contexts'):
            for context_name in auto_recorder.active_contexts:
                await auto_recorder.record_interaction(
                    context_name=context_name,
                    interaction_type="tool_usage",
                    content=f"Tool: {tool_name} - {description}",
                    metadata={
                        "tool": tool_name,
                        "description": description,
                        "result_count": len(result) if isinstance(result, list) else None,
                        "user_id": get_component('DEFAULT_USER_ID', 1),
                    },
                )
    except Exception as e:
        print(f"Warning: Could not auto-record tool usage: {e}")

def get_current_user():
    """Get current user info"""
    return {"user_id": get_component('DEFAULT_USER_ID', 1)}

@mcp.tool()
async def remember(text: str, context: str = None) -> str:
    """Store a memory in the specified context

    Args:
        text: The text content to remember
        context: Context name to store in (optional, uses default if not provided)

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
            # Apply secret redaction before storage
            user_id = get_component('DEFAULT_USER_ID', 1)
            memory_data = {
                "text": text,
                "timestamp": str(datetime.now()),
                "context": context,
                "user_id": user_id,
            }
            redacted_memory_data = redact_memory_before_storage(memory_data)
            redacted_text = redacted_memory_data.get("text", text)

            db = get_component('db')
            if db:
                db.add_memory(
                    context,
                    "note",
                    "mcp",
                    {
                        "text": redacted_text,
                        "timestamp": str(datetime.now()),
                        "context": context,
                        "user_id": get_component('DEFAULT_USER_ID', 1),
                    },
                    user_id=get_component('DEFAULT_USER_ID', 1),
                )

            # If CCTV recording is active, also record this interaction
            auto_recorder = get_component('auto_recorder')
            if auto_recorder and hasattr(auto_recorder, 'active_contexts') and context in auto_recorder.active_contexts:
                await auto_recorder.record_interaction(
                    context_name=context,
                    interaction_type="user_memory",
                    content=text,
                    metadata={"source": "mcp_remember", "user_id": user_id},
                )

            return f"📝 Memory stored successfully in context: {context} (User ID: {user_id})"
        except Exception as e:
            return f"Error storing memory: {e}"

    except Exception as e:
        return f"Error storing memory: {str(e)}"


@mcp.tool()
async def recall(context: str = None, query: str = None) -> list[dict[str, Any]]:
    """Retrieve memories from context, optionally filtered by query

    Args:
        context: Context name to retrieve from (optional, returns all if not specified)
        query: Text query to filter memories (optional)

    Returns:
        List of matching memories
    """
    try:
        # Auto-record this recall operation
        await auto_record_tool_usage("recall", f"Context: {context}, Query: {query}")

        db = get_component('db')
        user_id = get_component('DEFAULT_USER_ID', 1)
        
        if not db:
            return [{"error": "Database not available"}]
        
        if context:
            # Get memories from specific context
            memories = db.get_memories(context, user_id=user_id)
        else:
            # Get all memories across contexts
            memories = db.get_all_memories(user_id=user_id)

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

        # Record the result
        await auto_record_tool_usage(
            "recall", f"Found {len(memories)} memories", memories
        )

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
        result = await auto_recorder.start_recording(
            context_name, user_id=DEFAULT_USER_ID
        )

        if result["success"]:
            # Record the context start event
            await auto_recorder.record_interaction(
                context_name=context_name,
                interaction_type="system_event",
                content=f"CCTV recording started for context: {context_name}",
                metadata={"event_type": "context_start", "user_id": DEFAULT_USER_ID},
            )
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
                return (
                    f"🛑 Stopped recording for contexts: {', '.join(stopped_contexts)}"
                )
            else:
                return "🔴 No active recordings to stop"

    except Exception as e:
        return f"❌ Error stopping context: {str(e)}"


@mcp.tool()
async def list_contexts() -> str:
    """List all available contexts for the current user

    Returns:
        Formatted list of contexts with their details
    """
    try:
        # Auto-record this operation
        await auto_record_tool_usage("list_contexts", "User requested context list")

        user_info = get_current_user()
        result = spec_context_manager.list_contexts(user_info["user_id"])

        if result["success"]:
            contexts = result["contexts"]
            if not contexts:
                return "📋 No contexts found for current user"

            # Format context list
            context_list = ["📋 Available Contexts:"]
            for ctx in contexts:
                status = "🟢 Active" if ctx.get("is_active") else "⚪ Inactive"
                scope = ctx.get("scope", "personal").title()
                context_list.append(
                    f"  • {ctx['name']} ({scope}) - {status}"
                    + (f" - {ctx.get('description', 'No description')}" if ctx.get('description') else "")
                )

            return "\n".join(context_list)
        else:
            error_msg = f"❌ Error listing contexts: {result.get('error', 'Unknown error')}"
            await auto_record_tool_usage("list_contexts", error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"❌ Error listing contexts: {str(e)}"
        await auto_record_tool_usage("list_contexts", error_msg)
        return error_msg


@mcp.tool()
async def cross_team_share_memory(
    context_name: str,
    target_team: str,
    permission_level: str = "read",
    justification: str = None,
) -> dict[str, Any]:
    """Request cross-team memory sharing with approval workflow

    Args:
        context_name: Name of the context to share
        target_team: Target team name to share with
        permission_level: Permission level (read, write, admin)
        justification: Reason for sharing request

    Returns:
        Request status and details
    """
    try:
        user_info = get_current_user()
        result = approval_manager.request_cross_team_access(
            requester_user_id=user_info["user_id"],
            context_name=context_name,
            target_team=target_team,
            permission_level=permission_level,
            justification=justification or "Cross-team collaboration",
        )

        await auto_record_tool_usage(
            "cross_team_share_memory",
            f"Requested sharing {context_name} with {target_team}",
        )

        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to request cross-team sharing: {str(e)}",
        }


@mcp.tool()
async def team_merger_initiate(
    merger_type: str,
    source_teams: list[str],
    target_team: str = None,
    justification: str = None,
) -> dict[str, Any]:
    """
    Initiate team merger process with approval workflow

    Args:
        merger_type: Type of merger (consolidation, absorption, split)
        source_teams: List of source team names
        target_team: Target team name (for absorption type)
        justification: Business justification for merger

    Returns:
        Merger initiation status and details
    """
    try:
        user_info = get_current_user()
        result = approval_manager.initiate_team_merger(
            initiator_user_id=user_info["user_id"],
            merger_type=merger_type,
            source_teams=source_teams,
            target_team=target_team,
            justification=justification or "Team restructuring",
        )

        await auto_record_tool_usage(
            "team_merger_initiate",
            f"Initiated {merger_type} merger for teams: {', '.join(source_teams)}",
        )

        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initiate team merger: {str(e)}",
        }


@mcp.tool()
async def team_merger_execute(merger_id: int) -> dict[str, Any]:
    """
    Execute approved team merger

    Args:
        merger_id: ID of the approved merger

    Returns:
        Execution status and details
    """
    try:
        user_info = get_current_user()
        result = approval_manager.execute_team_merger(
            merger_id=merger_id, executor_user_id=user_info["user_id"]
        )

        await auto_record_tool_usage(
            "team_merger_execute", f"Executed team merger ID: {merger_id}"
        )

        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute team merger: {str(e)}",
        }


@mcp.tool()
async def team_merger_status(merger_id: int) -> dict[str, Any]:
    """
    Get status of team merger

    Args:
        merger_id: ID of the merger to check

    Returns:
        Merger status and details
    """
    try:
        result = approval_manager.get_merger_status(merger_id)

        await auto_record_tool_usage(
            "team_merger_status", f"Checked status of merger ID: {merger_id}"
        )

        return result
    except Exception as e:
        return {"status": "error", "message": f"Failed to get merger status: {str(e)}"}


@mcp.tool()
async def team_merger_rollback(merger_id: int, rollback_reason: str) -> dict[str, Any]:
    """
    Rollback completed team merger

    Args:
        merger_id: ID of the merger to rollback
        rollback_reason: Reason for rollback

    Returns:
        Rollback status and details
    """
    try:
        user_info = get_current_user()
        result = approval_manager.rollback_team_merger(
            merger_id=merger_id,
            rollback_reason=rollback_reason,
            rollback_user_id=user_info["user_id"],
        )

        return result
    except Exception as e:
        return {"status": "error", "message": f"Failed to rollback merger: {str(e)}"}


@mcp.tool()
async def approve_cross_team_request(
    request_id: int, action: str, reason: str = None
) -> str:
    """Approve or deny cross-team access request

    Args:
        request_id: ID of the request to process
        action: 'approve' or 'deny'
        reason: Optional reason for the decision

    Returns:
        Processing result message
    """
    try:
        user_info = get_current_user()
        result = approval_manager.process_approval_request(
            request_id=request_id,
            approver_user_id=user_info["user_id"],
            action=action,
            reason=reason,
        )

        if result["success"]:
            return f"✅ Request {request_id} {action}ed successfully"
        else:
            return f"❌ Error processing request: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f" Error processing approval action: {str(e)}"


@mcp.tool()
async def list_pending_approvals() -> str:
    """List pending cross-team access requests"""
    try:
        user_info = get_current_user()
        result = approval_manager.list_pending_requests(user_info["user_id"])

        if result["success"]:
            requests = result["requests"]
            if not requests:
                return "📋 No pending approval requests"

            # Format request list
            request_list = ["📋 Pending Approval Requests:"]
            for req in requests:
                request_list.append(
                    f"  • ID: {req['id']} - {req['context_name']} → {req['target_team']} "
                    f"({req['permission_level']}) - {req.get('justification', 'No justification')}"
                )

            return "\n".join(request_list)
        else:
            return f"❌ Error listing requests: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f" Error listing pending approvals: {str(e)}"


@mcp.tool()
async def enhance_ai_prompt_tool(
    file_path: str,
    language: str,
    enhancement_type: str = "comprehensive",
    user_context: str = None,
) -> str:
    """Enhance AI prompts with context and memory integration

    Args:
        file_path: Path to the file being worked on
        language: Programming language or file type
        enhancement_type: Type of enhancement (comprehensive, focused, debug)
        user_context: Additional user context

    Returns:
        Enhanced prompt with integrated context
    """
    try:
        user_info = get_current_user()
        result = spec_context_manager.enhance_ai_prompt(
            user_id=user_info["user_id"],
            file_path=file_path,
            language=language,
            enhancement_type=enhancement_type,
            user_context=user_context,
        )

        if result["success"]:
            return result["enhanced_prompt"]
        else:
            return f"❌ Error enhancing prompt: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"❌ Error enhancing AI prompt: {str(e)}"


@mcp.tool()
async def get_ai_context(user_id: int = None, project_context: str = None) -> str:
    """Get CCTV recording status and available contexts"""
    try:
        # Get recording status
        status = await auto_recorder.get_recording_status()

        # Get available contexts
        user_info = get_current_user()
        contexts_result = spec_context_manager.list_contexts(user_info["user_id"])

        # Format response
        response = ["🎥 CCTV Recording Status:"]
        if status["active_contexts"]:
            response.append(f"  Active recordings: {len(status['active_contexts'])}")
            for ctx_name, ctx_info in status["contexts"].items():
                response.append(f"    • {ctx_name}: {ctx_info['status']}")
        else:
            response.append("  No active recordings")

        if contexts_result["success"]:
            response.append(f"\n📋 Available contexts: {len(contexts_result['contexts'])}")

        return "\n".join(response)

    except Exception as e:
        return f"❌ Error getting AI context: {str(e)}"


@mcp.tool()
async def store_ai_feedback(
    original_prompt: str,
    enhanced_prompt: str,
    effectiveness_rating: int,
    feedback_notes: str = None,
) -> str:
    """Store feedback on AI prompt enhancement effectiveness

    Args:
        original_prompt: Original prompt text
        enhanced_prompt: Enhanced prompt text
        effectiveness_rating: Rating from 1-10
        feedback_notes: Optional feedback notes

    Returns:
        Storage confirmation message
    """
    try:
        user_info = get_current_user()
        result = spec_context_manager.store_ai_feedback(
            user_id=user_info["user_id"],
            original_prompt=original_prompt,
            enhanced_prompt=enhanced_prompt,
            effectiveness_rating=effectiveness_rating,
            feedback_notes=feedback_notes,
        )

        if result["success"]:
            return f"✅ AI feedback stored successfully (Rating: {effectiveness_rating}/10)"
        else:
            return f"❌ Error storing feedback: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"❌ Error storing AI feedback: {str(e)}"
