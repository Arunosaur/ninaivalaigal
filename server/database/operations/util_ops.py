"""
Database Utility Operations.

Shared helpers and common database utilities.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from sqlalchemy.orm import Session

from ..manager import DatabaseManager


class DatabaseUtilities(DatabaseManager):
    """Shared database utilities and helpers."""

    def get_db_instance(self) -> 'DatabaseUtilities':
        """Get database manager instance."""
        return self

    def validate_session(self, session: Optional[Session]) -> bool:
        """Validate database session."""
        if session is None:
            raise ValueError("Database session is required")
        return True

    def safe_commit(self, session: Session, operation_name: str = "database operation") -> bool:
        """Safely commit database transaction with error handling."""
        try:
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise Exception(f"Failed to commit {operation_name}: {str(e)}")

    def safe_rollback(self, session: Session) -> None:
        """Safely rollback database transaction."""
        try:
            session.rollback()
        except Exception:
            pass  # Rollback failures are typically not critical

    def close_session_safely(self, session: Session) -> None:
        """Safely close database session."""
        try:
            session.close()
        except Exception:
            pass  # Session close failures are typically not critical

    def execute_with_session(self, operation_func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute database operation with automatic session management."""
        session = self.get_session()
        try:
            result = operation_func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def batch_execute(
        self, operations: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]]
    ) -> List[Any]:
        """Execute multiple database operations in a single transaction."""
        session = self.get_session()
        results: List[Any] = []
        try:
            for operation_func, args, kwargs in operations:
                result = operation_func(session, *args, **kwargs)
                results.append(result)
            session.commit()
            return results
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_table_count(self, model_class: Type[Any]) -> int:
        """Get count of records in a table."""
        session = self.get_session()
        try:
            count: int = session.query(model_class).count()
            return count
        finally:
            session.close()

    def health_check(self) -> Dict[str, str]:
        """Perform database health check."""
        try:
            session = self.get_session()
            # Simple query to test connection
            session.execute("SELECT 1")
            session.close()
            return {"status": "healthy", "connection": "active"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database instance management
_db_instance = None


def get_db() -> Any:
    """Get database manager instance."""
    global _db_instance
    if _db_instance is None:
        # Import here to avoid circular imports
        from . import DatabaseOperations  # noqa: F401

        _db_instance = DatabaseOperations()
    return _db_instance


def reset_db_instance() -> None:
    """Reset database instance (for testing)."""
    global _db_instance
    _db_instance = None
