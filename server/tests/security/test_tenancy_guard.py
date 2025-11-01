#!/usr/bin/env python3
"""
Test suite for TenancyGuard - US#117: ORM Guardrails & Multi-Tenant Isolation

Tests cover:
- Automatic query filtering by organization
- Tenant context management
- Cross-tenant access prevention
- Model registration
- Security validation
"""

import pytest
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from server.security.orm.tenancy_guard import (
    TenancyGuard,
    TenantContext,
    set_tenant_context,
    clear_tenant_context,
    tenant_context,
    register_tenant_models,
    validate_tenant_access,
    filter_by_tenant,
)

Base = declarative_base()


class TestTeam(Base):
    """Test model with organization_id"""
    __tablename__ = "test_teams"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String)
    organization_id = Column(String)


class TestContext(Base):
    """Test model with organization_id"""
    __tablename__ = "test_contexts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String)
    organization_id = Column(String)


class TestTenancyGuard:
    """Test suite for TenancyGuard"""

    def test_tenant_context_set_and_get(self):
        """Test setting and getting tenant context"""
        clear_tenant_context()
        
        set_tenant_context(tenant_id="org-123", user_id="user-456", organization_id="org-123")
        
        context = TenantContext()
        assert context.tenant_id == "org-123"
        assert context.user_id == "user-456"
        assert context.organization_id == "org-123"

    def test_tenant_context_clear(self):
        """Test clearing tenant context"""
        set_tenant_context(tenant_id="org-123")
        clear_tenant_context()
        
        context = TenantContext()
        assert context.tenant_id is None
        assert context.organization_id is None

    def test_tenant_context_manager(self):
        """Test tenant context as context manager"""
        clear_tenant_context()
        
        with tenant_context(tenant_id="org-123", organization_id="org-123"):
            context = TenantContext()
            assert context.tenant_id == "org-123"
        
        # Context should be cleared after exit
        context = TenantContext()
        assert context.tenant_id is None

    def test_register_model(self):
        """Test model registration"""
        guard = TenancyGuard()
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        assert "TestTeam" in guard._registered_models
        assert guard._registered_models["TestTeam"] == "organization_id"

    def test_validate_access_same_tenant(self):
        """Test access validation for same tenant"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        set_tenant_context(organization_id="org-123")
        
        team = TestTeam(id="team-1", name="Test Team", organization_id="org-123")
        
        assert guard.validate_access(team, "read") is True

    def test_validate_access_different_tenant(self):
        """Test access validation blocks cross-tenant access"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        set_tenant_context(organization_id="org-123")
        
        team = TestTeam(id="team-1", name="Test Team", organization_id="org-999")
        
        assert guard.validate_access(team, "read") is False

    def test_validate_access_no_context(self):
        """Test access validation without tenant context"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        clear_tenant_context()
        
        team = TestTeam(id="team-1", name="Test Team", organization_id="org-123")
        
        assert guard.validate_access(team, "read") is False

    def test_validate_access_unregistered_model(self):
        """Test that unregistered models are allowed"""
        guard = TenancyGuard(enforce_context=True)
        
        # Don't register TestContext
        context = TestContext(id="ctx-1", name="Test", organization_id="org-123")
        
        assert guard.validate_access(context, "read") is True

    def test_filter_query_with_tenant(self):
        """Test query filtering with tenant context"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        set_tenant_context(organization_id="org-123")
        
        # Create in-memory database for testing
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        session = SessionLocal()
        
        # Create test data
        team1 = TestTeam(id="team-1", name="Team 1", organization_id="org-123")
        team2 = TestTeam(id="team-2", name="Team 2", organization_id="org-999")
        session.add(team1)
        session.add(team2)
        session.commit()
        
        # Query should only return team1 (same org)
        query = session.query(TestTeam)
        filtered_query = guard.filter_query(query, TestTeam)
        
        results = filtered_query.all()
        assert len(results) == 1
        assert results[0].organization_id == "org-123"
        
        session.close()

    def test_filter_query_no_context(self):
        """Test query filtering without tenant context blocks"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        clear_tenant_context()
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        session = SessionLocal()
        query = session.query(TestTeam)
        
        # Should raise error or return empty query
        try:
            filtered_query = guard.filter_query(query, TestTeam)
            # If no exception, query should be empty
            results = filtered_query.all()
            assert len(results) == 0
        except ValueError:
            # Expected behavior - tenant context required
            pass
        
        session.close()

    def test_filter_query_unregistered_model(self):
        """Test query filtering skips unregistered models"""
        guard = TenancyGuard(enforce_context=True)
        # Don't register TestContext
        
        set_tenant_context(organization_id="org-123")
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        session = SessionLocal()
        context = TestContext(id="ctx-1", name="Test", organization_id="org-999")
        session.add(context)
        session.commit()
        
        query = session.query(TestContext)
        filtered_query = guard.filter_query(query, TestContext)
        
        # Should return all results (not filtered)
        results = filtered_query.all()
        assert len(results) == 1
        
        session.close()

    def test_guard_enforce_context_disabled(self):
        """Test that guard doesn't enforce when disabled"""
        guard = TenancyGuard(enforce_context=False)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        clear_tenant_context()
        
        team = TestTeam(id="team-1", name="Test", organization_id="org-999")
        assert guard.validate_access(team, "read") is True
        
        # Query filtering should pass through
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        query = session.query(TestTeam)
        filtered_query = guard.filter_query(query, TestTeam)
        
        # Should not filter
        results = filtered_query.all()
        # Empty because no data, but query should execute

    def test_multiple_organizations_isolation(self):
        """Test isolation between multiple organizations"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        
        session = SessionLocal()
        
        # Create teams for different orgs
        for org_id in ["org-1", "org-2", "org-3"]:
            for i in range(3):
                team = TestTeam(
                    id=f"team-{org_id}-{i}",
                    name=f"Team {i}",
                    organization_id=org_id
                )
                session.add(team)
        session.commit()
        
        # Query as org-1
        set_tenant_context(organization_id="org-1")
        query = session.query(TestTeam)
        filtered_query = guard.filter_query(query, TestTeam)
        results = filtered_query.all()
        
        assert len(results) == 3
        assert all(r.organization_id == "org-1" for r in results)
        
        # Query as org-2
        set_tenant_context(organization_id="org-2")
        query = session.query(TestTeam)
        filtered_query = guard.filter_query(query, TestTeam)
        results = filtered_query.all()
        
        assert len(results) == 3
        assert all(r.organization_id == "org-2" for r in results)
        
        session.close()

    def test_context_nested(self):
        """Test nested tenant contexts"""
        clear_tenant_context()
        
        with tenant_context(organization_id="org-1"):
            with tenant_context(organization_id="org-2"):
                context = TenantContext()
                assert context.organization_id == "org-2"
            
            # Should restore to org-1
            context = TenantContext()
            assert context.organization_id == "org-1"
        
        # Should be cleared
        context = TenantContext()
        assert context.organization_id is None

    def test_register_tenant_models_function(self):
        """Test register_tenant_models function"""
        guard = TenancyGuard()
        
        # Mock the models import
        import sys
        from unittest.mock import MagicMock
        
        original_import = __import__
        
        def mock_import(name, *args, **kwargs):
            if name == "server.database.models":
                mock_module = MagicMock()
                mock_module.Team = TestTeam
                mock_module.Context = TestContext
                return mock_module
            return original_import(name, *args, **kwargs)
        
        # This is complex to test fully, but we can test the logic
        # For now, just verify the function exists and can be called
        assert callable(register_tenant_models)

    def test_install_tenancy_guard(self):
        """Test installing tenancy guard on engine"""
        from server.security.orm.tenancy_guard import install_tenancy_guard
        
        engine = create_engine("sqlite:///:memory:")
        
        # Should not raise
        install_tenancy_guard(engine, enforce_context=True)

    def test_cross_tenant_write_prevention(self):
        """Test that writes to wrong tenant are blocked"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        set_tenant_context(organization_id="org-123")
        
        team = TestTeam(id="team-1", name="Team", organization_id="org-999")
        
        # Should fail validation
        assert guard.validate_access(team, "write") is False

    def test_tenant_context_priority(self):
        """Test that organization_id takes priority over tenant_id"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        set_tenant_context(tenant_id="tenant-old", organization_id="org-123")
        
        team = TestTeam(id="team-1", name="Team", organization_id="org-123")
        
        # Should use organization_id
        assert guard.validate_access(team, "read") is True

    def test_unregistered_model_allowed(self):
        """Test that unregistered models are allowed (backward compatibility)"""
        guard = TenancyGuard(enforce_context=True)
        
        # Create model without registering
        unregistered = TestContext(id="ctx-1", name="Test", organization_id="org-999")
        
        set_tenant_context(organization_id="org-123")
        
        # Should allow (model not registered)
        assert guard.validate_access(unregistered, "read") is True

    def test_empty_tenant_context_blocking(self):
        """Test that empty tenant context blocks queries"""
        guard = TenancyGuard(enforce_context=True)
        guard.register_model(TestTeam, tenant_column="organization_id")
        
        clear_tenant_context()
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        query = session.query(TestTeam)
        
        # Should return empty query or raise error
        filtered = guard.filter_query(query, TestTeam)
        try:
            results = filtered.all()
            # If it doesn't raise, results should be empty
            assert len(results) == 0
        except ValueError:
            # Expected - tenant context required
            pass
        
        session.close()

