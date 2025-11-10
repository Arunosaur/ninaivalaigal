#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
API Data Models for ninaivalaigal
Extracted from main.py for better organization
"""

from pydantic import BaseModel


class MemoryPayload(BaseModel):
    """Memory payload for storing memories"""

    type: str
    source: str
    data: dict


class OrganizationCreate(BaseModel):
    """Model for creating organizations"""

    name: str
    description: str | None = None


class TeamCreate(BaseModel):
    """Model for creating teams"""

    name: str
    organization_id: int | None = None
    description: str | None = None


class TeamMemberAdd(BaseModel):
    """Model for adding team members"""

    user_id: int
    role: str = "member"


class ContextCreate(BaseModel):
    """Model for creating contexts"""

    name: str
    description: str | None = None
    scope: str = "personal"  # "personal", "team", "organization"
    team_id: int | None = None
    organization_id: int | None = None


class ContextShare(BaseModel):
    """Model for sharing contexts"""

    target_type: str  # "user", "team", or "organization"
    target_id: int
    permission_level: str  # "read", "write", "admin", "owner"


class ContextTransfer(BaseModel):
    """Model for transferring contexts"""

    target_type: str  # "user", "team", or "organization"
    target_id: int


class CrossTeamAccessRequest(BaseModel):
    """Model for cross-team access requests"""

    context_id: int
    target_team_id: int
    permission_level: str  # "read", "write", "admin"
    justification: str | None = None


class ApprovalAction(BaseModel):
    """Model for approval actions"""

    request_id: int
    action: str  # "approve" or "reject"
    reason: str | None = None


# SPEC-090: ACP Framework Models
class DraftApprovalRequest(BaseModel):
    """Model for creating draft approval requests"""

    context_id: str  # UUID
    requesting_team_id: str  # UUID
    target_team_id: str  # UUID
    permission_level: str  # "read", "write", "admin"
    justification: str | None = None


class SubmitApprovalRequest(BaseModel):
    """Model for submitting a draft approval request"""

    request_id: str  # UUID
    notes: str | None = None


class FinalizeApprovalRequest(BaseModel):
    """Model for finalizing an approval request"""

    request_id: str  # UUID
    notes: str | None = None


class ApprovalChainResponse(BaseModel):
    """Response model for approval chain"""

    request_id: str
    steps: list[dict]
    current_step: int | None = None
    status: str


class ApprovalEventResponse(BaseModel):
    """Response model for approval event"""

    event_id: str
    event_type: str
    previous_state: str | None = None
    new_state: str | None = None
    performed_by: str | None = None
    timestamp: str
    event_data: dict | None = None


class ApprovalEventsResponse(BaseModel):
    """Response model for approval event history"""

    request_id: str
    events: list[ApprovalEventResponse]
    total: int


# SPEC-091: A2A Context Propagation Models
class A2AContextRequest(BaseModel):
    """Model for creating A2A context envelope"""

    source_agent: str
    target_agent: str
    intent: str
    scope: dict  # Context scope (memory_ids, context_ids, team_ids, etc.)
    payload: dict  # Context payload data
    constraints: dict | None = None  # Optional constraints
    ttl_seconds: int = 3600  # Time-to-live in seconds (default: 1 hour)
    parent_envelope_id: str | None = None  # Parent context for lineage


class A2AContextResponse(BaseModel):
    """Response model for A2A context"""

    envelope_id: str
    source_agent: str
    target_agent: str
    intent: str
    scope: dict
    constraints: dict | None = None
    payload: dict
    signature: str | None = None
    expires_at: str
    created_at: str
    status: str
    version: str


class A2AContextLineageResponse(BaseModel):
    """Response model for A2A context lineage"""

    envelope_id: str
    lineage: list[dict]
    total_versions: int


class A2AContextListResponse(BaseModel):
    """Response model for listing A2A contexts"""

    contexts: list[A2AContextResponse]
    total: int
