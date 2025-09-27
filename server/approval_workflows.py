"""
Approval Workflows System - The Governance Bridge
Connects team + memory systems with controlled publishing and accountability
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from auth_utils import get_current_user
from enum import Enum

router = APIRouter(prefix="/approval", tags=["approval"])

# Approval Status Enum
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Mock Approval Database
APPROVALS_DB = [
    {
        "id": 1,
        "memory_id": 2,  # Team memory from memory_system.py
        "submitted_by": 123,
        "reviewed_by": None,
        "status": "pending",
        "submitted_at": "2025-01-26T10:00:00Z",
        "reviewed_at": None,
        "team_id": 1,
        "memory_content": "Team decision: Use GET-based endpoints for MVP to bypass POST issues",
        "submission_note": "Important architectural decision for the team",
        "review_note": None
    },
    {
        "id": 2,
        "memory_id": 3,  # Another team memory
        "submitted_by": 456,
        "reviewed_by": 123,
        "status": "approved",
        "submitted_at": "2025-01-25T14:30:00Z",
        "reviewed_at": "2025-01-25T16:45:00Z",
        "team_id": 1,
        "memory_content": "Code review: Auth system looks solid, ready for production",
        "submission_note": "Code review results for team visibility",
        "review_note": "Approved - excellent analysis and ready for team sharing"
    },
    {
        "id": 3,
        "memory_id": 5,  # Pending memory
        "submitted_by": 789,
        "reviewed_by": None,
        "status": "pending",
        "submitted_at": "2025-01-26T09:15:00Z",
        "reviewed_at": None,
        "team_id": 2,
        "memory_content": "Performance optimization: Database queries reduced by 40%",
        "submission_note": "Performance improvement results to share with team",
        "review_note": None
    }
]

# Team memberships (from teams_working.py)
TEAM_MEMBERSHIPS_DB = [
    {"id": 1, "team_id": 1, "user_id": 123, "role": "team_admin"},
    {"id": 2, "team_id": 1, "user_id": 789, "role": "member"},
    {"id": 3, "team_id": 2, "user_id": 456, "role": "team_admin"},
    {"id": 4, "team_id": 2, "user_id": 123, "role": "member"},
]

def get_user_team_role(user_id: int, team_id: int) -> Optional[str]:
    """Get user's role in a specific team"""
    membership = next(
        (m for m in TEAM_MEMBERSHIPS_DB 
         if m["team_id"] == team_id and m["user_id"] == user_id), 
        None
    )
    return membership["role"] if membership else None

def can_approve_for_team(user_id: int, team_id: int, user_role: str) -> bool:
    """Check if user can approve memories for a team"""
    # Global admins can approve anything
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Team admins can approve for their team
    team_role = get_user_team_role(user_id, team_id)
    return team_role == "team_admin"

def can_view_team_approvals(user_id: int, team_id: int, user_role: str) -> bool:
    """Check if user can view team approvals"""
    # Global admins can see all
    if user_role in ["admin", "org_admin"]:
        return True
    
    # Team members can see their team's approvals
    team_role = get_user_team_role(user_id, team_id)
    return team_role is not None

@router.get("/submit")
async def submit_for_approval(
    memory_id: int,
    submission_note: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Submit a memory for team approval"""
    user_id = user["user_id"]
    
    # Mock: Get memory details (in real implementation, query memory_system)
    # For demo, we'll simulate memory lookup
    mock_memory = {
        "id": memory_id,
        "user_id": user_id,
        "team_id": 1,  # Assume team 1 for demo
        "content": f"Memory content for ID {memory_id}",
    }
    
    # Verify user owns the memory
    if mock_memory["user_id"] != user_id:
        raise HTTPException(
            status_code=403, 
            detail="Can only submit your own memories for approval"
        )
    
    # Verify memory is team-scoped
    if mock_memory["team_id"] is None:
        raise HTTPException(
            status_code=400, 
            detail="Only team memories can be submitted for approval"
        )
    
    # Check if already submitted
    existing_approval = next(
        (a for a in APPROVALS_DB if a["memory_id"] == memory_id), 
        None
    )
    
    if existing_approval:
        return {
            "success": False,
            "error": f"Memory already submitted for approval (Status: {existing_approval['status']})",
            "existing_approval": existing_approval
        }
    
    # Create new approval request
    new_approval_id = max([a["id"] for a in APPROVALS_DB]) + 1 if APPROVALS_DB else 1
    
    new_approval = {
        "id": new_approval_id,
        "memory_id": memory_id,
        "submitted_by": user_id,
        "reviewed_by": None,
        "status": "pending",
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "reviewed_at": None,
        "team_id": mock_memory["team_id"],
        "memory_content": mock_memory["content"],
        "submission_note": submission_note,
        "review_note": None
    }
    
    APPROVALS_DB.append(new_approval)
    
    return {
        "success": True,
        "approval": new_approval,
        "message": "Memory submitted for approval successfully",
        "next_steps": "Team admins will review and approve/reject"
    }

@router.get("/pending")
async def get_pending_approvals(
    team_id: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List pending approvals for reviewer"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Filter approvals user can review
    reviewable_approvals = []
    
    for approval in APPROVALS_DB:
        if approval["status"] != "pending":
            continue
            
        approval_team_id = approval["team_id"]
        
        # Apply team filter if specified
        if team_id is not None and approval_team_id != team_id:
            continue
        
        # Check if user can approve for this team
        if can_approve_for_team(user_id, approval_team_id, user_role):
            reviewable_approvals.append(approval)
    
    # Sort by submission date (oldest first)
    reviewable_approvals.sort(key=lambda a: a["submitted_at"])
    
    return {
        "success": True,
        "pending_approvals": reviewable_approvals,
        "count": len(reviewable_approvals),
        "team_filter": team_id,
        "reviewer_role": user_role
    }

@router.get("/{approval_id}/approve")
async def approve_memory(
    approval_id: int,
    review_note: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Approve a pending memory"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find approval
    approval = next((a for a in APPROVALS_DB if a["id"] == approval_id), None)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Check if already reviewed
    if approval["status"] != "pending":
        return {
            "success": False,
            "error": f"Approval already {approval['status']}",
            "current_status": approval["status"]
        }
    
    # Check permissions
    if not can_approve_for_team(user_id, approval["team_id"], user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - not authorized to approve for this team"
        )
    
    # Don't allow self-approval
    if approval["submitted_by"] == user_id:
        return {
            "success": False,
            "error": "Cannot approve your own submission"
        }
    
    # Update approval
    approval["status"] = "approved"
    approval["reviewed_by"] = user_id
    approval["reviewed_at"] = datetime.utcnow().isoformat() + "Z"
    approval["review_note"] = review_note
    
    return {
        "success": True,
        "approval": approval,
        "message": "Memory approved successfully",
        "action": "Memory is now visible to all team members"
    }

@router.get("/{approval_id}/reject")
async def reject_memory(
    approval_id: int,
    review_note: str = "",
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Reject a pending memory"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find approval
    approval = next((a for a in APPROVALS_DB if a["id"] == approval_id), None)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Check if already reviewed
    if approval["status"] != "pending":
        return {
            "success": False,
            "error": f"Approval already {approval['status']}",
            "current_status": approval["status"]
        }
    
    # Check permissions
    if not can_approve_for_team(user_id, approval["team_id"], user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - not authorized to reject for this team"
        )
    
    # Don't allow self-rejection
    if approval["submitted_by"] == user_id:
        return {
            "success": False,
            "error": "Cannot reject your own submission"
        }
    
    # Update approval
    approval["status"] = "rejected"
    approval["reviewed_by"] = user_id
    approval["reviewed_at"] = datetime.utcnow().isoformat() + "Z"
    approval["review_note"] = review_note
    
    return {
        "success": True,
        "approval": approval,
        "message": "Memory rejected",
        "action": "Memory remains private to submitter"
    }

@router.get("/{approval_id}/status")
async def get_approval_status(
    approval_id: int,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current status of an approval"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Find approval
    approval = next((a for a in APPROVALS_DB if a["id"] == approval_id), None)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    
    # Check access permissions
    can_view = (
        approval["submitted_by"] == user_id or  # Submitter can see
        can_approve_for_team(user_id, approval["team_id"], user_role) or  # Approvers can see
        can_view_team_approvals(user_id, approval["team_id"], user_role)  # Team members can see
    )
    
    if not can_view:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "success": True,
        "approval": approval,
        "permissions": {
            "can_approve": can_approve_for_team(user_id, approval["team_id"], user_role),
            "is_submitter": approval["submitted_by"] == user_id,
            "can_view_team": can_view_team_approvals(user_id, approval["team_id"], user_role)
        }
    }

@router.get("/my-submissions")
async def get_my_submissions(
    status_filter: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List user's submitted approvals"""
    user_id = user["user_id"]
    
    # Get user's submissions
    user_submissions = [a for a in APPROVALS_DB if a["submitted_by"] == user_id]
    
    # Apply status filter
    if status_filter:
        user_submissions = [a for a in user_submissions if a["status"] == status_filter]
    
    # Sort by submission date (newest first)
    user_submissions.sort(key=lambda a: a["submitted_at"], reverse=True)
    
    return {
        "success": True,
        "submissions": user_submissions,
        "count": len(user_submissions),
        "status_filter": status_filter,
        "summary": {
            "pending": len([a for a in user_submissions if a["status"] == "pending"]),
            "approved": len([a for a in user_submissions if a["status"] == "approved"]),
            "rejected": len([a for a in user_submissions if a["status"] == "rejected"])
        }
    }

@router.get("/team/{team_id}/history")
async def get_team_approval_history(
    team_id: int,
    status_filter: Optional[str] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get approval history for a team"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Check team access
    if not can_view_team_approvals(user_id, team_id, user_role):
        raise HTTPException(
            status_code=403, 
            detail="Access denied - not a team member"
        )
    
    # Get team approvals
    team_approvals = [a for a in APPROVALS_DB if a["team_id"] == team_id]
    
    # Apply status filter
    if status_filter:
        team_approvals = [a for a in team_approvals if a["status"] == status_filter]
    
    # Sort by submission date (newest first)
    team_approvals.sort(key=lambda a: a["submitted_at"], reverse=True)
    
    return {
        "success": True,
        "approvals": team_approvals,
        "count": len(team_approvals),
        "team_id": team_id,
        "status_filter": status_filter,
        "summary": {
            "pending": len([a for a in team_approvals if a["status"] == "pending"]),
            "approved": len([a for a in team_approvals if a["status"] == "approved"]),
            "rejected": len([a for a in team_approvals if a["status"] == "rejected"])
        },
        "user_permissions": {
            "can_approve": can_approve_for_team(user_id, team_id, user_role),
            "team_role": get_user_team_role(user_id, team_id)
        }
    }

@router.get("/stats")
async def get_approval_stats(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get approval statistics for the user"""
    user_id = user["user_id"]
    user_role = user["role"]
    
    # Count submissions by user
    user_submissions = [a for a in APPROVALS_DB if a["submitted_by"] == user_id]
    
    # Count approvals by user (as reviewer)
    user_reviews = [a for a in APPROVALS_DB if a["reviewed_by"] == user_id]
    
    # Count pending approvals user can review
    pending_for_review = []
    for approval in APPROVALS_DB:
        if approval["status"] == "pending":
            if can_approve_for_team(user_id, approval["team_id"], user_role):
                pending_for_review.append(approval)
    
    return {
        "success": True,
        "stats": {
            "submissions": {
                "total": len(user_submissions),
                "pending": len([a for a in user_submissions if a["status"] == "pending"]),
                "approved": len([a for a in user_submissions if a["status"] == "approved"]),
                "rejected": len([a for a in user_submissions if a["status"] == "rejected"])
            },
            "reviews": {
                "total": len(user_reviews),
                "approved": len([a for a in user_reviews if a["status"] == "approved"]),
                "rejected": len([a for a in user_reviews if a["status"] == "rejected"])
            },
            "pending_for_review": len(pending_for_review)
        },
        "user_id": user_id,
        "role": user_role
    }
