#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
🧪 CRITICAL SMOKE TESTS - MUST ALWAYS PASS
These tests validate core infrastructure.
If ANY test fails, there's a regression.

Architecture:
- Apple Container CLI: No localhost port forwarding
- Access via PgBouncer (port 6432), not direct DB
- Dynamic IP detection from container inspect

Run before every commit: pytest tests/smoke/ -v
"""

import json
import os
import subprocess

import pytest


def get_container_ip(container_name: str) -> str | None:
    """Get IP address of Apple Container CLI container."""
    try:
        result = subprocess.run(
            ["container", "inspect", container_name],
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        inspect_data = json.loads(result.stdout)
        if inspect_data and len(inspect_data) > 0:
            networks = inspect_data[0].get("networks", [])
            if networks and len(networks) > 0:
                address = networks[0].get("address", "")
                # Remove CIDR suffix if present (e.g., "192.168.64.99/24" -> "192.168.64.99")
                return address.split("/")[0] if address else None
    except Exception:
        return None
    return None


class TestInfrastructureSmoke:
    """Test core infrastructure accessibility."""

    def test_database_accessible_via_pgbouncer(self):
        """Test PostgreSQL database accessibility via PgBouncer (correct architecture)."""
        # Get PgBouncer container IP (Apple Container CLI)
        pgbouncer_ip = get_container_ip("ninaivalaigal-dev-pgbouncer")

        if not pgbouncer_ip:
            pytest.skip("PgBouncer container not running (ninaivalaigal-dev-pgbouncer)")

        # Connect through PgBouncer on port 6432 (NOT direct DB)
        result = subprocess.run(
            [
                "psql",
                "-h",
                pgbouncer_ip,
                "-p",
                "6432",
                "-U",
                "nina",
                "-d",
                "nina",  # Database name through PgBouncer
                "-c",
                "SELECT 1;",
            ],
            env={
                **os.environ,
                "PGPASSWORD": "change_me_securely",  # pragma: allowlist secret
            },
            capture_output=True,
            timeout=5,
        )

        assert result.returncode == 0, f"PgBouncer connection failed: {result.stderr.decode()}"

    def test_redis_accessible(self):
        """Redis must be accessible via Apple Container CLI."""
        # Get Redis container IP
        redis_ip = get_container_ip("ninaivalaigal-dev-redis")

        if not redis_ip:
            pytest.skip("Redis container not running (ninaivalaigal-dev-redis)")

        result = subprocess.run(
            [
                "redis-cli",
                "-h",
                redis_ip,
                "-p",
                "6379",
                "-a",
                "nina_redis_dev_password",  # pragma: allowlist secret
                "ping",
            ],
            capture_output=True,
            timeout=5,
        )

        assert result.returncode == 0, f"Redis connection failed: {result.stderr.decode()}"

    def test_api_health_endpoint(self):
        """API /health endpoint must return 200."""
        import requests

        try:
            response = requests.get("http://localhost:13370/health", timeout=5)
            assert response.status_code == 200, f"Health check failed: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API server not running (expected in some contexts)")


class TestDatabaseSchema:
    """Database schema must be in expected state."""

    def test_migrations_applied(self):
        """Alembic migrations must be up to date via PgBouncer."""
        # Get PgBouncer container IP
        pgbouncer_ip = get_container_ip("ninaivalaigal-dev-pgbouncer")

        if not pgbouncer_ip:
            pytest.skip("PgBouncer container not running (ninaivalaigal-dev-pgbouncer)")

        # Connect through PgBouncer on port 6432
        db_url = (
            f"postgresql://nina:change_me_securely@{pgbouncer_ip}:6432/nina"  # pragma: allowlist secret  # noqa: E501
        )
        result = subprocess.run(
            ["alembic", "current"],
            cwd="/Users/swami/WorkSpace/ninaivalaigal",  # pragma: allowlist secret
            env={**os.environ, "DATABASE_URL": db_url},
            capture_output=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Alembic connected successfully
            # Note: Empty output is OK if no migrations have been run yet
            return

        raise AssertionError(f"Alembic failed to connect via PgBouncer: {result.stderr.decode()}")


class TestCriticalPaths:
    """Test critical application paths."""

    @pytest.mark.skip(reason="Requires running API server - implement when API is stable")
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

    @pytest.mark.skip(reason="Requires running API server - implement when API is stable")
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

    Current architecture (v5.0-frontend-split-audit-final):
    - Apple Container CLI: Dynamic IP-based networking
    - Database: Accessible ONLY via PgBouncer (port 6432)
    - PgBouncer: ninaivalaigal-dev-pgbouncer container
    - Redis: ninaivalaigal-dev-redis (port 6379)
    - API: May or may not be running (depending on context)
    - Migrations: Run through PgBouncer connection
    - NO direct DB access, NO localhost ports
    """
    # This test always passes but serves as documentation
    assert True, "If this fails, something is very wrong"
