#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Approval Workflow Router
Extracted from main.py for better code organization
"""

from approval_workflow import ApprovalWorkflowManager
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException
from models.api_models import ApprovalAction, CrossTeamAccessRequest

from auth import get_current_user

# Initialize router
router = APIRouter(prefix="/approvals", tags=["approvals"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from server.config import get_dynamic_database_url

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


@router.post("/approval-action")
async def handle_approval_action(
    approval_action: ApprovalAction,
    current_user: User = Depends(get_current_user),
    approval_manager: ApprovalWorkflowManager = Depends(get_approval_manager),
):
    """Approve or reject an approval request"""
    if approval_action.action == "approve":
        _ = approval_manager.approve_request(approval_action.request_id, current_user.id)
    elif approval_action.action == "reject":
        _ = approval_manager.reject_request(approval_action.request_id, current_user.id, approval_action.reason)
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'approve' or 'reject'")


@router.get("/pending")
async def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    approval_manager: ApprovalWorkflowManager = Depends(get_approval_manager),
):
    """Get pending approval requests for user's teams"""
    user_teams = db.get_user_teams(current_user.id)
    team_ids = [team.id for team in user_teams]

    all_requests = []
    for team_id in team_ids:
        requests = approval_manager.get_pending_requests_for_team(team_id)
        all_requests.extend(requests)

    return {"pending_requests": all_requests}


@router.get("/status/{request_id}")
async def get_request_status(
    request_id: str,
    current_user: User = Depends(get_current_user),
    approval_manager: ApprovalWorkflowManager = Depends(get_approval_manager),
):
    """Get status of a specific approval request"""
    result = approval_manager.get_request_status(request_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
