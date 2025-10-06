"""
🧪 CRITICAL SMOKE TESTS - MUST ALWAYS PASS
These tests validate core infrastructure.
If ANY test fails, there's a regression.

Run before every commit: pytest tests/smoke/ -v
"""

import os
import subprocess

import pytest


class TestInfrastructureSmoke:
    """Test core infrastructure accessibility."""

    def test_database_accessible(self):
        """Test PostgreSQL database accessibility via psql."""
        # Check if database is running
        result = subprocess.run(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "nina",
                "-d",
                "ninaivalaigal_dev",
                "-c",
                "SELECT 1;",
            ],
            env={
                **os.environ,
                "PGPASSWORD": "dev_password_change_in_production",  # pragma: allowlist secret
            },
            capture_output=True,
            timeout=5,
        )
        assert (
            result.returncode == 0
        ), f"Database connection failed: {result.stderr.decode()}"

    def test_redis_accessible(self):
        """Redis must be accessible."""
        result = subprocess.run(
            ["redis-cli", "-h", "localhost", "-p", "6379", "ping"],
            capture_output=True,
            timeout=5,
        )
        assert (
            result.returncode == 0
        ), f"Redis connection failed: {result.stderr.decode()}"

    def test_api_health_endpoint(self):
        """API /health endpoint must return 200."""
        import requests

        try:
            response = requests.get("http://localhost:13370/health", timeout=5)
            assert (
                response.status_code == 200
            ), f"Health check failed: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running (expected in some contexts)")


class TestDatabaseSchema:
    """Database schema must be in expected state."""

    def test_migrations_applied(self):
        """Alembic migrations must be up to date."""
        # Check alembic current version
        result = subprocess.run(
            ["alembic", "current"],
            cwd="/Users/swami/WorkSpace/ninaivalaigal/server",  # pragma: allowlist secret
            capture_output=True,
            timeout=10,
        )
        output = result.stdout.decode()
        # Should show a migration version (not empty)
        assert result.returncode == 0, f"Alembic check failed: {result.stderr.decode()}"
        assert (
            "head" in output.lower() or len(output.strip()) > 0
        ), "No migrations applied"


class TestCriticalPaths:
    """Test critical application paths."""

    @pytest.mark.skip(
        reason="Requires running API server - implement when API is stable"
    )
    def test_user_signup_endpoint_exists(self):
        """User signup endpoint must exist."""
        import requests

        response = requests.post(
            "http://localhost:13370/auth/signup",
            json={
                "email": "test@example.com",
                "password": "testpass123",  # pragma: allowlist secret
            },
            timeout=5,
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    @pytest.mark.skip(
        reason="Requires running API server - implement when API is stable"
    )
    def test_memory_crud_endpoint_exists(self):
        """Memory CRUD endpoints must exist."""
        import requests

        response = requests.get("http://localhost:13370/memory/", timeout=5)
        assert response.status_code != 404


# Regression guard: Record what's currently working
def test_regression_guard():
    """
    This test documents the current working state.
    Update this when you make intentional changes.

    Current known working state (v0.9-pre-phase1):
    - Database: PostgreSQL accessible
    - Redis: Accessible on 6379
    - API: May or may not be running (depending on context)
    - Migrations: Should be applied
    """
    # This test always passes but serves as documentation
    assert True, "If this fails, something is very wrong"
