"""
SPEC-011: Memory Lifecycle Management - Garbage Collection Service

This module provides automated memory lifecycle management including:
- TTL expiration
- Archival of inactive memories
- Purging of old archived memories
- Lifecycle notifications
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import asyncpg

logger = logging.getLogger(__name__)


class LifecycleEventType(Enum):
    CREATED = "created"
    ACCESSED = "accessed"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    RESTORED = "restored"
    DELETED = "deleted"


class LifecycleStatus(Enum):
    ACTIVE = "active"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class LifecyclePolicy:
    id: str
    scope: str
    user_id: str | None
    team_id: str | None
    org_id: str | None
    policy_type: str
    policy_config: dict
    enabled: bool


@dataclass
class MemoryLifecycleStats:
    total_memories: int
    active_memories: int
    expired_memories: int
    archived_memories: int
    deleted_memories: int
    avg_access_count: float
    oldest_memory_age_days: int
    most_recent_access_days: int


class MemoryGarbageCollector:
    """
    Background service for memory lifecycle management
    """

    def __init__(self, database_url: str, dry_run: bool = False):
        self.database_url = database_url
        self.dry_run = dry_run
        self.pool: asyncpg.Pool | None = None

    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url, min_size=1, max_size=5, command_timeout=60
        )
        logger.info("Memory GC service initialized")

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Memory GC service closed")

    async def run_lifecycle_cycle(self) -> dict[str, int]:
        """
        Run a complete lifecycle management cycle
        Returns statistics about actions taken
        """
        stats = {
            "expired_count": 0,
            "archived_count": 0,
            "purged_count": 0,
            "notifications_sent": 0,
        }

        try:
            # Step 1: Mark expired memories
            stats["expired_count"] = await self.mark_expired_memories()

            # Step 2: Archive inactive memories
            stats["archived_count"] = await self.archive_inactive_memories()

            # Step 3: Purge old archived memories (if enabled)
            stats["purged_count"] = await self.purge_old_archived_memories()

            # Step 4: Send notifications for expiring memories
            stats["notifications_sent"] = await self.send_expiration_notifications()

            logger.info(f"Lifecycle cycle completed: {stats}")

        except Exception as e:
            logger.error(f"Error during lifecycle cycle: {e}")
            raise

        return stats

    async def mark_expired_memories(self) -> int:
        """Mark memories that have passed their TTL as expired"""
        if self.dry_run:
            # Count what would be expired
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                SELECT COUNT(*) FROM memories
                WHERE expires_at IS NOT NULL
                  AND expires_at <= now()
                  AND lifecycle_status = 'active'
            """
                )
                logger.info(f"[DRY RUN] Would expire {count} memories")
                return count

        async with self.pool.acquire() as conn:
            expired_count = await conn.fetchval("SELECT mark_expired_memories()")
            logger.info(f"Marked {expired_count} memories as expired")
            return expired_count

    async def archive_inactive_memories(self) -> int:
        """Archive memories that haven't been accessed recently"""
        archived_count = 0

        # Get archival policies for each scope
        policies = await self.get_archival_policies()

        for policy in policies:
            days_threshold = policy.policy_config.get("days_inactive", 90)

            if self.dry_run:
                async with self.pool.acquire() as conn:
                    count = await conn.fetchval(
                        """
                        SELECT COUNT(*) FROM memories
                        WHERE last_accessed_at < (now() - INTERVAL '1 day' * $1)
                          AND lifecycle_status = 'active'
                          AND expires_at IS NULL
                          AND ($2::text IS NULL OR scope = $2)
                          AND ($3::integer IS NULL OR user_id = $3)
                          AND ($4::integer IS NULL OR team_id = $4)
                          AND ($5::integer IS NULL OR org_id = $5)
                    """,
                        days_threshold,
                        policy.scope,
                        policy.user_id,
                        policy.team_id,
                        policy.org_id,
                    )
                    logger.info(
                        f"[DRY RUN] Would archive {count} memories for policy {policy.id}"
                    )
                    archived_count += count
            else:
                async with self.pool.acquire() as conn:
                    count = await conn.fetchval(
                        "SELECT archive_old_memories($1)", days_threshold
                    )
                    archived_count += count

        if not self.dry_run:
            logger.info(f"Archived {archived_count} inactive memories")

        return archived_count

    async def purge_old_archived_memories(self, max_archive_days: int = 365) -> int:
        """Permanently delete archived memories older than threshold"""
        if self.dry_run:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM memories
                    WHERE lifecycle_status = 'archived'
                      AND archived_at < (now() - INTERVAL '1 day' * $1)
                """,
                    max_archive_days,
                )
                logger.info(f"[DRY RUN] Would purge {count} old archived memories")
                return count

        async with self.pool.acquire() as conn:
            # First, log the deletion events
            await conn.execute(
                """
                INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
                SELECT id, 'deleted', 'system',
                       jsonb_build_object('deleted_at', now(), 'reason', 'archive_purge', 'archive_age_days', $1)
                FROM memories
                WHERE lifecycle_status = 'archived'
                  AND archived_at < (now() - INTERVAL '1 day' * $1)
            """,
                max_archive_days,
            )

            # Then delete the memories
            purged_count = await conn.fetchval(
                """
                DELETE FROM memories
                WHERE lifecycle_status = 'archived'
                  AND archived_at < (now() - INTERVAL '1 day' * $1)
                RETURNING COUNT(*)
            """,
                max_archive_days,
            )

            logger.info(f"Purged {purged_count} old archived memories")
            return purged_count or 0

    async def send_expiration_notifications(self) -> int:
        """Send notifications for memories expiring soon"""
        # Find memories expiring in the next 7 days
        async with self.pool.acquire() as conn:
            expiring_memories = await conn.fetch(
                """
                SELECT id, scope, user_id, team_id, org_id, data, expires_at
                FROM memories
                WHERE expires_at BETWEEN now() AND (now() + INTERVAL '7 days')
                  AND lifecycle_status = 'active'
                  AND NOT EXISTS (
                      SELECT 1 FROM memory_lifecycle_events
                      WHERE memory_id = memories.id
                        AND event_type = 'expiring_notification'
                        AND created_at > (now() - INTERVAL '7 days')
                  )
            """
            )

        notifications_sent = 0

        for memory in expiring_memories:
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would notify about expiring memory {memory['id']}"
                )
                notifications_sent += 1
            else:
                # In a real implementation, this would send email/push notifications
                # For now, we'll just log the event
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO memory_lifecycle_events (memory_id, event_type, triggered_by, event_data)
                        VALUES ($1, 'expiring_notification', 'system', $2)
                    """,
                        memory["id"],
                        json.dumps(
                            {
                                "expires_at": memory["expires_at"].isoformat(),
                                "days_until_expiry": (
                                    memory["expires_at"] - datetime.now()
                                ).days,
                                "notification_sent_at": datetime.now().isoformat(),
                            }
                        ),
                    )

                logger.info(f"Sent expiration notification for memory {memory['id']}")
                notifications_sent += 1

        return notifications_sent

    async def get_archival_policies(self) -> list[LifecyclePolicy]:
        """Get all active archival policies"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, scope, user_id, team_id, org_id, policy_type, policy_config, enabled
                FROM memory_lifecycle_policies
                WHERE policy_type = 'archival' AND enabled = true
            """
            )

            return [
                LifecyclePolicy(
                    id=str(row["id"]),
                    scope=row["scope"],
                    user_id=row["user_id"],
                    team_id=row["team_id"],
                    org_id=row["org_id"],
                    policy_type=row["policy_type"],
                    policy_config=row["policy_config"]
                    if isinstance(row["policy_config"], dict)
                    else {},
                    enabled=row["enabled"],
                )
                for row in rows
            ]

    async def get_lifecycle_stats(
        self,
        scope: str | None = None,
        user_id: str | None = None,
        team_id: str | None = None,
        org_id: str | None = None,
    ) -> MemoryLifecycleStats:
        """Get lifecycle statistics for a given scope"""
        async with self.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) as total_memories,
                    COUNT(*) FILTER (WHERE lifecycle_status = 'active') as active_memories,
                    COUNT(*) FILTER (WHERE lifecycle_status = 'expired') as expired_memories,
                    COUNT(*) FILTER (WHERE lifecycle_status = 'archived') as archived_memories,
                    COUNT(*) FILTER (WHERE lifecycle_status = 'deleted') as deleted_memories,
                    COALESCE(AVG(access_count), 0) as avg_access_count,
                    COALESCE(EXTRACT(days FROM (now() - MIN(created_at))), 0) as oldest_memory_age_days,
                    COALESCE(EXTRACT(days FROM (now() - MAX(last_accessed_at))), 0) as most_recent_access_days
                FROM memories
                WHERE ($1::text IS NULL OR scope = $1)
                  AND ($2::integer IS NULL OR user_id = $2)
                  AND ($3::integer IS NULL OR team_id = $3)
                  AND ($4::integer IS NULL OR org_id = $4)
            """,
                scope,
                user_id,
                team_id,
                org_id,
            )

            return MemoryLifecycleStats(
                total_memories=stats["total_memories"],
                active_memories=stats["active_memories"],
                expired_memories=stats["expired_memories"],
                archived_memories=stats["archived_memories"],
                deleted_memories=stats["deleted_memories"],
                avg_access_count=float(stats["avg_access_count"]),
                oldest_memory_age_days=int(stats["oldest_memory_age_days"]),
                most_recent_access_days=int(stats["most_recent_access_days"]),
            )


async def main():
    """Main entry point for running memory GC as a standalone service"""
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

    from auth import load_config

    database_url = load_config()  # Use existing config system
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    interval_minutes = int(os.getenv("GC_INTERVAL_MINUTES", "60"))

    gc = MemoryGarbageCollector(database_url, dry_run=dry_run)

    try:
        await gc.initialize()

        logger.info(
            f"Starting memory GC service (dry_run={dry_run}, interval={interval_minutes}min)"
        )

        while True:
            try:
                stats = await gc.run_lifecycle_cycle()
                logger.info(f"GC cycle completed: {stats}")

                # Wait for next cycle
                await asyncio.sleep(interval_minutes * 60)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in GC cycle: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)

    finally:
        await gc.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main())
