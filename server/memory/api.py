"""api module."""

from fastapi import APIRouter, Request

from .models import MemoryQuery, MemoryRecord, MemoryShare
from .store import memory_store

router = APIRouter(prefix="/memory")


@router.post("/write")
async def write_memory(record: MemoryRecord, request: Request):
    """Write a new memory record for the authenticated user."""
    user = request.state.user
    return memory_store.write(user["user_id"], record)


@router.post("/query")
async def query_memory(query: MemoryQuery, request: Request):
    """Query memories for the authenticated user."""
    user = request.state.user
    return memory_store.query(user["user_id"], query)


@router.post("/share")
async def share_memory(share: MemoryShare, request: Request):
    """Share a memory with other users."""
    user = request.state.user
    return memory_store.share(user["user_id"], share)
