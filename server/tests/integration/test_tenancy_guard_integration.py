#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Integration tests for TenancyGuard - US#117: ORM Guardrails & Multi-Tenant Isolation

Tests integration with actual database models and real-world scenarios.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from server.security.orm.tenancy_guard import (
    clear_tenant_context,
    install_tenancy_guard,
    set_tenant_context,
)


def _get_test_database_url():
    """Get test database URL from environment.

    Uses existing DATABASE_URL from environment which should already be configured
    with correct credentials. Uses the same database (no separate test DB).
    """
    # Use existing DATABASE_URL from environment
    db_url = os.getenv("DATABASE_URL") or os.getenv("NINAIVALAIGAL_DATABASE_URL")

    if db_url:
        # Use the database as-is (no separate test DB for now)
        return db_url

    # Fallback: build from components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("PGBOUNCER_PORT") or os.getenv("POSTGRES_PORT", "6432")
    user = os.getenv("NINA_DB_USER") or os.getenv("POSTGRES_USER", "nina")
    password = os.getenv("NINA_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB", "nina")

    if not password:
        return None  # Cannot build URL without password

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


@pytest.fixture(scope="module")
def test_db_engine():
    """Create test database engine with PostgreSQL."""
    db_url = _get_test_database_url()

    if not db_url:
        pytest.skip("DATABASE_URL not configured")

    try:
        engine = create_engine(db_url, echo=False)
        # Test connection
        with engine.connect() as conn:
            conn.execute(conn.text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"PostgreSQL database not available: {e}")

    # Install tenancy guard (DDL operations will bypass tenant checks)
    install_tenancy_guard(engine, enforce_context=True)

    # Register models for tenant filtering
    from server.security.orm.tenancy_guard import register_tenant_models

    register_tenant_models()

    # Import models - database.__init__ already calls extend_team_model()
    # Reflect existing tables (don't create - tables already exist in database)
    from server.database import Base, Context, Organization, Team  # noqa: F401

    # Reflect the actual database schema to sync metadata
    Base.metadata.reflect(bind=engine)

    yield engine

    # Cleanup: drop test tables (optional, comment out if you want to keep data)
    # Base.metadata.drop_all(bind=engine)
    clear_tenant_context()


@pytest.fixture
def test_db(test_db_engine):
    """Create test database session."""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        clear_tenant_context()


class TestTenancyGuardIntegration:
    """Integration tests with actual database models"""

    def test_team_isolation(self, test_db):
        """Test that teams are isolated by organization_id"""
        from uuid import uuid4

        from server.database import Organization, Team

        # Create organizations first
        org1_id = uuid4()
        org2_id = uuid4()

        # Create organizations without tenant context (DDL/admin operation)
        clear_tenant_context()
        org1 = Organization(id=org1_id, name=f"Org 1 {org1_id.hex[:8]}")
        org2 = Organization(id=org2_id, name=f"Org 2 {org2_id.hex[:8]}")
        test_db.add_all([org1, org2])
        test_db.commit()

        # Create teams for different organizations
        # Set tenant context to org1 for creating teams
        set_tenant_context(organization_id=org1_id)

        # Create teams
        team1 = Team(id=uuid4(), name="Team 1", organization_id=org1_id)
        team2 = Team(id=uuid4(), name="Team 2", organization_id=org1_id)

        test_db.add_all([team1, team2])
        test_db.commit()

        # Switch to org2 context for creating team3
        set_tenant_context(organization_id=org2_id)
        team3 = Team(id=uuid4(), name="Team 3", organization_id=org2_id)
        test_db.add(team3)
        test_db.commit()

        # Query as org1 - should only see org1 teams
        set_tenant_context(organization_id=org1_id)
        org1_teams = test_db.query(Team).all()

        # Filter by our org1_id to verify isolation
        org1_filtered = [t for t in org1_teams if str(t.organization_id) == str(org1_id)]

        assert len(org1_filtered) >= 2, (
            f"Expected at least 2 teams for org1, but found teams: "
            f"{[(str(t.organization_id), t.name) for t in org1_teams]}"
        )
        # Verify all returned teams belong to org1 (TenancyGuard should filter)
        assert all(str(team.organization_id) == str(org1_id) for team in org1_teams), (
            f"TenancyGuard should filter to only org1 teams, but found: "
            f"{[(str(t.organization_id), t.name) for t in org1_teams]}"
        )
        assert team3 not in org1_teams

        # Query as org2 - should only see org2 teams
        set_tenant_context(organization_id=org2_id)
        org2_teams = test_db.query(Team).all()

        org2_filtered = [t for t in org2_teams if str(t.organization_id) == str(org2_id)]

        assert len(org2_filtered) >= 1, (
            f"Expected at least 1 team for org2, but found: "
            f"{[(str(t.organization_id), t.name) for t in org2_teams]}"
        )
        assert all(str(t.organization_id) == str(org2_id) for t in org2_teams), (
            f"TenancyGuard should filter to only org2 teams, but found: "
            f"{[(str(t.organization_id), t.name) for t in org2_teams]}"
        )

    def test_context_isolation(self, test_db):
        """Test that contexts are isolated by organization_id"""
        from uuid import uuid4

        from server.database import Context, Organization

        org1_id = uuid4()
        org2_id = uuid4()

        # Create organizations first (required for foreign key)
        clear_tenant_context()
        org1 = Organization(id=org1_id, name=f"Org 1 {org1_id.hex[:8]}")
        org2 = Organization(id=org2_id, name=f"Org 2 {org2_id.hex[:8]}")
        test_db.add_all([org1, org2])
        test_db.commit()

        # Create contexts for different orgs
        set_tenant_context(organization_id=org1_id)
        ctx1 = Context(id=uuid4(), name="Context 1", organization_id=org1_id)
        test_db.add(ctx1)
        test_db.commit()

        set_tenant_context(organization_id=org2_id)
        ctx2 = Context(id=uuid4(), name="Context 2", organization_id=org2_id)
        test_db.add(ctx2)
        test_db.commit()

        # Query as org1 - should only see org1 contexts
        set_tenant_context(organization_id=org1_id)
        org1_contexts = test_db.query(Context).all()

        # Filter by our org1_id to verify isolation
        org1_filtered = [ctx for ctx in org1_contexts if str(ctx.organization_id) == str(org1_id)]

        assert (
            len(org1_filtered) >= 1
        ), f"Expected at least 1 context for org1, but found contexts: {[str(c.organization_id) for c in org1_contexts]}"
        # Verify all returned contexts belong to org1 (TenancyGuard should filter)
        assert all(
            str(ctx.organization_id) == str(org1_id) for ctx in org1_contexts
        ), f"TenancyGuard should filter to only org1 contexts, but found: {[(str(c.organization_id), c.name) for c in org1_contexts]}"

    def test_cross_org_access_blocked(self, test_db):
        """Test that cross-org access is blocked"""
        from uuid import uuid4

        from server.database import Organization, Team
        from server.security.orm.tenancy_guard import validate_tenant_access

        org1_id = uuid4()
        org2_id = uuid4()

        # Create organizations first
        clear_tenant_context()
        org1 = Organization(id=org1_id, name=f"Org 1 {org1_id.hex[:8]}")
        org2 = Organization(id=org2_id, name=f"Org 2 {org2_id.hex[:8]}")
        test_db.add_all([org1, org2])
        test_db.commit()

        # Create team in org2
        set_tenant_context(organization_id=org2_id)
        team = Team(id=uuid4(), name="Org2 Team", organization_id=org2_id)
        test_db.add(team)
        test_db.commit()

        # Try to access as org1 - should be blocked
        set_tenant_context(organization_id=org1_id)
        from server.security.orm.tenancy_guard import validate_tenant_access

        assert validate_tenant_access(team, "read") is False

    def test_no_tenant_context_blocks_queries(self, test_db):
        """Test that queries without tenant context are blocked or return empty"""
        from uuid import uuid4

        from server.database import Organization, Team

        # Create organization first
        org_id = uuid4()
        clear_tenant_context()
        org = Organization(id=org_id, name=f"Test Org {org_id.hex[:8]}")
        test_db.add(org)
        test_db.commit()

        # Create a team with tenant context
        set_tenant_context(organization_id=org_id)
        team = Team(id=uuid4(), name="Team", organization_id=org_id)
        test_db.add(team)
        test_db.commit()

        # Clear tenant context
        clear_tenant_context()

        # Query without tenant context should be blocked/raise error or return empty
        # The before_compile handler returns query.filter(False) which should return empty,
        # but before_cursor_execute also enforces context and raises ValueError
        try:
            teams = test_db.query(Team).all()
            # If query succeeded, it should return empty (filtered out)
            assert len(teams) == 0, "Query without tenant context should return empty results"
        except ValueError as e:
            # If query was blocked by before_cursor_execute, that's also acceptable
            assert "Tenant context required" in str(e), "Error should mention tenant context requirement"
            # Verify no teams were accessed
            pass
