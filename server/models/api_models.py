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
