#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Alembic Clean Reset - Single Source of Truth Fix
# This script creates a clean, consistent migration structure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     ALEMBIC CLEAN RESET - SINGLE SOURCE OF TRUTH FIX     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Backup current migrations
print_status "Creating backup of current migrations..."
BACKUP_DIR="alembic/backup.$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r alembic/*/versions "$BACKUP_DIR/" 2>/dev/null || true
print_status "Backup created: $BACKUP_DIR"

# Clean up existing migration files
print_status "Cleaning up existing migration files..."
for env in public graphops memory intelligence compliance hipaa incident_response iso27001 pentest security soc2; do
    if [ -d "alembic/$env/versions" ]; then
        rm -rf alembic/$env/versions/*
        print_status "Cleaned: alembic/$env/versions/"
    fi
done

# Create clean migration structure
print_status "Creating clean migration structure..."

# Core API Schema (main application)
print_status "Creating Core API schema migration..."
cat > alembic/public/versions/20251118_1200_core_api_base.py << 'EOF'
"""core_api_base

Create base schema for core API application with single source of truth.
All main application tables in core_api schema.

Revision ID: 20251118_1200_core_api_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_core_api_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create core_api schema
    op.execute("CREATE SCHEMA IF NOT EXISTS core_api")
    
    # Users table with all fields
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_enforced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_method", sa.String(length=50), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="core_api",
    )
    op.create_index(op.f("ix_core_api_users_id"), "users", ["id"], unique=False, schema="core_api")
    op.create_index(op.f("ix_core_api_users_username"), "users", ["username"], unique=True, schema="core_api")
    op.create_index(op.f("ix_core_api_users_email"), "users", ["email"], unique=True, schema="core_api")

    # MFA TOTP Secrets
    op.create_table(
        "mfa_totp_secrets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret", sa.String(length=32), nullable=False),
        sa.Column("backup_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # MFA WebAuthn Credentials
    op.create_table(
        "mfa_webauthn_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.UniqueConstraint("credential_id"),
        schema="core_api",
    )

    # MFA Enforcement Policies
    op.create_table(
        "mfa_enforcement_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_role", sa.String(length=50), nullable=True),
        sa.Column("target_account_type", sa.String(length=50), nullable=True),
        sa.Column("mfa_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )

    # SSO Providers
    op.create_table(
        "sso_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=False),
        sa.Column("client_secret", sa.String(length=255), nullable=False),
        sa.Column("authorization_url", sa.String(length=500), nullable=False),
        sa.Column("token_url", sa.String(length=500), nullable=False),
        sa.Column("userinfo_url", sa.String(length=500), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )

    # User SSO Accounts
    op.create_table(
        "user_sso_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("provider_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["core_api.sso_providers.id"]),
        sa.UniqueConstraint("provider_id", "provider_user_id"),
        schema="core_api",
    )

    # Security Events
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # Anomaly Detections
    op.create_table(
        "anomaly_detections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("detection_type", sa.String(length=100), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("activity_data", sa.JSON(), nullable=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("is_false_positive", sa.Boolean(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # Device Fingerprints
    op.create_table(
        "device_fingerprints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=255), nullable=False),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.UniqueConstraint("fingerprint_hash"),
        schema="core_api",
    )

    # Risk Configurations
    op.create_table(
        "risk_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("device_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("location_weight", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("time_weight", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("behavior_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("risk_threshold_critical", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("risk_threshold_high", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("risk_threshold_medium", sa.Float(), nullable=False, server_default="0.4"),
        sa.Column("vpn_penalty", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("proxy_penalty", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("tor_penalty", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("new_device_penalty", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("unusual_location_penalty", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("unusual_time_penalty", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table("risk_configurations", schema="core_api")
    op.drop_table("device_fingerprints", schema="core_api")
    op.drop_table("anomaly_detections", schema="core_api")
    op.drop_table("security_events", schema="core_api")
    op.drop_table("user_sso_accounts", schema="core_api")
    op.drop_table("sso_providers", schema="core_api")
    op.drop_table("mfa_enforcement_policies", schema="core_api")
    op.drop_table("mfa_webauthn_credentials", schema="core_api")
    op.drop_table("mfa_totp_secrets", schema="core_api")
    op.drop_table("users", schema="core_api")
    
    # Note: Keep the core_api schema for potential reuse
EOF

# GraphOps Schema
print_status "Creating GraphOps schema migration..."
cat > alembic/graphops/versions/20251118_1200_graphops_base.py << 'EOF'
"""graphops_base

Create base schema for GraphOps service.

Revision ID: 20251118_1200_graphops_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_graphops_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Note: ag_catalog schema is created by Apache AGE extension
    # We only create our application-specific tables here
    
    # GraphOps registry tables
    op.create_table(
        "graph_schema_registry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_name", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schema_name", "schema_version"),
        schema="ag_catalog",
    )


def downgrade() -> None:
    op.drop_table("graph_schema_registry", schema="ag_catalog")
EOF

# Memory Schema
print_status "Creating Memory schema migration..."
cat > alembic/memory/versions/20251118_1200_memory_base.py << 'EOF'
"""memory_base

Create base schema for Memory service.

Revision ID: 20251118_1200_memory_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_memory_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create memory schema
    op.execute("CREATE SCHEMA IF NOT EXISTS memory")
    
    # Memory relationships
    op.create_table(
        "memory_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_memory_id", sa.Integer(), nullable=False),
        sa.Column("target_memory_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="memory",
    )


def downgrade() -> None:
    op.drop_table("memory_relationships", schema="memory")
EOF

# Intelligence Schema
print_status "Creating Intelligence schema migration..."
cat > alembic/intelligence/versions/20251118_1200_intelligence_base.py << 'EOF'
"""intelligence_base

Create base schema for Intelligence service.

Revision ID: 20251118_1200_intelligence_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_intelligence_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create intelligence_graph schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intelligence_graph")
    
    # Intelligence insights
    op.create_table(
        "intelligence_insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("insight_type", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("insight_data", sa.JSON(), nullable=False),
        sa.Column("source_memory_ids", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="intelligence_graph",
    )


def downgrade() -> None:
    op.drop_table("intelligence_insights", schema="intelligence_graph")
EOF

# Update public env.py to target core_api schema
print_status "Updating public environment configuration..."
cat > alembic/public/env.py << 'EOF'
#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""Alembic migration environment for CORE_API schema (main application)."""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL from environment
database_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")

if not database_url:
    # Build URL from individual components
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "nina")
    password = os.getenv("POSTGRES_PASSWORD", "dev_password_change_in_production")
    database = os.getenv("POSTGRES_DB", "ninaivalaigal_dev")
    database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Import models for autogenerate
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../services/core-api"))
from database.models import Base

# For autogenerate to work, we need the actual metadata
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema="core_api",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version",
            version_table_schema="core_api",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

# Create validation script
print_status "Creating validation script..."
cat > scripts/alembic-validate-single-source.sh << 'EOF'
#!/bin/bash
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Validate single source of truth for Alembic migrations

set -euo pipefail

echo "🔍 Validating single source of truth for Alembic migrations..."
echo

# Check for duplicate table names across schemas
echo "Checking for duplicate table names across schemas..."

# Extract table names from all migration files
temp_dir=$(mktemp -d)
find alembic -name "*.py" -path "*/versions/*" -exec grep -l "create_table" {} \; | while read file; do
    schema=$(echo "$file" | sed 's|alembic/[^/]*/versions/.*|\1|' | sed 's|alembic/||')
    grep "create_table" "$file" -A 1 | grep '"' | sed 's/.*"\([^"]*\)".*/\1/' | while read table; do
        echo "$schema:$table" >> "$temp_dir/tables.txt"
    done
done

# Check for duplicates
if [ -f "$temp_dir/tables.txt" ]; then
    duplicates=$(cut -d: -f2 "$temp_dir/tables.txt" | sort | uniq -d)
    if [ -n "$duplicates" ]; then
        echo "❌ DUPLICATE TABLE NAMES FOUND:"
        for table in $duplicates; do
            echo "   $table:"
            grep ":$table$" "$temp_dir/tables.txt" | sed 's/^/     - /'
        done
        echo
        echo "🚨 This violates single source of truth principle!"
        rm -rf "$temp_dir"
        exit 1
    else
        echo "✅ No duplicate table names found"
    fi
else
    echo "⚠️  No migration files found"
fi

# Check schema consistency
echo
echo "Checking schema consistency..."

# Check if public schema migrations target core_api
public_files=$(find alembic/public/versions -name "*.py" 2>/dev/null || true)
if [ -n "$public_files" ]; then
    schema_usage=$(grep -c "schema=" alembic/public/versions/*.py 2>/dev/null || echo "0")
    if [ "$schema_usage" -gt 0 ]; then
        echo "✅ Public schema migrations use explicit schema targeting"
    else
        echo "⚠️  Public schema migrations should use explicit schema targeting"
    fi
fi

# Clean up
rm -rf "$temp_dir"

echo
echo "✅ Single source of truth validation complete"
EOF

chmod +x scripts/alembic-validate-single-source.sh

# Create documentation
print_status "Creating updated documentation..."
cat > docs/ALEMBIC-SINGLE-SOURCE-OF-TRUTH.md << 'EOF'
# Alembic Single Source of Truth Architecture

**Date:** November 18, 2025  
**Status:** ✅ **ACTIVE - Clean Implementation**

---

## 🎯 **Single Source of Truth Principle**

This architecture ensures **no table duplication** across schemas and **clear ownership** for each data domain.

---

## 📊 **Schema Ownership**

### **core_api Schema** (Main Application)
**Owner**: Python API Service  
**Purpose**: All main application tables  
**Tables**: users, mfa_*, sso_*, security_*, anomaly_*, device_*, risk_*

### **ag_catalog Schema** (GraphOps)
**Owner**: Rust GraphOps Service  
**Purpose**: Apache AGE graph catalog + application tables  
**Tables**: graph_schema_registry, age_*

### **memory Schema** (Memory Service)
**Owner**: Python API Service  
**Purpose**: Memory relationships and data  
**Tables**: memory_relationships, memory_*

### **intelligence_graph Schema** (AI Service)
**Owner**: Python API Service  
**Purpose**: AI insights and intelligence data  
**Tables**: intelligence_insights, intelligence_*

### **Compliance Schemas** (Isolated)
**Owner**: Compliance Service  
**Purpose**: Regulatory compliance data  
**Tables**: gdpr_*, hipaa_*, soc2_*, iso27001_*, incident_*, pentest_*, threat_intelligence

---

## 🔧 **Migration Commands**

### **Core API (Main Application)**
```bash
# Create migration
alembic -c alembic/public/alembic.ini revision --autogenerate -m "description"

# Apply migration
alembic -c alembic/public/alembic.ini upgrade head

# Check status
alembic -c alembic/public/alembic.ini current
```

### **All Schemas**
```bash
# Check all statuses
./scripts/alembic-status-all.sh

# Validate single source of truth
./scripts/alembic-validate-single-source.sh

# Upgrade all schemas
./scripts/alembic-upgrade-all.sh
```

---

## ✅ **Validation Rules**

1. **No Duplicate Tables**: Each table name exists in only one schema
2. **Explicit Schema Targeting**: All create_table calls specify schema
3. **Clear Ownership**: Each schema has a single responsible service
4. **Consistent Naming**: Related tables use appropriate prefixes

---

## 🚨 **Prevention Measures**

### **Automated Validation**
```bash
# Run before committing
./scripts/alembic-validate-single-source.sh

# Pre-commit hook (recommended)
#!/bin/sh
./scripts/alembic-validate-single-source.sh || exit 1
```

### **Development Guidelines**
1. **Always specify schema** in create_table calls
2. **Use descriptive table names** with appropriate prefixes
3. **Check for conflicts** before creating new tables
4. **Run validation** after each migration

---

## 📋 **Migration History**

### **2025-11-18: Single Source of Truth Reset**
- Cleaned up all previous migrations
- Created consistent schema structure
- Established clear ownership boundaries
- Added validation scripts

---

**For technical details, see:** `/alembic/README.md`  
**For validation, see:** `/scripts/alembic-validate-single-source.sh`
EOF

print_status "✅ Clean Alembic setup created successfully!"
echo
print_status "Next steps:"
echo "1. Run: ./scripts/alembic-validate-single-source.sh"
echo "2. Run: ./scripts/alembic-upgrade-all.sh (when ready)"
echo "3. Update models to target core_api schema"
echo
print_warning "Remember to update your SQLAlchemy models to use the core_api schema!"
echo
echo -e "${GREEN}🎉 Single source of truth fix complete!${NC}"
