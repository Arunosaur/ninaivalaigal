#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Development Tools Router
Quick endpoints for seeding test data and development utilities
"""

from datetime import datetime, timedelta
from uuid import uuid4

from database import DatabaseManager, Memory, User
from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user

router = APIRouter(prefix="/dev", tags=["dev-tools"])


def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.post("/seed-activity")
async def seed_user_activity(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Seed realistic activity data for the current user (development only)

    Creates:
    - 5-10 sample memories with various contexts
    - 2-3 team memberships (simulated)
    - Recent activity timestamps
    """
    session = db.get_session()
    try:
        # Create sample memories with different contexts
        memories_data = [
            {
                "data": {
                    "content": (
                        "Project Alpha Q4 planning session notes - "
                        "discussed roadmap priorities and resource allocation"
                    ),
                    "tags": ["q4", "planning"],
                },
                "context": "work-project",
                "type": "meeting-notes",
                "created_at": datetime.utcnow() - timedelta(minutes=2),
            },
            {
                "data": {
                    "content": ("Research findings on memory retention algorithms " "and cognitive load optimization"),
                    "tags": ["research", "algorithms"],
                },
                "context": "research",
                "type": "document",
                "created_at": datetime.utcnow() - timedelta(hours=3),
            },
            {
                "data": {
                    "content": ("Team standup: Sprint 12 progress update - " "8 stories completed, 2 in progress"),
                    "tags": ["standup", "sprint12"],
                },
                "context": "team-standup",
                "type": "meeting-notes",
                "created_at": datetime.utcnow() - timedelta(hours=24),
            },
            {
                "data": {
                    "content": (
                        "Customer feedback analysis: 85% satisfaction rate, " "key improvement areas identified"
                    ),
                    "tags": ["feedback", "analysis"],
                },
                "context": "customer-insights",
                "type": "analysis",
                "created_at": datetime.utcnow() - timedelta(days=2),
            },
            {
                "data": {
                    "content": ("Architecture decision: Migrating to event-driven " "microservices for scalability"),
                    "tags": ["architecture", "decision"],
                },
                "context": "architecture",
                "type": "decision-record",
                "created_at": datetime.utcnow() - timedelta(days=5),
            },
        ]

        created_memories = []
        for mem_data in memories_data:
            memory = Memory(
                id=uuid4(),
                user_id=current_user.id,
                data=mem_data["data"],
                context=mem_data["context"],
                type=mem_data["type"],
                source="web-ui",
                created_at=mem_data["created_at"],
                updated_at=mem_data["created_at"],
            )
            session.add(memory)
            created_memories.append(mem_data["context"])

        session.commit()

        return {
            "success": True,
            "message": "Activity data seeded successfully",
            "created": {
                "memories": len(memories_data),
                "contexts": created_memories,
            },
            "note": "Refresh your dashboard to see the new activity",
        }

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {str(e)}")
    finally:
        session.close()


@router.post("/clear-activity")
async def clear_user_activity(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Clear all activity data for the current user (development only)
    Use with caution - deletes all memories!
    """
    session = db.get_session()
    try:
        # Delete all user's memories
        deleted_count = session.query(Memory).filter(Memory.user_id == current_user.id).delete()
        session.commit()

        return {"success": True, "message": "Activity data cleared", "deleted_memories": deleted_count}

    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")
    finally:
        session.close()


@router.get("/stats")
async def get_dev_stats(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Quick stats for development"""
    session = db.get_session()
    try:
        from sqlalchemy import func

        memory_count = session.query(func.count(Memory.id)).filter(Memory.user_id == current_user.id).scalar()

        return {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "memory_count": memory_count,
            "account_type": current_user.account_type,
            "has_data": memory_count > 0,
        }
    finally:
        session.close()
