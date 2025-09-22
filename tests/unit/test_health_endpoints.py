"""Unit tests for server modules."""
import pytest


class TestServerModules:
    """Test server module imports and basic functionality."""

    def test_database_import(self):
        """Test that we can import database module."""
        from server import database

        assert hasattr(database, "get_db")
        # Test that Base is defined
        assert hasattr(database, "Base")

    def test_auth_import(self):
        """Test that we can import auth module."""
        from server import auth

        # Test that key functions exist
        assert hasattr(auth, "create_access_token") or hasattr(
            auth, "authenticate_user"
        )

    def test_memory_api_import(self):
        """Test that we can import memory API."""
        from server import memory_api

        # Should have some API functions
        assert hasattr(memory_api, "router") or callable(
            getattr(memory_api, "create_memory", None)
        )

    def test_rbac_middleware_import(self):
        """Test that we can import RBAC middleware."""
        from server import rbac_middleware

        # Should have middleware class or function
        assert hasattr(rbac_middleware, "RBACMiddleware") or hasattr(
            rbac_middleware, "rbac_middleware"
        )

    def test_redis_client_import(self):
        """Test that we can import Redis client."""
        from server import redis_client

        # Should have Redis client functionality
        assert hasattr(redis_client, "get_redis_client") or hasattr(
            redis_client, "RedisClient"
        )

    def test_relevance_engine_import(self):
        """Test that we can import relevance engine."""
        from server import relevance_engine

        # Should have relevance engine class
        assert hasattr(relevance_engine, "RelevanceEngine") or hasattr(
            relevance_engine, "calculate_relevance"
        )

    def test_memory_providers_import(self):
        """Test that we can import memory providers."""
        from server.memory.providers import postgres

        assert hasattr(postgres, "PostgresMemoryProvider")

    def test_observability_import(self):
        """Test that we can import observability modules."""
        from server.observability import health

        # Should have health check functionality
        assert hasattr(health, "health_check") or hasattr(health, "get_health_status")
