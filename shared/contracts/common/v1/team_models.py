# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Team management Pydantic models."""

from typing import Optional

from pydantic import BaseModel, Field


class TeamCreateRequest(BaseModel):
    """Request model for creating a team."""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    organization_id: Optional[str] = Field(None, description="Organization ID (UUID)")
    description: Optional[str] = Field(None, description="Team description")


class TeamUpdateRequest(BaseModel):
    """Request model for updating a team."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Team name")
    description: Optional[str] = Field(None, description="Team description")


class TeamResponse(BaseModel):
    """Response model for team data."""

    id: str = Field(..., description="Team ID (UUID)")
    name: str = Field(..., description="Team name")
    organization_id: Optional[str] = Field(None, description="Organization ID (UUID)")
    description: Optional[str] = Field(None, description="Team description")
    created_by: str = Field(..., description="Creator user ID (UUID)")
    created_at: str = Field(..., description="Creation timestamp")
    is_active: bool = Field(default=True, description="Active status")
    member_count: int = Field(default=0, description="Number of members")

    class Config:
        """Pydantic config."""

        from_attributes = True


class TeamMemberAddRequest(BaseModel):
    """Request model for adding a team member."""

    user_id: str = Field(..., description="User ID (UUID)")
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$", description="Member role")


class TeamMemberUpdateRequest(BaseModel):
    """Request model for updating a team member's role."""

    role: str = Field(..., pattern="^(owner|admin|member|viewer)$", description="Member role")


class TeamMemberResponse(BaseModel):
    """Response model for team member data."""

    id: str = Field(..., description="Member ID (UUID)")
    team_id: str = Field(..., description="Team ID (UUID)")
    user_id: str = Field(..., description="User ID (UUID)")
    role: str = Field(..., description="Member role")
    joined_at: str = Field(..., description="Join timestamp")
    is_active: bool = Field(default=True, description="Active status")
    user_name: Optional[str] = Field(None, description="User display name")
    user_email: Optional[str] = Field(None, description="User email")

    class Config:
        """Pydantic config."""

        from_attributes = True
