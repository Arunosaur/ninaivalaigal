"""
Memory Substrate API Endpoints

RESTful API for memory operations using pluggable providers.
"""

from typing import Optional
import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/health")
async def memory_health():
    """Memory API health check"""
    return {"status": "healthy", "service": "memory-api"}
