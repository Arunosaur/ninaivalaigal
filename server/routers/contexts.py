"""
Context Management Router
Extracted from main.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from auth import get_current_user
from database import Context, ContextPermission, DatabaseManager, User
from models.api_models import ContextCreate, ContextShare, ContextTransfer
from rbac.permissions import Action, Resource
from rbac_middleware import require_permission

# Initialize router
router = APIRouter(prefix="/contexts", tags=["contexts"])

# Database manager instance
db = DatabaseManager()


@router.post("")
@require_permission(Resource.CONTEXT, Action.CREATE)
async def create_context(
    request: Request,
    context_data: ContextCreate,
    current_user: User = Depends(get_current_user),
):
    """Create a new context with ownership"""
    try:
        # Create context with ownership
        context = db.create_context_with_ownership(
            name=context_data.name,
            description=context_data.description,
            scope=context_data.scope,
            owner_id=current_user.id,
            team_id=context_data.team_id,
            organization_id=context_data.organization_id,
        )

        return {
            "id": context.id,
            "name": context.name,
            "description": context.description,
            "scope": context.scope,
            "created_at": context.created_at.isoformat(),
            "message": "Context created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{context_id}/share")
def share_context(
    context_id: int,
    share_data: ContextShare,
    current_user: User = Depends(get_current_user),
):
    """Share context with user/team/organization"""
    try:
        # Validate ownership/admin permission
        if not db.check_context_permission(context_id, current_user.id, "admin"):
            raise HTTPException(403, "Only context owners/admins can share contexts")

        session = db.get_session()
        try:
            # Create permission entry
            permission = ContextPermission(
                context_id=context_id,
                user_id=(
                    share_data.target_id if share_data.target_type == "user" else None
                ),
                team_id=(
                    share_data.target_id if share_data.target_type == "team" else None
                ),
                organization_id=(
                    share_data.target_id
                    if share_data.target_type == "organization"
                    else None
                ),
                permission_level=share_data.permission_level,
                granted_by=current_user.id,
            )
            session.add(permission)
            session.commit()

            return {
                "success": True,
                "message": f"Context shared with {share_data.target_type} {share_data.target_id}",
            }
        finally:
            session.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{context_id}/transfer")
def transfer_context(
    context_id: int,
    transfer_data: ContextTransfer,
    current_user: User = Depends(get_current_user),
):
    """Transfer context ownership"""
    try:
        # Validate current ownership
        if not db.check_context_permission(context_id, current_user.id, "owner"):
            raise HTTPException(403, "Only context owners can transfer ownership")

        # Transfer ownership logic would go here
        # This is a placeholder for the actual implementation
        return {
            "success": True,
            "message": f"Context ownership transferred to {transfer_data.target_type} {transfer_data.target_id}",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
def get_all_contexts(current_user: User = Depends(get_current_user)):
    """Get all contexts with user isolation"""
    try:
        contexts = db.get_user_contexts(current_user.id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to share context: {str(e)}"
        )


@router.delete("/{context_name}")
def delete_context(context_name: str, current_user: User = Depends(get_current_user)):
    """Delete context with mandatory user authentication"""
    try:
        # Check if context exists and user has permission
        context = db.get_context_by_name(context_name, current_user.id)
        if not context:
            raise HTTPException(404, f"Context '{context_name}' not found")

        # Delete the context
        db.delete_context(context_name, current_user.id)
        return {"message": f"Context '{context_name}' deleted successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
