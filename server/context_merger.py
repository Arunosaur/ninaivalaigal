"""
Context merger utility for handling duplicate contexts safely
"""
import logging
from typing import Any

from database import Context, DatabaseManager, Memory

logger = logging.getLogger(__name__)


class ContextMerger:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def merge_duplicate_contexts(
        self, context_name: str, user_id: int
    ) -> dict[str, Any]:
        """
        Merge duplicate contexts with same name/owner/scope, keeping the most recent one
        and transferring all memories to it.
        """
        session = self.db.get_session()
        try:
            # Find all contexts with same name and owner
            contexts = (
                session.query(Context)
                .filter_by(name=context_name, owner_id=user_id, scope="personal")
                .order_by(Context.created_at.asc())
                .all()
            )

            if len(contexts) <= 1:
                return {
                    "success": True,
                    "message": "No duplicates found",
                    "merged_count": 0,
                }

            # Keep the most recent context (last in chronological order)
            target_context = contexts[-1]
            contexts_to_merge = contexts[:-1]

            merged_memory_count = 0

            # Transfer memories from older contexts to the target context
            for old_context in contexts_to_merge:
                # Update memories to point to target context
                memories = (
                    session.query(Memory)
                    .filter_by(context=context_name, user_id=user_id)
                    .all()
                )

                for memory in memories:
                    # Ensure memory points to the correct context (by name, not ID)
                    # Memories use context name, not context_id in this system
                    merged_memory_count += 1

                # Delete the old context
                session.delete(old_context)
                logger.info(f"Merged context {old_context.id} into {target_context.id}")

            session.commit()

            return {
                "success": True,
                "message": f"Merged {len(contexts_to_merge)} duplicate contexts",
                "merged_count": len(contexts_to_merge),
                "memory_count": merged_memory_count,
                "target_context_id": target_context.id,
            }

        except Exception as e:
            session.rollback()
            logger.error(f"Error merging contexts: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def find_duplicate_contexts(self, user_id: int = None) -> list[dict[str, Any]]:
        """Find all duplicate contexts for a user or globally"""
        session = self.db.get_session()
        try:
            query = """
            SELECT name, owner_id, scope, COUNT(*) as duplicate_count
            FROM contexts
            WHERE owner_id IS NOT NULL
            """
            if user_id:
                query += f" AND owner_id = {user_id}"
            query += """
            GROUP BY name, owner_id, scope
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            """

            result = session.execute(query)
            duplicates = []

            for row in result:
                duplicates.append(
                    {
                        "name": row[0],
                        "owner_id": row[1],
                        "scope": row[2],
                        "duplicate_count": row[3],
                    }
                )

            return duplicates

        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
        finally:
            session.close()
