"""
Smoke tests for Redis connectivity and basic operations.
These tests ensure Redis is running and accessible.
"""

import os
import time

import pytest
import redis


class TestRedisSmoke:
    """Comprehensive Redis smoke tests."""

    # Redis connection parameters
    REDIS_CONFIG = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "password": os.getenv("REDIS_PASSWORD", "secure_nina_password"),
        "db": int(os.getenv("REDIS_DB", "0")),
        "decode_responses": True,
        "socket_timeout": 5,
        "socket_connect_timeout": 5,
    }

    def get_redis_client(self) -> redis.Redis:
        """Get Redis client with unified password authentication."""
        try:
            # Use unified password authentication (no username/ACL complexity)
            client = redis.Redis(
                host=self.REDIS_CONFIG["host"],
                port=self.REDIS_CONFIG["port"],
                password=self.REDIS_CONFIG["password"],
                db=self.REDIS_CONFIG["db"],
                decode_responses=self.REDIS_CONFIG["decode_responses"],
                socket_timeout=self.REDIS_CONFIG["socket_timeout"],
                socket_connect_timeout=self.REDIS_CONFIG["socket_connect_timeout"],
            )
            # Test connection
            client.ping()
            return client
        except Exception as e:
            pytest.fail(f"Failed to connect to Redis: {e}")

    def test_redis_connection(self):
        """Test basic Redis connection."""
        try:
            client = self.get_redis_client()
            response = client.ping()
            assert response is True
        except Exception as e:
            pytest.fail(f"Redis connection test failed: {e}")

    def test_redis_basic_operations(self):
        """Test basic Redis set/get operations."""
        try:
            client = self.get_redis_client()

            # Test string operations
            test_key = "smoke_test:basic"
            test_value = "test_value_123"

            # Set value
            result = client.set(test_key, test_value)
            assert result is True

            # Get value
            retrieved_value = client.get(test_key)
            assert retrieved_value == test_value

            # Clean up
            client.delete(test_key)

        except Exception as e:
            pytest.fail(f"Redis basic operations test failed: {e}")

    def test_redis_expiration(self):
        """Test Redis key expiration."""
        try:
            client = self.get_redis_client()

            test_key = "smoke_test:expiration"
            test_value = "expires_soon"

            # Set with expiration
            client.setex(test_key, 2, test_value)  # 2 seconds

            # Verify it exists
            assert client.get(test_key) == test_value

            # Check TTL
            ttl = client.ttl(test_key)
            assert 0 < ttl <= 2

            # Wait for expiration
            time.sleep(3)

            # Verify it's gone
            assert client.get(test_key) is None

        except Exception as e:
            pytest.fail(f"Redis expiration test failed: {e}")

    def test_redis_hash_operations(self):
        """Test Redis hash operations."""
        try:
            client = self.get_redis_client()

            hash_key = "smoke_test:hash"
            hash_data = {"field1": "value1", "field2": "value2", "field3": "value3"}

            # Set hash fields
            client.hset(hash_key, mapping=hash_data)

            # Get all hash fields
            retrieved_data = client.hgetall(hash_key)
            assert retrieved_data == hash_data

            # Get specific field
            field_value = client.hget(hash_key, "field1")
            assert field_value == "value1"

            # Clean up
            client.delete(hash_key)

        except Exception as e:
            pytest.fail(f"Redis hash operations test failed: {e}")

    def test_redis_list_operations(self):
        """Test Redis list operations."""
        try:
            client = self.get_redis_client()

            list_key = "smoke_test:list"
            test_items = ["item1", "item2", "item3"]

            # Push items to list
            for item in test_items:
                client.lpush(list_key, item)

            # Get list length
            list_length = client.llen(list_key)
            assert list_length == len(test_items)

            # Get all items
            retrieved_items = client.lrange(list_key, 0, -1)
            # Items are in reverse order due to lpush
            assert retrieved_items == list(reversed(test_items))

            # Clean up
            client.delete(list_key)

        except Exception as e:
            pytest.fail(f"Redis list operations test failed: {e}")

    def test_redis_set_operations(self):
        """Test Redis set operations."""
        try:
            client = self.get_redis_client()

            set_key = "smoke_test:set"
            test_members = {"member1", "member2", "member3"}

            # Add members to set
            for member in test_members:
                client.sadd(set_key, member)

            # Get set size
            set_size = client.scard(set_key)
            assert set_size == len(test_members)

            # Get all members
            retrieved_members = client.smembers(set_key)
            assert retrieved_members == test_members

            # Test membership (Redis returns 1/0, not True/False)
            assert client.sismember(set_key, "member1") == 1
            assert client.sismember(set_key, "nonexistent") == 0

            # Clean up
            client.delete(set_key)

        except Exception as e:
            pytest.fail(f"Redis set operations test failed: {e}")

    def test_redis_sorted_set_operations(self):
        """Test Redis sorted set operations."""
        try:
            client = self.get_redis_client()

            zset_key = "smoke_test:zset"
            test_data = {"member1": 1.0, "member2": 2.0, "member3": 3.0}

            # Add members with scores
            for member, score in test_data.items():
                client.zadd(zset_key, {member: score})

            # Get sorted set size
            zset_size = client.zcard(zset_key)
            assert zset_size == len(test_data)

            # Get members by score range
            members_by_score = client.zrangebyscore(zset_key, 1.0, 3.0)
            assert len(members_by_score) == 3

            # Get member score
            score = client.zscore(zset_key, "member2")
            assert score == 2.0

            # Clean up
            client.delete(zset_key)

        except Exception as e:
            pytest.fail(f"Redis sorted set operations test failed: {e}")

    def test_redis_info(self):
        """Test Redis server info."""
        try:
            client = self.get_redis_client()

            info = client.info()
            assert isinstance(info, dict)
            assert "redis_version" in info
            assert "used_memory" in info
            assert "connected_clients" in info

            # Check Redis version (expecting 7.x)
            redis_version = info["redis_version"]
            assert redis_version.startswith("7."), f"Expected Redis 7.x, got {redis_version}"

        except Exception as e:
            pytest.fail(f"Redis info test failed: {e}")

    def test_redis_pipeline(self):
        """Test Redis pipeline operations."""
        try:
            client = self.get_redis_client()

            # Create pipeline
            pipe = client.pipeline()

            # Queue multiple operations
            test_keys = ["pipe_test:1", "pipe_test:2", "pipe_test:3"]
            for i, key in enumerate(test_keys):
                pipe.set(key, f"value_{i}")

            # Execute pipeline
            results = pipe.execute()
            assert len(results) == len(test_keys)
            assert all(result is True for result in results)

            # Verify values were set
            for i, key in enumerate(test_keys):
                value = client.get(key)
                assert value == f"value_{i}"

            # Clean up
            client.delete(*test_keys)

        except Exception as e:
            pytest.fail(f"Redis pipeline test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
