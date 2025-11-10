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
SPEC-090: Enhanced with ACP framework endpoints
"""

import uuid
from typing import Optional

from approval_acp import ACPApprovalManager, ApprovalChain, ApprovalEvent, ApprovalState
from approval_workflow import ApprovalWorkflowManager
from auth_service import get_current_user
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException, Request, status
from models.api_models import (
    ApprovalAction,
    ApprovalChainResponse,
    ApprovalEventResponse,
    ApprovalEventsResponse,
    CrossTeamAccessRequest,
    DraftApprovalRequest,
    FinalizeApprovalRequest,
    SubmitApprovalRequest,
)

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


def get_acp_approval_manager(
    request: Request,
    db: DatabaseManager = Depends(get_db),
) -> ACPApprovalManager:
    """Get ACP approval manager with queue and event publisher"""
    # Get queue manager from app state or import directly
    try:
        queue_manager = getattr(request.app.state, "queue_manager", None)
        if queue_manager is None:
            from redis_queue import queue_manager as default_queue_manager

            queue_manager = default_queue_manager
    except (AttributeError, ImportError):
        queue_manager = None

    # Get event publisher from app state
    event_publisher = getattr(request.app.state, "event_publisher", None) if hasattr(request, "app") else None

    return ACPApprovalManager(db, queue_manager, event_publisher)


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


# ============================================================================
# SPEC-090: ACP Framework Endpoints
# ============================================================================


@router.post("/draft", status_code=status.HTTP_201_CREATED)
async def create_draft_approval_request(
    draft_request: DraftApprovalRequest,
    current_user: User = Depends(get_current_user),
    acp_manager: ACPApprovalManager = Depends(get_acp_approval_manager),
):
    """
    Create a draft approval request (SPEC-090).

    Draft requests are not yet submitted and can be edited before submission.
    """
    try:
        result = await acp_manager.create_draft_request(
            context_id=uuid.UUID(draft_request.context_id),
            requesting_team_id=uuid.UUID(draft_request.requesting_team_id),
            target_team_id=uuid.UUID(draft_request.target_team_id),
            requested_by=current_user.id,
            permission_level=draft_request.permission_level,
            justification=draft_request.justification,
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create draft request"))

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create draft request: {str(e)}")


@router.post("/{request_id}/submit")
async def submit_approval_request(
    request_id: str,
    submit_data: Optional[SubmitApprovalRequest] = None,
    current_user: User = Depends(get_current_user),
    acp_manager: ACPApprovalManager = Depends(get_acp_approval_manager),
):
    """
    Submit a draft approval request for approval (SPEC-090).

    Transitions the request from DRAFT to PENDING state and creates approval chain.
    """
    try:
        req_id = uuid.UUID(request_id)
        result = await acp_manager.submit_request(req_id, submitted_by=current_user.id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to submit request"))

        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit request: {str(e)}")


@router.post("/{request_id}/finalize")
async def finalize_approval_request(
    request_id: str,
    finalize_data: Optional[FinalizeApprovalRequest] = None,
    current_user: User = Depends(get_current_user),
    acp_manager: ACPApprovalManager = Depends(get_acp_approval_manager),
):
    """
    Finalize an approved or rejected request (SPEC-090).

    Transitions the request to FINALIZED state (terminal state).
    """
    try:
        req_id = uuid.UUID(request_id)
        result = await acp_manager.finalize_request(req_id, finalized_by=current_user.id)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to finalize request"))

        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize request: {str(e)}")


@router.get("/{request_id}/chain")
async def get_approval_chain(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get approval chain for a request (SPEC-090).

    Returns all steps in the approval chain with their status.
    """
    try:
        req_id = uuid.UUID(request_id)
        session = db.get_session()

        try:
            chain_steps = (
                session.query(ApprovalChain).filter_by(request_id=req_id).order_by(ApprovalChain.step_number).all()
            )

            if not chain_steps:
                raise HTTPException(status_code=404, detail="Approval chain not found")

            steps = []
            current_step = None
            for i, step in enumerate(chain_steps, 1):
                step_data = {
                    "step_number": step.step_number,
                    "approver_id": str(step.approver_id) if step.approver_id else None,
                    "approver_role": step.approver_role,
                    "status": step.status,
                    "approved_by": str(step.approved_by) if step.approved_by else None,
                    "approved_at": step.approved_at.isoformat() if step.approved_at else None,
                    "rejected_by": str(step.rejected_by) if step.rejected_by else None,
                    "rejected_at": step.rejected_at.isoformat() if step.rejected_at else None,
                    "notes": step.notes,
                }
                steps.append(step_data)

                if step.status == ApprovalState.PENDING.value:
                    current_step = step.step_number

            # Get request status
            from approval_workflow import CrossTeamApprovalRequest

            request = session.query(CrossTeamApprovalRequest).filter_by(id=req_id).first()
            request_status = request.status if request else "unknown"

            return ApprovalChainResponse(
                request_id=str(req_id),
                steps=steps,
                current_step=current_step,
                status=request_status,
            )
        finally:
            session.close()

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval chain: {str(e)}")


@router.get("/{request_id}/events")
async def get_approval_events(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get event history for an approval request (SPEC-090).

    Returns all events in the approval workflow for audit and rollback purposes.
    """
    try:
        req_id = uuid.UUID(request_id)
        session = db.get_session()

        try:
            events = session.query(ApprovalEvent).filter_by(request_id=req_id).order_by(ApprovalEvent.timestamp).all()

            event_responses = []
            for event in events:
                event_responses.append(
                    ApprovalEventResponse(
                        event_id=str(event.id),
                        event_type=event.event_type,
                        previous_state=event.previous_state,
                        new_state=event.new_state,
                        performed_by=str(event.performed_by) if event.performed_by else None,
                        timestamp=event.timestamp.isoformat(),
                        event_data=event.event_data or {},
                    )
                )

            return ApprovalEventsResponse(
                request_id=str(req_id),
                events=event_responses,
                total=len(event_responses),
            )
        finally:
            session.close()

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval events: {str(e)}")


@router.post("/{request_id}/retry")
async def retry_approval_workflow(
    request_id: str,
    current_user: User = Depends(get_current_user),
    acp_manager: ACPApprovalManager = Depends(get_acp_approval_manager),
):
    """
    Retry a failed approval workflow (SPEC-090).

    Retries the workflow with exponential backoff.
    """
    try:
        req_id = uuid.UUID(request_id)
        result = await acp_manager.workflow_engine.retry_failed_workflow(req_id, retry_count=0)

        if not result:
            raise HTTPException(status_code=400, detail="Retry failed or max retries exceeded")

        return {"success": True, "message": "Workflow retry initiated", "request_id": str(req_id)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry workflow: {str(e)}")
