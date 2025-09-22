"""
Approval Workflow Router
Extracted from main.py for better code organization
"""

from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from database import DatabaseManager, User
from models.api_models import CrossTeamAccessRequest, ApprovalAction
from approval_workflow import ApprovalWorkflowManager

# Initialize router
router = APIRouter(prefix="/approvals", tags=["approvals"])

# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url
    return DatabaseManager(get_dynamic_database_url())

def get_approval_manager(db: DatabaseManager = Depends(get_db)):
    """Get approval manager with dynamic database"""
    return ApprovalWorkflowManager(db)


@router.post("/cross-team-request")
async def request_cross_team_access(
    request_data: CrossTeamAccessRequest, 
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    approval_manager: ApprovalWorkflowManager = Depends(get_approval_manager),
):
    """Request cross-team access to a context"""
    # Get user's team for the request
    user_teams = db.get_user_teams(current_user.id)
    if not user_teams:
        raise HTTPException(
            status_code=400,
            detail="User must be a member of a team to request cross-team access",
        )

    # Use the first team the user belongs to as requesting team
    requesting_team_id = user_teams[0].id

    result = approval_manager.request_cross_team_access(
        context_id=request_data.context_id,
        requesting_team_id=requesting_team_id,
        target_team_id=request_data.target_team_id,
        requested_by=current_user.id,
        permission_level=request_data.permission_level,
        justification=request_data.justification,
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/action")
async def handle_approval_action(
    action_data: ApprovalAction, current_user: User = Depends(get_current_user)
):
    """Approve or reject a cross-team access request"""
    if action_data.action == "approve":
        result = approval_manager.approve_request(
            action_data.request_id, current_user.id
        )
    elif action_data.action == "reject":
        result = approval_manager.reject_request(
            action_data.request_id, current_user.id, action_data.reason
        )
    else:
        raise HTTPException(
            status_code=400, detail="Invalid action. Must be 'approve' or 'reject'"
        )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/pending")
async def get_pending_approvals(current_user: User = Depends(get_current_user)):
    """Get pending approval requests for user's teams"""
    user_teams = db.get_user_teams(current_user.id)
    team_ids = [team.id for team in user_teams]

    all_requests = []
    for team_id in team_ids:
        requests = approval_manager.get_pending_requests_for_team(team_id)
        all_requests.extend(requests)

    return {"pending_requests": all_requests}


@router.get("/status/{request_id}")
async def get_approval_status(
    request_id: int, current_user: User = Depends(get_current_user)
):
    """Get status of a specific approval request"""
    result = approval_manager.get_request_status(request_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
