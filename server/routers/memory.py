"""
Memory Management Router
Extracted from main.py for better code organization
"""

import json
from fastapi import APIRouter, Depends, HTTPException, Request
from auth import get_current_user
from database import DatabaseManager, User
from models.api_models import MemoryPayload
from rbac.permissions import Action, Resource
from rbac_middleware import get_rbac_context, require_permission
from security_integration import redact_text

# Initialize router
router = APIRouter(prefix="/memory", tags=["memory"])

# Database manager instance
db = DatabaseManager()


@router.post("")
@require_permission(Resource.MEMORY, Action.CREATE)
async def store_memory(
    request: Request,
    entry: MemoryPayload,
    current_user: User = Depends(get_current_user),
):
    """Store a memory entry with user isolation and duplicate filtering"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        # Extract context from data if provided, otherwise use default
        context = (
            entry.data.get("context", "default")
            if hasattr(entry, "data") and entry.data
            else "default"
        )

        # If Windsurf is sending to hardcoded "test-context", redirect to actual active context
        if context == "test-context" and entry.source == "zsh_session":
            active_contexts = db.get_all_contexts()
            active_context_names = [
                ctx.get("name")
                for ctx in active_contexts
                if ctx.get("is_active", False)
            ]
            if active_context_names:
                # Use the first active context instead of hardcoded test-context
                context = active_context_names[0]
                # Also update the data.context field to match the redirected context
                if hasattr(entry, "data") and entry.data:
                    entry.data["context"] = context
            else:
                # No active context - block the capture
                return {
                    "message": "Skipped capture - no active context (camera off)",
                    "id": None,
                }

        # Skip terminal_command entries if we're getting duplicates from Windsurf
        if entry.type == "terminal_command" and entry.source == "zsh_session":
            return {"message": "Skipped duplicate terminal_command entry", "id": None}

        # Apply redaction to sensitive data before storing
        rbac_context = get_rbac_context(request)
        if entry.data:
            # Convert data to string for redaction
            data_str = json.dumps(entry.data)
            redacted_data_str = await redact_text(data_str, rbac_context=rbac_context)
            # Parse back to dict if redaction was applied
            if redacted_data_str != data_str:
                try:
                    entry.data = json.loads(redacted_data_str)
                except json.JSONDecodeError:
                    # If redaction broke JSON structure, store as redacted string
                    entry.data = {"redacted_content": redacted_data_str}

        memory_id = db.add_memory(
            context=context,
            memory_type=entry.type,
            source=entry.source,
            data=entry.data,
            user_id=user_id,
        )
        return {"message": "Memory entry recorded.", "id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("")
@require_permission(Resource.MEMORY, Action.READ)
def get_memory(
    request: Request, context: str, current_user: User = Depends(get_current_user)
):
    """Retrieve memories for a context with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        memories = db.get_memories(context, user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/all")
def get_all_memories(current_user: User = Depends(get_current_user)):
    """Retrieve all memories with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        memories = db.get_all_memories(user_id)
        return memories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/recall")
async def recall_hierarchical(
    query: str, context: str = None, current_user: User = Depends(get_current_user)
):
    """Hierarchical memory recall with user isolation"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        # Get memories with hierarchical recall
        memories = db.recall_memories(query, context, user_id)
        return {
            "query": query,
            "context": context,
            "memories": memories,
            "count": len(memories),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to recall memories: {str(e)}"
        )


@router.post("/record")
async def record_interaction(
    context: str,
    interaction_type: str,
    metadata: dict = None,
    current_user: User = Depends(get_current_user),
):
    """Record an interaction in a context"""
    try:
        # Use authenticated user ID (mandatory)
        user_id = current_user.id

        # Record the interaction
        interaction_id = db.record_interaction(
            context=context,
            interaction_type=interaction_type,
            metadata=metadata or {},
            user_id=user_id,
        )

        return {
            "message": "Interaction recorded successfully",
            "interaction_id": interaction_id,
            "context": context,
            "type": interaction_type,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to record interaction: {str(e)}"
        )
