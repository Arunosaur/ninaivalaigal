# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Common Pydantic models for all services."""

from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """Standard error codes."""

    UNSPECIFIED = "ERROR_CODE_UNSPECIFIED"
    INVALID_INPUT = "ERROR_CODE_INVALID_INPUT"
    NOT_FOUND = "ERROR_CODE_NOT_FOUND"
    UNAUTHORIZED = "ERROR_CODE_UNAUTHORIZED"
    FORBIDDEN = "ERROR_CODE_FORBIDDEN"
    CONFLICT = "ERROR_CODE_CONFLICT"
    INTERNAL = "ERROR_CODE_INTERNAL"
    SERVICE_UNAVAILABLE = "ERROR_CODE_SERVICE_UNAVAILABLE"
    RATE_LIMITED = "ERROR_CODE_RATE_LIMITED"


class Error(BaseModel):
    """Standard error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, str]] = Field(default=None, description="Additional error details")
    timestamp: Optional[str] = Field(default=None, description="Timestamp when error occurred")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")


class ValidationError(BaseModel):
    """Validation error for field-level issues."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    code: str = Field(..., description="Error code specific to validation")


class PageRequest(BaseModel):
    """Pagination request parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    sort_by: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default="asc", description="Sort direction (asc/desc)")


class PageInfo(BaseModel):
    """Pagination metadata in response."""

    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class CursorRequest(BaseModel):
    """Cursor-based pagination request."""

    cursor: Optional[str] = Field(default=None, description="Cursor for next page")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items to return")


class CursorInfo(BaseModel):
    """Cursor-based pagination response."""

    next_cursor: Optional[str] = Field(default=None, description="Next cursor")
    previous_cursor: Optional[str] = Field(default=None, description="Previous cursor")
    has_more: bool = Field(..., description="Whether there are more items")
