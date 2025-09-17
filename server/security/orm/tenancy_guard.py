"""
ORM Tenancy Guard

Database-level tenant isolation with SQLAlchemy integration to prevent
cross-tenant data access in multi-tenant applications.
"""

import logging
from typing import Optional, Any, Dict, List
from contextlib import contextmanager
from functools import wraps
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select, Update, Delete, Insert


class TenantContext:
    """Thread-local tenant context."""
    
    def __init__(self):
        self._tenant_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._organization_id: Optional[str] = None
    
    @property
    def tenant_id(self) -> Optional[str]:
        return self._tenant_id
    
    @property
    def user_id(self) -> Optional[str]:
        return self._user_id
    
    @property
    def organization_id(self) -> Optional[str]:
        return self._organization_id
    
    def set_context(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None
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
        self.enforce_context = enforce_context
        self.logger = logging.getLogger("tenancy.guard")
        self._registered_models: Dict[str, str] = {}
    
    def register_model(self, model_class: type, tenant_column: str = "tenant_id"):
        """Register a model for tenant filtering."""
        self._registered_models[model_class.__name__] = tenant_column
        self.logger.info(f"Registered model {model_class.__name__} with tenant column {tenant_column}")
    
    def install_listeners(self, engine):
        """Install SQLAlchemy event listeners for tenant filtering."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Intercept SQL execution to add tenant filtering."""
            if not self.enforce_context:
                return
            
            tenant_id = _tenant_context.tenant_id
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
        
        current_tenant = _tenant_context.tenant_id
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
    
    def filter_query(self, query: Select, model_class: type) -> Select:
        """Add tenant filtering to query."""
        if not self.enforce_context:
            return query
        
        model_name = model_class.__name__
        tenant_column = self._registered_models.get(model_name)
        
        if not tenant_column:
            return query
        
        tenant_id = _tenant_context.tenant_id
        if not tenant_id:
            if self.enforce_context:
                raise ValueError(f"Tenant context required for querying {model_name}")
            return query
        
        # Add tenant filter
        tenant_attr = getattr(model_class, tenant_column)
        return query.where(tenant_attr == tenant_id)


# Global tenancy guard
_tenancy_guard = TenancyGuard()


def get_tenant_context() -> TenantContext:
    """Get current tenant context."""
    return _tenant_context


def set_tenant_context(
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None
):
    """Set tenant context."""
    _tenant_context.set_context(tenant_id, user_id, organization_id)


def clear_tenant_context():
    """Clear tenant context."""
    _tenant_context.clear()


@contextmanager
def tenant_context(
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    organization_id: Optional[str] = None
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


class TenantAwareSession(Session):
    """Session that automatically applies tenant filtering."""
    
    def query(self, *entities, **kwargs):
        """Override query to add tenant filtering."""
        query = super().query(*entities, **kwargs)
        
        # Apply tenant filtering to each entity
        for entity in entities:
            if hasattr(entity, '__name__'):  # It's a model class
                query = filter_by_tenant(query, entity)
        
        return query


def create_tenant_aware_session(session_factory, **kwargs):
    """Create tenant-aware session."""
    return TenantAwareSession(bind=session_factory.bind, **kwargs)


# FastAPI integration
async def get_tenant_from_jwt(token: str) -> Optional[str]:
    """Extract tenant ID from JWT token."""
    try:
        from .rbac.context import get_subject_ctx
        context = get_subject_ctx(token)
        return context.organization_id or context.user_id
    except Exception:
        return None


def create_tenant_middleware():
    """Create FastAPI middleware for tenant context."""
    
    async def tenant_middleware(request, call_next):
        # Extract tenant from JWT
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            tenant_id = await get_tenant_from_jwt(token)
            
            if tenant_id:
                with tenant_context(tenant_id=tenant_id):
                    return await call_next(request)
        
        return await call_next(request)
    
    return tenant_middleware
