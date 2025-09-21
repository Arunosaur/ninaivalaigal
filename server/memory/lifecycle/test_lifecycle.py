"""
SPEC-011: Memory Lifecycle Management Tests

Test suite for memory lifecycle functionality including:
- TTL expiration
- Archival policies
- Garbage collection
- API endpoints
"""

import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import asyncpg
import pytest

from .api import lifecycle_router
from .memory_gc import MemoryGarbageCollector


class TestMemoryGarbageCollector:
    """Test the memory garbage collector"""

    @pytest.fixture
    async def gc(self):
        """Create a test garbage collector instance"""
        database_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://nina:change_me_securely@127.0.0.1:5433/nina_test",
        )
        gc = MemoryGarbageCollector(database_url, dry_run=True)
        await gc.initialize()
        yield gc
        await gc.close()

    @pytest.fixture
    async def setup_test_data(self, gc):
        """Set up test data in the database"""
        async with gc.pool.acquire() as conn:
            # Clear existing test data
            await conn.execute("DELETE FROM memory_lifecycle_events")
            await conn.execute("DELETE FROM memory_records")

            # Insert test memories
            test_memories = [
                # Active memory
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "scope": "personal",
                    "user_id": "user1",
                    "kind": "note",
                    "text": "Active memory",
                    "lifecycle_status": "active",
                    "created_at": datetime.now() - timedelta(days=1),
                    "last_accessed_at": datetime.now() - timedelta(hours=1),
                },
                # Expired memory (TTL passed)
                {
                    "id": "22222222-2222-2222-2222-222222222222",
                    "scope": "personal",
                    "user_id": "user1",
                    "kind": "note",
                    "text": "Expired memory",
                    "lifecycle_status": "active",
                    "expires_at": datetime.now() - timedelta(hours=1),
                    "created_at": datetime.now() - timedelta(days=2),
                    "last_accessed_at": datetime.now() - timedelta(days=1),
                },
                # Old inactive memory (should be archived)
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "scope": "personal",
                    "user_id": "user1",
                    "kind": "note",
                    "text": "Old inactive memory",
                    "lifecycle_status": "active",
                    "created_at": datetime.now() - timedelta(days=100),
                    "last_accessed_at": datetime.now() - timedelta(days=95),
                },
                # Already archived memory
                {
                    "id": "44444444-4444-4444-4444-444444444444",
                    "scope": "personal",
                    "user_id": "user1",
                    "kind": "note",
                    "text": "Archived memory",
                    "lifecycle_status": "archived",
                    "archived_at": datetime.now() - timedelta(days=400),
                    "created_at": datetime.now() - timedelta(days=500),
                    "last_accessed_at": datetime.now() - timedelta(days=450),
                },
            ]

            for memory in test_memories:
                await conn.execute(
                    """
                    INSERT INTO memory_records
                    (id, scope, user_id, team_id, org_id, kind, text, metadata, embedding,
                     lifecycle_status, expires_at, archived_at, created_at, last_accessed_at, access_count)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                    memory["id"],
                    memory["scope"],
                    memory["user_id"],
                    memory.get("team_id"),
                    memory.get("org_id"),
                    memory["kind"],
                    memory["text"],
                    {},
                    None,
                    memory["lifecycle_status"],
                    memory.get("expires_at"),
                    memory.get("archived_at"),
                    memory["created_at"],
                    memory["last_accessed_at"],
                    1,
                )

    @pytest.mark.asyncio
    async def test_mark_expired_memories(self, gc, setup_test_data):
        """Test marking expired memories"""
        # Run in dry-run mode to count what would be expired
        expired_count = await gc.mark_expired_memories()

        # Should find 1 expired memory
        assert expired_count == 1

    @pytest.mark.asyncio
    async def test_archive_inactive_memories(self, gc, setup_test_data):
        """Test archiving inactive memories"""
        # Run archival
        archived_count = await gc.archive_inactive_memories()

        # Should archive the old inactive memory
        assert archived_count >= 1

    @pytest.mark.asyncio
    async def test_purge_old_archived_memories(self, gc, setup_test_data):
        """Test purging old archived memories"""
        # Run purge with 365 day threshold
        purged_count = await gc.purge_old_archived_memories(365)

        # Should purge the old archived memory
        assert purged_count >= 1

    @pytest.mark.asyncio
    async def test_run_lifecycle_cycle(self, gc, setup_test_data):
        """Test running a complete lifecycle cycle"""
        stats = await gc.run_lifecycle_cycle()

        # Should have stats for all operations
        assert "expired_count" in stats
        assert "archived_count" in stats
        assert "purged_count" in stats
        assert "notifications_sent" in stats

        # Should have found some work to do
        total_actions = sum(stats.values())
        assert total_actions > 0

    @pytest.mark.asyncio
    async def test_get_lifecycle_stats(self, gc, setup_test_data):
        """Test getting lifecycle statistics"""
        stats = await gc.get_lifecycle_stats(scope="personal", user_id="user1")

        assert stats.total_memories >= 4  # We inserted 4 test memories
        assert stats.active_memories >= 2
        assert stats.avg_access_count >= 1.0
        assert stats.oldest_memory_age_days >= 0


class TestLifecycleAPI:
    """Test the lifecycle API endpoints"""

    @pytest.fixture
    def mock_gc(self):
        """Mock garbage collector for API tests"""
        gc = AsyncMock(spec=MemoryGarbageCollector)
        gc.pool = AsyncMock()
        return gc

    @pytest.mark.asyncio
    async def test_set_memory_ttl_endpoint(self, mock_gc):
        """Test setting TTL via API"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(lifecycle_router)

        # Mock the dependency
        app.dependency_overrides[get_memory_gc] = lambda: mock_gc

        client = TestClient(app)

        # Mock database operations
        mock_gc.pool.acquire.return_value.__aenter__.return_value.fetchval.return_value = True
        mock_gc.pool.acquire.return_value.__aenter__.return_value.execute.return_value = None

        response = client.post(
            "/memory/lifecycle/memories/test-id/ttl",
            json={"memory_id": "test-id", "ttl_hours": 24},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["memory_id"] == "test-id"
        assert data["ttl_hours"] == 24
        assert "expires_at" in data

    @pytest.mark.asyncio
    async def test_get_lifecycle_stats_endpoint(self, mock_gc):
        """Test getting stats via API"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from .memory_gc import MemoryLifecycleStats

        app = FastAPI()
        app.include_router(lifecycle_router)

        # Mock the dependency
        app.dependency_overrides[get_memory_gc] = lambda: mock_gc

        # Mock stats response
        mock_stats = MemoryLifecycleStats(
            total_memories=100,
            active_memories=80,
            expired_memories=10,
            archived_memories=8,
            deleted_memories=2,
            avg_access_count=5.5,
            oldest_memory_age_days=365,
            most_recent_access_days=1,
        )
        mock_gc.get_lifecycle_stats.return_value = mock_stats

        client = TestClient(app)

        response = client.get("/memory/lifecycle/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total_memories"] == 100
        assert data["active_memories"] == 80
        assert data["avg_access_count"] == 5.5


class TestLifecyclePolicies:
    """Test lifecycle policy management"""

    @pytest.mark.asyncio
    async def test_default_policies_created(self):
        """Test that default policies are created during migration"""
        database_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://nina:change_me_securely@127.0.0.1:5433/nina_test",
        )

        try:
            pool = await asyncpg.create_pool(database_url)

            async with pool.acquire() as conn:
                policies = await conn.fetch(
                    """
                    SELECT scope, policy_type, policy_config
                    FROM memory_lifecycle_policies
                    WHERE policy_type = 'archival'
                """
                )

                # Should have policies for all scopes
                scopes = {policy["scope"] for policy in policies}
                assert "personal" in scopes
                assert "team" in scopes
                assert "organization" in scopes

                # Check policy configurations
                for policy in policies:
                    config = policy["policy_config"]
                    assert "days_inactive" in config
                    assert config["days_inactive"] > 0

        finally:
            if "pool" in locals():
                await pool.close()


# Integration test
@pytest.mark.integration
class TestLifecycleIntegration:
    """Integration tests requiring a real database"""

    @pytest.mark.asyncio
    async def test_full_lifecycle_workflow(self):
        """Test the complete lifecycle workflow"""
        database_url = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://nina:change_me_securely@127.0.0.1:5433/nina_test",
        )

        gc = MemoryGarbageCollector(database_url, dry_run=False)

        try:
            await gc.initialize()

            # Insert a test memory with TTL
            memory_id = "99999999-9999-9999-9999-999999999999"
            expires_at = datetime.now() + timedelta(seconds=1)  # Expires in 1 second

            async with gc.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO memory_records
                    (id, scope, user_id, kind, text, metadata, lifecycle_status, expires_at, created_at, last_accessed_at, access_count)
                    VALUES ($1, 'personal', 'test_user', 'note', 'Test memory', '{}', 'active', $2, now(), now(), 1)
                """,
                    memory_id,
                    expires_at,
                )

            # Wait for expiration
            await asyncio.sleep(2)

            # Run garbage collection
            stats = await gc.run_lifecycle_cycle()

            # Should have expired the memory
            assert stats["expired_count"] >= 1

            # Verify the memory is marked as expired
            async with gc.pool.acquire() as conn:
                status = await conn.fetchval(
                    "SELECT lifecycle_status FROM memory_records WHERE id = $1",
                    memory_id,
                )
                assert status == "expired"

                # Check that an event was logged
                event_count = await conn.fetchval(
                    """
                    SELECT COUNT(*) FROM memory_lifecycle_events
                    WHERE memory_id = $1 AND event_type = 'expired'
                """,
                    memory_id,
                )
                assert event_count >= 1

        finally:
            await gc.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
