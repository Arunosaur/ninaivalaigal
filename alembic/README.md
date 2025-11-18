# Alembic Single Source of Truth Setup

**Architecture:** Single Source of Truth with Schema Isolation  
**Date:** 2025-11-18  
**Status:** Active - Clean Implementation

---

## Overview

This project uses a **single source of truth Alembic setup** where each database schema has its own isolated migration environment. This prevents cross-contamination, eliminates duplicate tables, and provides clear ownership boundaries.

---

## Directory Structure

```
alembic/
├── README.md                    # This file
├── public/                      # Core API (core_api schema)
│   ├── alembic.ini
│   ├── env.py                   # Targets core_api schema
│   ├── script.py.mako
│   └── versions/
│       └── *.py                 # Migration files

├── graphops/                    # GraphOps service (ag_catalog schema)
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── *.py                 # Migration files

├── memory/                      # Memory schema
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── *.py                 # Migration files

└── intelligence/                # Intelligence graph schema
    ├── alembic.ini
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── *.py                 # Migration files
```

---

## Schema Mapping

| Schema | Environment | Purpose | Service Owner | Status |
|--------|-------------|---------|---------------|--------|
| `core_api` | `alembic/public/` | Main application tables | Python API | Clean |
| `ag_catalog` | `alembic/graphops/` | Apache AGE graph catalog | Rust GraphOps | Clean |
| `memory` | `alembic/memory/` | Memory graph relationships | Python API | Clean |
| `intelligence_graph` | `alembic/intelligence/` | Graph intelligence data | Python API | Clean |

---

## Single Source of Truth Rules

### No Duplicate Tables
- Each table name exists in only ONE schema
- Validation script prevents duplicates
- Clear ownership boundaries

### Explicit Schema Targeting
- All `create_table` calls specify `schema`
- No ambiguous table creation
- Consistent naming conventions

### Clear Ownership
- Each schema has one responsible service
- No cross-schema table duplication
- Independent version tracking

---

## Usage

### Per-Schema Commands

Each schema has independent Alembic commands:

```bash
# Public schema (main application)
alembic -c alembic/public/alembic.ini revision --autogenerate -m "description"
alembic -c alembic/public/alembic.ini upgrade head
alembic -c alembic/public/alembic.ini current
alembic -c alembic/public/alembic.ini history

# GraphOps schema (ag_catalog)
alembic -c alembic/graphops/alembic.ini revision --autogenerate -m "description"
alembic -c alembic/graphops/alembic.ini upgrade head
alembic -c alembic/graphops/alembic.ini current

# Memory schema
alembic -c alembic/memory/alembic.ini revision --autogenerate -m "description"
alembic -c alembic/memory/alembic.ini upgrade head
alembic -c alembic/memory/alembic.ini current

# Intelligence schema
alembic -c alembic/intelligence/alembic.ini revision --autogenerate -m "description"
alembic -c alembic/intelligence/alembic.ini upgrade head
alembic -c alembic/intelligence/alembic.ini current
```

### Master Commands (All Schemas)

```bash
# Check status of all schemas
./scripts/alembic-status-all.sh

# Verify all schemas are healthy
./scripts/alembic-verify-all.sh

# Reset all schemas (nuclear option - use with caution!)
./scripts/alembic-reset-all.sh
```

---

## Benefits

### ✅ **Full Isolation**
- Each schema evolves independently
- No cross-contamination of revision history
- Clear ownership boundaries

### ✅ **No "Multiple Heads" Conflicts**
- Each schema has its own version tracking
- No conflicts between service migrations
- Easy to stamp/reset per schema

### ✅ **Easy Rollback Granularity**
- Rollback one schema without affecting others
- Per-service deployment independence
- Microservice-friendly architecture

### ✅ **Works with Multiple Services**
- Python API manages: public, memory, intelligence
- Rust GraphOps manages: ag_catalog
- Future services can add their own schemas

---

## Adding a New Schema

To add a new schema to the multi-environment setup:

```bash
# 1. Create environment directory
mkdir -p alembic/new_schema/versions

# 2. Copy template files
cp alembic/public/alembic.ini alembic/new_schema/
cp alembic/public/env.py alembic/new_schema/
cp alembic/public/script.py.mako alembic/new_schema/

# 3. Edit alembic/new_schema/env.py
# Update version_table_schema = "new_schema"
# Update target_metadata to point to your models

# 4. Generate base migration
alembic -c alembic/new_schema/alembic.ini revision --autogenerate -m "0001_base"

# 5. Create version table in database
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "
CREATE TABLE IF NOT EXISTS new_schema.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);"

# 6. Stamp database
alembic -c alembic/new_schema/alembic.ini stamp head
```

---

## Troubleshooting

### "Multiple heads" error

This should not happen with the multi-environment setup. If it does:

1. Check which environment has the issue:
   ```bash
   ./scripts/alembic-status-all.sh
   ```

2. Fix the specific environment:
   ```bash
   alembic -c alembic/<schema>/alembic.ini heads
   alembic -c alembic/<schema>/alembic.ini merge <rev1> <rev2> -m "merge heads"
   ```

### Version table not found

Create the version table for the schema:

```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "
CREATE TABLE IF NOT EXISTS <schema>.alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);"
```

### Wrong version tracked

Manually update the version:

```bash
container exec ninaivalaigal-dev-db psql -U nina -d ninaivalaigal_dev -c "
UPDATE <schema>.alembic_version SET version_num = '<correct_version>';"
```

---

## Documentation

- **Architecture:** `/docs/ALEMBIC-MULTI-ENV-ARCHITECTURE.md`
- **Reset Script:** `/scripts/alembic-reset-all.sh`
- **Status Script:** `/scripts/alembic-status-all.sh`
- **Verification Script:** `/scripts/alembic-verify-all.sh`

---

## Migration History

### 2025-11-06: Multi-Environment Setup
- Migrated from single-environment to multi-environment setup
- Created separate environments for: public, graphops, memory, intelligence
- Fixed "multiple heads" issue
- Archived old migration structure

---

**For more information, see:** `/docs/ALEMBIC-MULTI-ENV-ARCHITECTURE.md`
