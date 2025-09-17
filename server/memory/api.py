from fastapi import APIRouter, Depends, Request
from .models import MemoryRecord, MemoryQuery, MemoryShare
from .store import memory_store

router = APIRouter(prefix="/memory")

@router.post("/write")
async def write_memory(record: MemoryRecord, request: Request):
    user = request.state.user
    return memory_store.write(user["user_id"], record)

@router.post("/query")
async def query_memory(query: MemoryQuery, request: Request):
    user = request.state.user
    return memory_store.query(user["user_id"], query)

@router.post("/share")
async def share_memory(share: MemoryShare, request: Request):
    user = request.state.user
    return memory_store.share(user["user_id"], share)
