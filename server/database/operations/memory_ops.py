"""
Memory Operations
Database operations for memory management
"""

from ..manager import DatabaseManager
from ..models import Context, Memory


class MemoryOperations(DatabaseManager):
    """Memory-related database operations"""

    def add_memory(
        self,
        context: str,
        memory_type: str,
        content: str,
        metadata: dict = None,
        user_id: int = None,
    ):
        """Add a new memory to a context"""
        session = self.get_session()
        try:
            # Resolve context
            context_obj = self.resolve_context(context, user_id, session=session)
            if not context_obj:
                # Create context if it doesn't exist
                context_obj = Context(
                    name=context, owner_id=user_id, scope="personal", is_active=True
                )
                session.add(context_obj)
                session.flush()  # Get the ID

            memory = Memory(
                context_id=context_obj.id,
                memory_type=memory_type,
                content=content,
                metadata=metadata or {},
                user_id=user_id,
            )

            session.add(memory)
            session.commit()
            return memory
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_memories(self, context: str, user_id: int = None):
        """Get all memories from a specific context"""
        session = self.get_session()
        try:
            if user_id:
                # Get context accessible to user
                context_obj = self.resolve_context(context, user_id, session=session)
                if not context_obj:
                    return []

                memories = (
                    session.query(Memory)
                    .filter(Memory.context_id == context_obj.id)
                    .order_by(Memory.created_at.desc())
                    .all()
                )
            else:
                # Admin access - get all memories from context
                context_obj = (
                    session.query(Context).filter(Context.name == context).first()
                )
                if not context_obj:
                    return []

                memories = (
                    session.query(Memory)
                    .filter(Memory.context_id == context_obj.id)
                    .order_by(Memory.created_at.desc())
                    .all()
                )

            return [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "memory_type": mem.memory_type,
                    "metadata": mem.metadata,
                    "created_at": (
                        mem.created_at.isoformat() if mem.created_at else None
                    ),
                    "context": context,
                }
                for mem in memories
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_all_memories(self, user_id: int = None):
        """Get all memories accessible to a user"""
        session = self.get_session()
        try:
            if user_id:
                # Get memories from contexts accessible to user
                memories = (
                    session.query(Memory)
                    .join(Context)
                    .filter(Context.owner_id == user_id)
                    .order_by(Memory.created_at.desc())
                    .all()
                )
            else:
                # Admin access - get all memories
                memories = (
                    session.query(Memory).order_by(Memory.created_at.desc()).all()
                )

            return [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "memory_type": mem.memory_type,
                    "metadata": mem.metadata,
                    "created_at": (
                        mem.created_at.isoformat() if mem.created_at else None
                    ),
                    "context": mem.context.name if mem.context else None,
                }
                for mem in memories
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_recent_memories(self, limit: int = 50, user_id: int = None):
        """Get recent memories with optional user filtering"""
        session = self.get_session()
        try:
            if user_id:
                # Get recent memories from user's contexts
                memories = (
                    session.query(Memory)
                    .join(Context)
                    .filter(Context.owner_id == user_id)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .all()
                )
            else:
                # Admin access - get all recent memories
                memories = (
                    session.query(Memory)
                    .order_by(Memory.created_at.desc())
                    .limit(limit)
                    .all()
                )

            return [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "memory_type": mem.memory_type,
                    "metadata": mem.metadata,
                    "created_at": (
                        mem.created_at.isoformat() if mem.created_at else None
                    ),
                    "context": mem.context.name if mem.context else None,
                }
                for mem in memories
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def search_memories(
        self,
        query: str,
        user_id: int = None,
        context: str = None,
        memory_type: str = None,
        limit: int = 50,
    ):
        """Search memories with various filters"""
        session = self.get_session()
        try:
            # Base query
            query_obj = session.query(Memory)

            # Filter by user access
            if user_id:
                query_obj = query_obj.join(Context).filter(Context.owner_id == user_id)

            # Filter by context
            if context:
                context_obj = self.resolve_context(context, user_id, session=session)
                if context_obj:
                    query_obj = query_obj.filter(Memory.context_id == context_obj.id)
                else:
                    return []  # Context not found or not accessible

            # Filter by memory type
            if memory_type:
                query_obj = query_obj.filter(Memory.memory_type == memory_type)

            # Text search in content
            if query:
                query_obj = query_obj.filter(Memory.content.ilike(f"%{query}%"))

            # Order and limit
            memories = query_obj.order_by(Memory.created_at.desc()).limit(limit).all()

            return [
                {
                    "id": mem.id,
                    "content": mem.content,
                    "memory_type": mem.memory_type,
                    "metadata": mem.metadata,
                    "created_at": (
                        mem.created_at.isoformat() if mem.created_at else None
                    ),
                    "context": mem.context.name if mem.context else None,
                    "relevance_score": 1.0,  # TODO: Implement proper relevance scoring
                }
                for mem in memories
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def delete_memory(self, memory_id: int, user_id: int = None):
        """Delete a specific memory"""
        session = self.get_session()
        try:
            query = session.query(Memory).filter(Memory.id == memory_id)

            # If user_id provided, ensure user owns the memory's context
            if user_id:
                query = query.join(Context).filter(Context.owner_id == user_id)

            memory = query.first()
            if not memory:
                raise ValueError("Memory not found or not accessible")

            session.delete(memory)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_memory(
        self,
        memory_id: int,
        content: str = None,
        metadata: dict = None,
        user_id: int = None,
    ):
        """Update an existing memory"""
        session = self.get_session()
        try:
            query = session.query(Memory).filter(Memory.id == memory_id)

            # If user_id provided, ensure user owns the memory's context
            if user_id:
                query = query.join(Context).filter(Context.owner_id == user_id)

            memory = query.first()
            if not memory:
                raise ValueError("Memory not found or not accessible")

            # Update fields
            if content is not None:
                memory.content = content
            if metadata is not None:
                memory.metadata = metadata

            session.commit()
            return memory
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_memory_by_id(self, memory_id: int, user_id: int = None):
        """Get a specific memory by ID"""
        session = self.get_session()
        try:
            query = session.query(Memory).filter(Memory.id == memory_id)

            # If user_id provided, ensure user owns the memory's context
            if user_id:
                query = query.join(Context).filter(Context.owner_id == user_id)

            memory = query.first()
            if not memory:
                return None

            return {
                "id": memory.id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "metadata": memory.metadata,
                "created_at": (
                    memory.created_at.isoformat() if memory.created_at else None
                ),
                "context": memory.context.name if memory.context else None,
            }
        except Exception as e:
            raise e
        finally:
            session.close()
