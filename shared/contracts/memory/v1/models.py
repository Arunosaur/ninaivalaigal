# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Memory service Pydantic models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Memory(BaseModel):
    """Memory entity."""

    id: str = Field(..., description="Memory ID")
    user_id: str = Field(..., description="User ID")
    content: str = Field(..., description="Memory content")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Memory metadata")
    tags: List[str] = Field(default_factory=list, description="Memory tags")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")


class CreateMemoryRequest(BaseModel):
    """Create memory request."""

    user_id: str = Field(..., description="User ID")
    content: str = Field(..., min_length=1, description="Memory content")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Memory metadata")
    tags: List[str] = Field(default_factory=list, description="Memory tags")


class GetMemoryRequest(BaseModel):
    """Get memory request."""

    memory_id: str = Field(..., description="Memory ID")


class UpdateMemoryRequest(BaseModel):
    """Update memory request."""

    memory_id: str = Field(..., description="Memory ID")
    content: Optional[str] = Field(default=None, description="New content")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="New metadata")
    tags: Optional[List[str]] = Field(default=None, description="New tags")


class DeleteMemoryRequest(BaseModel):
    """Delete memory request."""

    memory_id: str = Field(..., description="Memory ID")


class ListMemoriesRequest(BaseModel):
    """List memories request."""

    user_id: str = Field(..., description="User ID")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")


class MemoryList(BaseModel):
    """List of memories."""

    memories: List[Memory] = Field(default_factory=list, description="Memories")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
