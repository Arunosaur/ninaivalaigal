#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
ORM Tenancy Guard

Database-level tenant isolation with SQLAlchemy integration to prevent
cross-tenant data access in multi-tenant applications.
"""

import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

logger = logging.getLogger(__name__)


class TenantContext:
    """Thread-local tenant context."""

    def __init__(self):
        """Initialize instance."""
        self._tenant_id: str | None = None
        self._user_id: str | None = None
        self._organization_id: str | None = None

    @property
    def tenant_id(self) -> str | None:
        """Tenant id method."""
        return self._tenant_id

    @property
    def user_id(self) -> str | None:
        """User id method."""
        return self._user_id

    @property
    def organization_id(self) -> str | None:
        """Organization id method."""
        return self._organization_id

    def set_context(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        organization_id: str | None = None,
    ):
        """Set tenant context."""
        self._tenant_id = tenant_id
        self._user_id = user_id
        self._organization_id = organization_id

    def clear(self):
        """Clear tenant context."""
        self._tenant_id = None
        self._user_id = None
        self._organization_id = None

    def is_set(self) -> bool:
        """Check if tenant context is set."""
        return self._tenant_id is not None


# Global tenant context
_tenant_context = TenantContext()


class TenancyGuard:
    """ORM tenancy guard for automatic tenant filtering."""

    def __init__(self, enforce_context: bool = True):
        """Initialize instance."""
        self.enforce_context = enforce_context
        self.logger = logging.getLogger("tenancy.guard")
        self._registered_models: dict[str, str] = {}

    def register_model(self, model_class: type, tenant_column: str = "tenant_id"):
        """Register a model for tenant filtering."""
        self._registered_models[model_class.__name__] = tenant_column
        self.logger.info(f"Registered model {model_class.__name__} with tenant column {tenant_column}")

    def install_listeners(self, engine):
        """Install SQLAlchemy event listeners for tenant filtering."""

        # Install query compilation listener for automatic filtering
        # Use Query instead of Session for better compatibility
        from sqlalchemy.orm import Query

        @event.listens_for(Query, "before_compile", retval=True)
        def receive_before_compile(query):
            """Automatically filter queries by tenant context."""
            if not self.enforce_context:
                return query

            tenant_id = _tenant_context.tenant_id or _tenant_context.organization_id
            if not tenant_id:
                if self.enforce_context:
                    self.logger.warning("No tenant context set - blocking query")
                    # Return empty query result instead of raising error
                    # This prevents accidental cross-tenant data access
                    return query.filter(False)  # Empty result
                return query

            # Extract entity from query using multiple methods
            entity = None

            # Method 1: Use column_descriptions (SQLAlchemy 1.x Query)
            if hasattr(query, "column_descriptions") and query.column_descriptions:
                try:
                    desc = query.column_descriptions[0]
                    if isinstance(desc, dict):
                        entity = desc.get("entity")
                    elif hasattr(desc, "entity"):
                        entity = desc.entity
                    elif hasattr(desc, "type"):
                        entity = desc.type
                except (KeyError, IndexError, AttributeError):
                    pass

            # Method 2: Try _bind_mapper (SQLAlchemy internal)
            if not entity and hasattr(query, "_bind_mapper") and query._bind_mapper:
                entity = query._bind_mapper.class_

            # Method 3: Try _entities (some SQLAlchemy versions)
            if not entity and hasattr(query, "_entities") and query._entities:
                try:
                    entity_desc = query._entities[0]
                    if hasattr(entity_desc, "entity_zero") and hasattr(entity_desc.entity_zero, "entity"):
                        entity = entity_desc.entity_zero.entity
                    elif hasattr(entity_desc, "entity"):
                        entity = entity_desc.entity
                    elif hasattr(entity_desc, "mapper"):
                        entity = entity_desc.mapper.class_
                except (AttributeError, IndexError):
                    pass

            # Method 4: Try _primary_entity (SQLAlchemy 1.4+)
            if not entity and hasattr(query, "_primary_entity") and query._primary_entity:
                try:
                    primary = query._primary_entity
                    if hasattr(primary, "mapper"):
                        entity = primary.mapper.class_
                    elif hasattr(primary, "entity"):
                        entity = primary.entity
                except AttributeError:
                    pass

            # Check if we found a valid model entity
            if (
                entity
                and isinstance(entity, type)
                and (hasattr(entity, "__table__") or hasattr(entity, "__tablename__"))
            ):
                model_name = entity.__name__
                if model_name in self._registered_models:
                    self.logger.debug(f"Filtering query for registered model: {model_name}")
                    query = self.filter_query(query, entity)
                else:
                    self.logger.debug(f"Model {model_name} not registered for tenant filtering, skipping")
            else:
                self.logger.debug(f"Could not extract entity from query: {type(query)}")

            self.logger.debug(f"Applied tenant filter (tenant_id={tenant_id})")
            return query

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Intercept SQL execution to add tenant filtering."""
            if not self.enforce_context:
                return

            # Allow DDL operations (CREATE, DROP, ALTER) and system queries to bypass tenant checks
            # These are system-level operations that don't need tenant context
            statement_str = statement if isinstance(statement, str) else str(statement)
            statement_upper = statement_str.upper()

            # DDL keywords
            ddl_keywords = [
                "CREATE TABLE",
                "DROP TABLE",
                "ALTER TABLE",
                "CREATE INDEX",
                "DROP INDEX",
                "CREATE SCHEMA",
                "DROP SCHEMA",
                "CREATE SEQUENCE",
                "DROP SEQUENCE",
                "CREATE VIEW",
                "DROP VIEW",
                "CREATE TYPE",
                "DROP TYPE",
            ]

            # System/metadata queries
            system_patterns = [
                "INFORMATION_SCHEMA",
                "PG_CATALOG",
                "SELECT VERSION()",
                "SELECT CURRENT_",
                "SELECT PG_",
                "SELECT 1",  # Health checks
                "FROM PG_",  # PostgreSQL catalog queries
                "FROM INFORMATION_SCHEMA",  # Information schema queries
            ]

            # Root entity operations - Organizations are root entities and don't belong to organizations
            root_entity_patterns = [
                "INSERT INTO ORGANIZATIONS",  # Creating organizations doesn't need tenant context
            ]

            if any(keyword in statement_upper for keyword in ddl_keywords):
                self.logger.debug("DDL operation detected, bypassing tenant check")
                return

            if any(pattern in statement_upper for pattern in system_patterns):
                self.logger.debug("System/metadata query detected, bypassing tenant check")
                return

            if any(pattern in statement_upper for pattern in root_entity_patterns):
                self.logger.debug("Root entity operation detected (Organizations), bypassing tenant check")
                return

            tenant_id = _tenant_context.tenant_id or _tenant_context.organization_id
            if not tenant_id:
                self.logger.warning("No tenant context set for query execution")
                if self.enforce_context:
                    raise ValueError("Tenant context required but not set")

            # Log query execution with tenant context
            self.logger.debug(f"Executing query with tenant_id={tenant_id}")

    def validate_access(self, model_instance: Any, operation: str = "read") -> bool:
        """Validate tenant access for model instance."""
        if not self.enforce_context:
            return True

        model_name = model_instance.__class__.__name__
        tenant_column = self._registered_models.get(model_name)

        if not tenant_column:
            # Model not registered for tenancy, allow access
            return True

        # Use organization_id first (more specific), fallback to tenant_id
        current_tenant = _tenant_context.organization_id or _tenant_context.tenant_id
        if not current_tenant:
            self.logger.error(f"No tenant context for {operation} operation on {model_name}")
            return False

        instance_tenant = getattr(model_instance, tenant_column, None)
        if instance_tenant != current_tenant:
            self.logger.error(
                f"Tenant access violation: {operation} on {model_name} "
                f"(instance_tenant={instance_tenant}, current_tenant={current_tenant})"
            )
            return False

        return True

    def filter_query(self, query, model_class: type):
        """Add tenant filtering to query."""
        if not self.enforce_context:
            return query

        model_name = model_class.__name__
        tenant_column = self._registered_models.get(model_name)

        if not tenant_column:
            return query

        # Use organization_id first (more specific), fallback to tenant_id
        tenant_id = _tenant_context.organization_id or _tenant_context.tenant_id
        if not tenant_id:
            if self.enforce_context:
                raise ValueError(f"Tenant context required for querying {model_name}")
            return query

        # Add tenant filter
        # For SQLAlchemy 1.x Query objects, use filter() method
        # For SQLAlchemy 2.x Select objects, use where() method
        tenant_attr = getattr(model_class, tenant_column)

        # Check if query is SQLAlchemy 1.x Query or 2.x Select
        if hasattr(query, "filter"):
            # SQLAlchemy 1.x Query object
            return query.filter(tenant_attr == tenant_id)
        elif hasattr(query, "where"):
            # SQLAlchemy 2.x Select object
            return query.where(tenant_attr == tenant_id)
        else:
            # Fallback: try filter first, then where
            try:
                return query.filter(tenant_attr == tenant_id)
            except AttributeError:
                return query.where(tenant_attr == tenant_id)


# Global tenancy guard
_tenancy_guard = TenancyGuard()


def get_tenant_context() -> TenantContext:
    """Get current tenant context."""
    return _tenant_context


def set_tenant_context(
    tenant_id: str | None = None,
    user_id: str | None = None,
    organization_id: str | None = None,
):
    """Set tenant context."""
    _tenant_context.set_context(tenant_id, user_id, organization_id)


def clear_tenant_context():
    """Clear tenant context."""
    _tenant_context.clear()


@contextmanager
def tenant_context(
    tenant_id: str | None = None,
    user_id: str | None = None,
    organization_id: str | None = None,
):
    """Context manager for tenant context."""
    old_tenant = _tenant_context.tenant_id
    old_user = _tenant_context.user_id
    old_org = _tenant_context.organization_id

    try:
        _tenant_context.set_context(tenant_id, user_id, organization_id)
        yield
    finally:
        _tenant_context.set_context(old_tenant, old_user, old_org)


def require_tenant_context(func):
    """Decorator to require tenant context."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not _tenant_context.is_set():
            raise ValueError("Tenant context required")
        return func(*args, **kwargs)

    return wrapper


def tenant_isolated(tenant_column: str = "tenant_id"):
    """Decorator to mark model as tenant-isolated."""

    def decorator(model_class):
        _tenancy_guard.register_model(model_class, tenant_column)
        return model_class

    return decorator


def validate_tenant_access(model_instance: Any, operation: str = "read") -> bool:
    """Validate tenant access for model instance."""
    return _tenancy_guard.validate_access(model_instance, operation)


def filter_by_tenant(query: Select, model_class: type) -> Select:
    """Add tenant filtering to query."""
    return _tenancy_guard.filter_query(query, model_class)


def install_tenancy_guard(engine, enforce_context: bool = True):
    """Install tenancy guard on SQLAlchemy engine."""
    global _tenancy_guard
    _tenancy_guard = TenancyGuard(enforce_context)
    _tenancy_guard.install_listeners(engine)

    # Register all models that need tenant isolation
    register_tenant_models()


def register_tenant_models():
    """Register all models with organization/team isolation."""
    try:
        from server.database.models import Context, ContextPermission, Team

        # Register models with organization_id column
        _tenancy_guard.register_model(Team, tenant_column="organization_id")
        _tenancy_guard.register_model(Context, tenant_column="organization_id")
        _tenancy_guard.register_model(ContextPermission, tenant_column="organization_id")

        # Note: Memory model doesn't have organization_id directly,
        # but should be filtered by user_id or context.organization_id
        # This requires custom filtering logic

        _tenancy_guard.logger.info("Registered all tenant-isolated models")
    except ImportError:
        _tenancy_guard.logger.warning("Could not import models for registration")


class TenantAwareSession(Session):
    """Session that automatically applies tenant filtering."""

    def query(self, *entities, **kwargs):
        """Override query to add tenant filtering."""
        query = super().query(*entities, **kwargs)

        # Apply tenant filtering to each entity
        for entity in entities:
            if hasattr(entity, "__name__"):  # It's a model class
                query = filter_by_tenant(query, entity)

        return query


def create_tenant_aware_session(session_factory, **kwargs):
    """Create tenant-aware session."""
    return TenantAwareSession(bind=session_factory.bind, **kwargs)


# FastAPI integration
async def get_tenant_from_jwt(token: str) -> str | None:
    """Extract tenant ID from JWT token."""
    try:
        from .rbac.context import get_subject_ctx

        context = get_subject_ctx(token)
        return context.organization_id or context.user_id
    except Exception:
        return None


def create_tenant_middleware():
    """Create FastAPI middleware for tenant context."""
    from fastapi import Request

    async def tenant_middleware(request: Request, call_next):
        # Extract tenant from JWT
        auth_header = request.headers.get("authorization", "")
        org_id = None
        user_id = None

        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

            try:
                # Try multiple methods to extract tenant info
                tenant_id = await get_tenant_from_jwt(token)
                if tenant_id:
                    org_id = tenant_id
            except Exception as e:
                # Graceful fallback: tenant extraction failed, continue without tenant context
                logger.debug("Tenant extraction from JWT failed", error=str(e))

            # Also try direct JWT parsing
            try:
                import os

                import jwt

                secret = os.getenv("NINAIVALAIGAL_JWT_SECRET")
                if secret:
                    payload = jwt.decode(token, secret, algorithms=["HS256"])
                    org_id = payload.get("org_id") or payload.get("organization_id")
                    user_id = payload.get("user_id") or payload.get("sub")
            except Exception as e:
                # Graceful fallback: JWT parsing failed, continue without tenant context
                # This is expected when token format doesn't match or secret is missing
                logger.debug("JWT parsing failed for tenant extraction", error=str(e))

        # Set tenant context if available
        if org_id or user_id:
            with tenant_context(tenant_id=org_id, user_id=user_id, organization_id=org_id):
                return await call_next(request)

        # If no tenant context, still proceed (may be public endpoint)
        # But enforce_context will block queries that need tenant
        return await call_next(request)

    return tenant_middleware
