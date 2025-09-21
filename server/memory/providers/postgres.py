"""
PostgreSQL Memory Provider

Native implementation using PostgreSQL with pgvector for embeddings.
"""

import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from ..interfaces import MemoryItem, MemoryProviderError


class PostgresMemoryProvider:
    """PostgreSQL-based memory provider with pgvector support"""

    def __init__(self, database_url: str, **kwargs):
        if not database_url:
            raise ValueError("database_url is required for PostgresMemoryProvider")

        self.database_url = database_url
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    async def remember(
        self,
        *,
        text: str,
        meta: Mapping[str, Any] | None = None,
        user_id: int | None = None,
        context_id: str | None = None,
    ) -> MemoryItem:
        """Store a memory item in PostgreSQL"""
        try:
            memory_id = str(uuid.uuid4())
            created_at = datetime.utcnow()
            meta_json = json.dumps(meta or {})

            with self.SessionLocal() as session:
                # Insert into memories table
                # Note: In a real implementation, you'd generate embeddings here
                result = session.execute(
                    text(
                        """
                        INSERT INTO memories (id, user_id, context_id, content, metadata, created_at)
                        VALUES (:id, :user_id, :context_id, :content, :metadata, :created_at)
                        RETURNING id
                    """
                    ),
                    {
                        "id": memory_id,
                        "user_id": user_id,
                        "context_id": context_id,
                        "content": text,
                        "metadata": meta_json,
                        "created_at": created_at,
                    },
                )
                session.commit()

                return MemoryItem(
                    id=memory_id,
                    text=text,
                    meta=meta or {},
                    user_id=user_id,
                    context_id=context_id,
                    created_at=created_at.isoformat(),
                )

        except SQLAlchemyError as e:
            raise MemoryProviderError(f"Failed to store memory: {e}")

    async def recall(
        self,
        *,
        query: str,
        k: int = 5,
        user_id: int | None = None,
        context_id: str | None = None,
    ) -> Sequence[MemoryItem]:
        """Retrieve memory items by similarity search"""
        try:
            with self.SessionLocal() as session:
                # Simple text search for now - in production you'd use vector similarity
                sql_query = """
                    SELECT id, user_id, context_id, content, metadata, created_at
                    FROM memories
                    WHERE content ILIKE :query
                """
                params = {"query": f"%{query}%", "limit": k}

                # Add user/context filters if provided
                if user_id is not None:
                    sql_query += " AND user_id = :user_id"
                    params["user_id"] = user_id

                if context_id is not None:
                    sql_query += " AND context_id = :context_id"
                    params["context_id"] = context_id

                sql_query += " ORDER BY created_at DESC LIMIT :limit"

                result = session.execute(text(sql_query), params)
                rows = result.fetchall()

                memories = []
                for row in rows:
                    memories.append(
                        MemoryItem(
                            id=str(row.id),
                            text=row.content,
                            meta=json.loads(row.metadata) if row.metadata else {},
                            user_id=row.user_id,
                            context_id=row.context_id,
                            created_at=row.created_at.isoformat()
                            if row.created_at
                            else None,
                        )
                    )

                return memories

        except SQLAlchemyError as e:
            raise MemoryProviderError(f"Failed to recall memories: {e}")

    async def delete(self, *, id: str, user_id: int | None = None) -> bool:
        """Delete a memory item"""
        try:
            with self.SessionLocal() as session:
                sql_query = "DELETE FROM memories WHERE id = :id"
                params = {"id": id}

                # Add user filter for security
                if user_id is not None:
                    sql_query += " AND user_id = :user_id"
                    params["user_id"] = user_id

                result = session.execute(text(sql_query), params)
                session.commit()

                return result.rowcount > 0

        except SQLAlchemyError as e:
            raise MemoryProviderError(f"Failed to delete memory: {e}")

    async def list_memories(
        self,
        *,
        user_id: int | None = None,
        context_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[MemoryItem]:
        """List memory items with pagination"""
        try:
            with self.SessionLocal() as session:
                sql_query = """
                    SELECT id, user_id, context_id, content, metadata, created_at
                    FROM memories
                    WHERE 1=1
                """
                params = {"limit": limit, "offset": offset}

                if user_id is not None:
                    sql_query += " AND user_id = :user_id"
                    params["user_id"] = user_id

                if context_id is not None:
                    sql_query += " AND context_id = :context_id"
                    params["context_id"] = context_id

                sql_query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"

                result = session.execute(text(sql_query), params)
                rows = result.fetchall()

                memories = []
                for row in rows:
                    memories.append(
                        MemoryItem(
                            id=str(row.id),
                            text=row.content,
                            meta=json.loads(row.metadata) if row.metadata else {},
                            user_id=row.user_id,
                            context_id=row.context_id,
                            created_at=row.created_at.isoformat()
                            if row.created_at
                            else None,
                        )
                    )

                return memories

        except SQLAlchemyError as e:
            raise MemoryProviderError(f"Failed to list memories: {e}")

    async def health_check(self) -> bool:
        """Check if PostgreSQL connection is healthy"""
        try:
            with self.SessionLocal() as session:
                session.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError:
            return False
