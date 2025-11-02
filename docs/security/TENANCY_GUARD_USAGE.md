# TenancyGuard Usage Guide

**US#117: ORM Guardrails & Multi-Tenant Isolation**

## Overview

TenancyGuard provides automatic database-level tenant isolation for multi-tenant applications. It automatically filters all database queries by organization, preventing cross-tenant data leaks.

## Quick Start

### Installation

TenancyGuard is automatically installed when the database engine is created:

```python
from server.database import DatabaseManager

db_manager = DatabaseManager(database_url="postgresql://...")
# TenancyGuard is automatically installed and enabled
```

### Setting Tenant Context

Tenant context is automatically extracted from JWT tokens via FastAPI middleware. For manual operations:

```python
from server.security.orm.tenancy_guard import set_tenant_context, tenant_context

# Set tenant context
set_tenant_context(
    organization_id="org-123",
    user_id="user-456"
)

# Use context manager for temporary context
with tenant_context(organization_id="org-123"):
    # All queries here are filtered by org-123
    teams = db.query(Team).all()
```

### Model Registration

Models with `organization_id` columns are automatically registered. To register custom models:

```python
from server.security.orm.tenancy_guard import tenant_isolated

@tenant_isolated(tenant_column="organization_id")
class MyModel(Base):
    organization_id = Column(String)
    # ...
```

## Features

### Automatic Query Filtering

All queries are automatically filtered by tenant context:

```python
set_tenant_context(organization_id="org-123")
teams = db.query(Team).all()
# Only returns teams where organization_id = 'org-123'
```

### Access Validation

Validate instance-level access before operations:

```python
from server.security.orm.tenancy_guard import validate_tenant_access

team = db.query(Team).filter_by(id="team-123").first()
if validate_tenant_access(team, "read"):
    # Safe to access
    pass
```

### Context Management

Use context managers for nested operations:

```python
with tenant_context(organization_id="org-123"):
    # Create operations
    team = Team(name="New Team", organization_id="org-123")
    db.add(team)
    db.commit()
```

## Security

### Defense in Depth

TenancyGuard provides defense in depth:
- **API Level**: FastAPI middleware extracts tenant from JWT
- **ORM Level**: Automatic query filtering
- **Instance Level**: Access validation before operations

### Bypass Prevention

Tenant filtering cannot be bypassed except:
- System-level operations (with audit logging)
- Explicit context override (documented and reviewed)

## Performance

- **Overhead**: <1ms per query
- **No Additional Round-trips**: Filtering happens at SQLAlchemy level
- **Indexed Columns**: Uses organization_id indexes for fast filtering

## Testing

See `server/tests/security/test_tenancy_guard.py` for examples.

## Related Documentation

- `server/security/orm/tenancy_guard.py` - Implementation
- `governance/reports/US117_PROGRESS_REPORT.md` - Progress report
