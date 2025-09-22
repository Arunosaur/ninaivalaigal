"""
Context Operations
Database operations for context management
"""

from ..manager import DatabaseManager
from ..models import Context


class ContextOperations(DatabaseManager):
    """Context-related database operations"""

    def set_active_context(
        self, context_name: str, user_id: int = None, scope: str = None
    ):
        """Set a context as active"""
        session = self.get_session()
        try:
            context = self.resolve_context(context_name, user_id, scope, session)

            if context:
                context.is_active = True
            else:
                # Create new personal context if not found
                context = Context(
                    name=context_name,
                    is_active=True,
                    owner_id=user_id,
                    scope="personal",
                )
                session.add(context)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def create_context(
        self,
        name: str,
        description: str = None,
        user_id: int = None,
        scope: str = "personal",
        is_active: bool = False,
    ):
        """Create a new context"""
        session = self.get_session()
        try:
            # Check if context already exists for this user/scope
            existing = (
                session.query(Context)
                .filter(
                    Context.name == name,
                    Context.owner_id == user_id,
                    Context.scope == scope,
                )
                .first()
            )

            if existing:
                raise ValueError(f"Context '{name}' already exists for this user/scope")

            context = Context(
                name=name,
                description=description,
                owner_id=user_id,
                scope=scope,
                is_active=is_active,
            )

            session.add(context)
            session.commit()
            return context
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_context(self, context_name: str, user_id: int):
        """Delete a recording context - requires user authentication"""
        if user_id is None:
            raise ValueError("User authentication required for delete operations")

        session = self.get_session()
        try:
            context = (
                session.query(Context)
                .filter(Context.name == context_name, Context.owner_id == user_id)
                .first()
            )

            if not context:
                raise ValueError(
                    f"Context '{context_name}' not found or not owned by user"
                )

            session.delete(context)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def clear_active_context(self, user_id: int = None):
        """Clear active context status"""
        session = self.get_session()
        try:
            if user_id:
                contexts = session.query(Context).filter(Context.owner_id == user_id)
            else:
                contexts = session.query(Context)

            contexts.update({"is_active": False})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_active_context(self, user_id: int = None):
        """Get the currently active context"""
        session = self.get_session()
        try:
            if user_id:
                context = (
                    session.query(Context)
                    .filter(Context.owner_id == user_id, Context.is_active == True)
                    .first()
                )
            else:
                context = (
                    session.query(Context).filter(Context.is_active == True).first()
                )

            return context
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_all_contexts(self, user_id: int = None):
        """Get all contexts accessible to a user"""
        session = self.get_session()
        try:
            if user_id:
                # Get contexts owned by user or shared with user
                owned_contexts = session.query(Context).filter(
                    Context.owner_id == user_id
                )

                # TODO: Add shared contexts logic when permissions are implemented
                contexts = owned_contexts.all()
            else:
                contexts = session.query(Context).all()

            return [
                {
                    "id": ctx.id,
                    "name": ctx.name,
                    "description": ctx.description,
                    "scope": ctx.scope,
                    "is_active": ctx.is_active,
                    "created_at": (
                        ctx.created_at.isoformat() if ctx.created_at else None
                    ),
                    "owner_id": ctx.owner_id,
                }
                for ctx in contexts
            ]
        except Exception as e:
            raise e
        finally:
            session.close()

    def resolve_context(
        self, context_name: str, user_id: int = None, scope: str = None, session=None
    ):
        """Resolve context based on name, user access, and scope priority"""
        should_close_session = session is None
        if session is None:
            session = self.get_session()

        try:
            # Priority order: user-specific -> team -> organization -> global
            query = session.query(Context).filter(Context.name == context_name)

            if user_id:
                # First try personal context
                personal_context = query.filter(
                    Context.owner_id == user_id, Context.scope == "personal"
                ).first()
                if personal_context:
                    return personal_context

                # Then try team contexts (if user is member)
                # TODO: Implement team context resolution

                # Then try organization contexts (if user is member)
                # TODO: Implement organization context resolution

            # Finally try global contexts
            global_context = query.filter(Context.scope == "global").first()
            if global_context:
                return global_context

            return None
        except Exception as e:
            raise e
        finally:
            if should_close_session:
                session.close()

    def get_contexts(self, user_id: int = None):
        """Get contexts accessible to user"""
        session = self.get_session()
        try:
            if user_id:
                contexts = (
                    session.query(Context).filter(Context.owner_id == user_id).all()
                )
            else:
                contexts = session.query(Context).all()

            return [ctx.name for ctx in contexts]
        except Exception as e:
            raise e
        finally:
            session.close()

    def start_context(self, context_name: str):
        """Start recording context - MCP compatibility"""
        # For MCP compatibility - could store active context state
        pass

    def stop_context(self, context_name: str = None):
        """Stop recording context - either specific context or all active contexts"""
        session = self.get_session()
        try:
            if context_name:
                # Stop specific context
                context = (
                    session.query(Context).filter(Context.name == context_name).first()
                )
                if context:
                    context.is_active = False
            else:
                # Stop all active contexts
                session.query(Context).filter(Context.is_active == True).update(
                    {"is_active": False}
                )

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def stop_specific_context(self, context_name: str):
        """Stop specific context by name"""
        return self.stop_context(context_name)
