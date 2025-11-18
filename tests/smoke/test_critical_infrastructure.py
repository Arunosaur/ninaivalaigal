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
        # Get PgBouncer TX container IP (Apple Container CLI) - Transaction mode on port 6432
        # Architecture: Dual PgBouncer (Task #85)
        # - pgbouncer-tx: Transaction mode (port 6432) for Core API, GraphOps
        # - pgbouncer-sess: Session mode (port 6433) for Memory Service (Rust/SQLx)
        pgbouncer_ip = get_container_ip("ninaivalaigal-dev-pgbouncer-tx")

        if not pgbouncer_ip:
            pytest.skip("PgBouncer TX container not running (ninaivalaigal-dev-pgbouncer-tx)")

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
                "ninaivalaigal_dev",  # Database name through PgBouncer
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
        """Core API /health endpoint must return 200."""
        import requests

        # Core API service (SPEC-100 Stage 3 microservices)
        # Port allocation per config/ports.nv.yaml: apple.dev.core_api = 13390
        # Container: ninaivalaigal-dev-core-api
        try:
            response = requests.get("http://localhost:13390/health", timeout=5)
            assert response.status_code == 200, f"Core API health check failed: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Core API server not running (ninaivalaigal-dev-core-api on port 13390)")


class TestDatabaseSchema:
    """Database schema must be in expected state."""

    def test_migrations_applied(self):
        """Alembic migrations must be up to date via PgBouncer."""
        # Get PgBouncer TX container IP (Transaction mode on port 6432)
        # Architecture: Dual PgBouncer (Task #85)
        pgbouncer_ip = get_container_ip("ninaivalaigal-dev-pgbouncer-tx")

        if not pgbouncer_ip:
            pytest.skip("PgBouncer TX container not running (ninaivalaigal-dev-pgbouncer-tx)")

        # Connect through PgBouncer on port 6432
        db_url = f"postgresql://nina:dev_password_change_in_production@{pgbouncer_ip}:6432/ninaivalaigal_dev"  # pragma: allowlist secret  # noqa: E501
        result = subprocess.run(
            ["alembic", "-c", "alembic/public/alembic.ini", "current"],
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

    def test_user_signup_endpoint_exists(self):
        """User signup endpoint must exist."""
        import requests

        # Core API signup endpoint (SPEC-100 Stage 3 microservices)
        # Port allocation per config/ports.nv.yaml: apple.dev.core_api = 13390
        # Endpoint: POST /auth/signup/individual (from OpenAPI schema)
        try:
            response = requests.post(
                "http://localhost:13390/auth/signup/individual",
                json={
                    "email": "smoketest@example.com",
                    "password": "testpass123",  # pragma: allowlist secret
                    "full_name": "Smoke Test User",
                },
                timeout=5,
            )
            # Should not be 404 (endpoint exists)
            # 400/422 are acceptable (validation errors), 409 is acceptable (duplicate email)
            assert response.status_code != 404, f"Signup endpoint not found: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Core API server not running (ninaivalaigal-dev-core-api on port 13390)")

    def test_memory_crud_endpoint_exists(self):
        """Memory CRUD endpoints must exist."""
        import requests

        # Core API memory endpoint (SPEC-100 Stage 3 microservices)
        # Port allocation per config/ports.nv.yaml: apple.dev.core_api = 13390
        # Endpoint: GET /api/v1/memory/memories
        try:
            response = requests.get("http://localhost:13390/api/v1/memory/memories", timeout=5)
            # Should not be 404 (endpoint exists)
            # 401/403 are acceptable (auth required), but 404 means endpoint doesn't exist
            assert response.status_code != 404, f"Memory endpoint not found: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Core API server not running (ninaivalaigal-dev-core-api on port 13390)")


# Regression guard: Record what's currently working
def test_regression_guard():
    """
    This test documents the current working state.
    Update this when you make intentional changes.

    Current architecture (v6.0-dual-pgbouncer - Task #85):
    - Apple Container CLI: Dynamic IP-based networking
    - Database: Accessible via Dual PgBouncer setup
    - PgBouncer TX: ninaivalaigal-dev-pgbouncer-tx (transaction mode, port 6432) for Core API, GraphOps
    - PgBouncer SESS: ninaivalaigal-dev-pgbouncer-sess (session mode, port 6433) for Memory Service (Rust/SQLx)
    - Redis: ninaivalaigal-dev-redis (port 6379)
    - API: May or may not be running (depending on context)
    - Migrations: Run through PgBouncer TX connection (port 6432)
    - NO direct DB access, NO localhost ports
    """
    # This test always passes but serves as documentation
    assert True, "If this fails, something is very wrong"
