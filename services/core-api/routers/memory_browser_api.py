#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Memory browser endpoints for authenticated users."""

import json
import uuid
from datetime import datetime
from typing import Any, List, Optional

from auth_service import get_current_user
from database import DatabaseManager, Memory, User
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc


def get_db():
    """Get database manager with dynamic configuration."""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    """Request model for creating a new memory"""

    content: str = Field(..., min_length=1, description="Memory content")
    context: str = Field(default="general", description="Memory context/category")
    tags: Optional[List[str]] = Field(default=None, description="Tags for the memory")
    pinned: bool = Field(default=False, description="Whether to pin this memory")


def _serialize_memory(record: Memory) -> dict[str, Any]:
    # Handle both string and dict data due to VIEW mapping
    if isinstance(record.data, str):
        try:
            payload = json.loads(record.data) if record.data else {}
        except (json.JSONDecodeError, TypeError):
            payload = {"content": record.data or "Untitled memory"}
    else:
        payload = record.data or {}

    content = payload.get("content") or payload.get("text") or payload.get("body") or "Untitled memory"

    tags = payload.get("tags")
    if not isinstance(tags, list):
        tags = []

    try:
        size = len(json.dumps(payload).encode("utf-8"))
    except Exception:
        size = 0

    return {
        "id": str(record.id),
        "content": content,
        "context": record.context,
        "tags": tags,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        "pinned": bool(payload.get("pinned", False)),
        "archived": bool(payload.get("archived", False)),
        "relevance_score": float(payload.get("relevance_score", 0.0) or 0.0),
        "size": size,
    }


@router.get("/memories")
def list_memories(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List the authenticated user's memories for the browser UI."""

    session = db.get_session()
    try:
        # Debug: Check total memories for this user
        total_count = session.query(Memory).filter(Memory.user_id == current_user.id).count()
        print(f"[DEBUG] Total memories for user {current_user.id}: {total_count}")

        query = (
            session.query(Memory)
            .filter(Memory.user_id == current_user.id)
            .order_by(desc(Memory.created_at))
            .offset(offset)
            .limit(limit)
        )

        records = query.all()
        print(f"[DEBUG] Query returned {len(records)} records")
        serialized = [_serialize_memory(memory) for memory in records]

        return {
            "memories": serialized,
            "count": len(serialized),
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - safeguard
        raise HTTPException(status_code=500, detail=f"Failed to load memories: {str(exc)}")
    finally:
        session.close()


@router.post("/memories", status_code=201)
def create_memory(
    memory_data: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Create a new memory for the authenticated user."""

    session = db.get_session()
    try:
        # Create memory data payload
        data_payload = {
            "content": memory_data.content,
            "tags": memory_data.tags or [],
            "pinned": memory_data.pinned,
            "archived": False,
            "relevance_score": 1.0,
        }

        # Create new memory record
        new_memory = Memory(
            id=uuid.uuid4(),
            user_id=current_user.id,
            context=memory_data.context,
            type="user_created",  # Required field
            source="web_ui",  # Required field
            data=data_payload,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add(new_memory)
        session.commit()
        session.refresh(new_memory)

        print(f"[DEBUG] Created memory {new_memory.id} for user {current_user.id}")

        return {"success": True, "memory": _serialize_memory(new_memory), "message": "Memory created successfully"}

    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Failed to create memory: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to create memory: {str(exc)}")
    finally:
        session.close()


class MemoryUpdate(BaseModel):
    """Request model for updating a memory"""

    content: Optional[str] = Field(None, min_length=1, description="Memory content")
    context: Optional[str] = Field(None, description="Memory context/category")
    tags: Optional[List[str]] = Field(None, description="Tags for the memory")
    pinned: Optional[bool] = Field(None, description="Whether to pin this memory")
    archived: Optional[bool] = Field(None, description="Whether to archive this memory")


@router.get("/memories/{memory_id}")
def get_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get a specific memory by ID for the authenticated user."""

    session = db.get_session()
    try:
        # Parse UUID
        try:
            mem_uuid = uuid.UUID(memory_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid memory ID format")

        # Query memory with user isolation
        memory = session.query(Memory).filter(Memory.id == mem_uuid, Memory.user_id == current_user.id).first()

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"success": True, "memory": _serialize_memory(memory)}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(exc)}")
    finally:
        session.close()


@router.put("/memories/{memory_id}")
def update_memory(
    memory_id: str,
    memory_data: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Update a specific memory for the authenticated user."""

    session = db.get_session()
    try:
        # Parse UUID
        try:
            mem_uuid = uuid.UUID(memory_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid memory ID format")

        # Query memory with user isolation
        memory = session.query(Memory).filter(Memory.id == mem_uuid, Memory.user_id == current_user.id).first()

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        # Update memory data payload - handle string data from VIEW
        if isinstance(memory.data, str):
            try:
                data_payload = json.loads(memory.data) if memory.data else {}
            except (json.JSONDecodeError, TypeError):
                data_payload = {"content": memory.data or "Untitled memory"}
        else:
            data_payload = memory.data or {}

        # Update fields if provided
        if memory_data.content is not None:
            data_payload["content"] = memory_data.content

        if memory_data.tags is not None:
            data_payload["tags"] = memory_data.tags

        if memory_data.pinned is not None:
            data_payload["pinned"] = memory_data.pinned

        if memory_data.archived is not None:
            data_payload["archived"] = memory_data.archived

        # Update memory record
        memory.data = data_payload
        if memory_data.context is not None:
            memory.context = memory_data.context
        memory.updated_at = datetime.utcnow()

        session.commit()
        session.refresh(memory)

        print(f"[DEBUG] Updated memory {memory.id} for user {current_user.id}")

        return {
            "success": True,
            "memory": _serialize_memory(memory),
            "message": "Memory updated successfully",
        }

    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Failed to update memory: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to update memory: {str(exc)}")
    finally:
        session.close()


@router.delete("/memories/{memory_id}")
def delete_memory(
    memory_id: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Delete a specific memory for the authenticated user."""

    session = db.get_session()
    try:
        # Parse UUID
        try:
            mem_uuid = uuid.UUID(memory_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid memory ID format")

        # Query memory with user isolation
        memory = session.query(Memory).filter(Memory.id == mem_uuid, Memory.user_id == current_user.id).first()

        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")

        # Delete the memory
        session.delete(memory)
        session.commit()

        print(f"[DEBUG] Deleted memory {memory_id} for user {current_user.id}")

        return {"success": True, "message": "Memory deleted successfully"}

    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Failed to delete memory: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(exc)}")
    finally:
        session.close()
