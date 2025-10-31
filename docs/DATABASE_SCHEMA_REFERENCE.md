# Database Schema Reference

**Version**: 1.0
**Last Updated**: 2025-10-31
**Migration**: 0124_create_memory_schema_and_tables

---

## 🏗️ Schema Architecture

Ninaivalaigal uses PostgreSQL schema namespaces for logical separation and ownership delegation:

```
ninaivalaigal_dev (database)
├── public schema      → Core identity & cross-domain entities
├── memory schema      → Memory persistence (owned by Memory Service)
├── graph schema       → Graph intelligence (future - owned by Graph Service)
├── billing schema     → Financial records (future - owned by Business Service)
└── admin schema       → System monitoring (future - owned by Admin Service)
```

---

## 📊 Schema Details

### **`public` Schema** - Core Identity

**Owner**: Core API (Python)
**Purpose**: Global identity model (users, teams, organizations)

| Table | Description | Key Columns |
|-------|-------------|-------------|
| `users` | User accounts | `id`, `email`, `password_hash`, `account_type` |
| `teams` | Team entities | `id`, `name`, `owner_id` |
| `organizations` | Organization entities | `id`, `name`, `domain` |
| `team_memberships` | User-team relationships | `user_id`, `team_id`, `role` |
| `contexts` | Memory contexts | `id`, `name`, `user_id`, `team_id` |

**Why public?**
- Referenced by every domain (memory, billing, graph, analytics)
- Migrated early (created before other schemas)
- Low churn (few schema changes)
- Universally required for joins

---

### **`memory` Schema** - Memory Persistence

**Owner**: Memory Service (Rust)
**Purpose**: Anything related to storage, retrieval, and AI operations on memories

| Table | Description | Canonical? |
|-------|-------------|------------|
| **`memory_records`** | **Single source of truth for all memory data** | ✅ **YES** |
| `memory_tags` | Tags associated with memories | No |

#### **`memory.memory_records`** - Canonical Memory Table

```sql
CREATE TABLE memory.memory_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Cross-schema foreign keys (fully qualified)
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
    org_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,

    -- Scope control
    scope TEXT CHECK (scope IN ('personal','team','organization')) NOT NULL,

    -- Memory classification
    kind TEXT NOT NULL,  -- e.g., 'note', 'image', 'file_context', 'conversation'

    -- Memory content
    text TEXT NOT NULL,

    -- Flexible metadata (tags, source, context, etc.)
    metadata JSONB DEFAULT '{}'::jsonb,

    -- pgvector embedding for semantic search (OpenAI 1536-dim)
    embedding VECTOR(1536),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

**Indexes:**
- `idx_memory_records_user_id` - Filter by user
- `idx_memory_records_team_id` - Filter by team (partial index)
- `idx_memory_records_org_id` - Filter by org (partial index)
- `idx_memory_records_scope_kind` - Composite for scope + kind queries
- `idx_memory_records_created_at` - Time-based sorting
- `idx_memory_records_embedding` - HNSW vector similarity search
- `idx_memory_records_metadata` - GIN index for JSONB queries

**Performance Targets:**
- Insert: <5ms P95
- Lookup by ID: <2ms P95
- Vector similarity search (k=10): <50ms P95
- Metadata filter queries: <20ms P95

---

#### **`memory.memory_tags`** - Memory Tagging

```sql
CREATE TABLE memory.memory_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID NOT NULL REFERENCES memory.memory_records(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(memory_id, tag)
);
```

**Purpose**: Allow memories to be tagged with multiple labels for categorization.

**Indexes:**
- `idx_memory_tags_memory_id` - Reverse lookup (find tags for memory)
- `idx_memory_tags_tag` - Find all memories with a specific tag

---

## 🔄 Backward Compatibility

### **`public.memories`** - Compatibility View (DEPRECATED)

```sql
CREATE VIEW public.memories AS
SELECT
    id,
    user_id,
    text AS data,
    metadata,
    created_at,
    updated_at
FROM memory.memory_records;
```

**Purpose**: Allows legacy Python ORM code to continue working without changes.

**Status**: ⚠️ **DEPRECATED** - Do not use in new code. Migrate to `memory.memory_records`.

**Migration Path**:
1. Old code queries `public.memories` → works via view
2. New Rust code writes to `memory.memory_records` → canonical
3. Gradually migrate Python code to use `memory.memory_records`
4. Eventually drop the view (target: Q1 2026)

---

## 🎯 Service Responsibility Matrix

| Service | Role | Table/Schema | Write? | Read? |
|---------|------|--------------|--------|-------|
| **Rust Memory Service** | CRUD + embedding write | `memory.memory_records` | ✅ | ✅ |
| **Python Core API** | Legacy routing + proxy | `public.memories` (view) | ❌ | ✅ |
| **Graph Service** | Vector search, similarity | `memory.memory_records` | ❌ | ✅ |
| **Business/Admin** | Analytics, quotas | joins `users` + `memory.memory_records` | ❌ | ✅ |

**Notes:**
- ✅ **Rust writes** → High-throughput inserts/updates to canonical table
- ❌ **Python reads** → Legacy compatibility via view (read-only)
- 🔍 **Graph reads** → Semantic search using embeddings + metadata

---

## 🔗 Cross-Schema Foreign Keys

All foreign keys from `memory` schema tables **must be fully qualified**:

```sql
-- ✅ CORRECT
user_id UUID REFERENCES public.users(id)
team_id UUID REFERENCES public.teams(id)

-- ❌ WRONG (ambiguous)
user_id UUID REFERENCES users(id)
```

This ensures:
- Referential integrity across schemas
- Clear ownership boundaries
- Database normalization maintained

---

## 🧪 Testing Strategy

### Schema Verification
```bash
# Verify memory schema exists
psql -c "\dn"

# List tables in memory schema
psql -c "\dt memory.*"

# Verify view exists
psql -c "\dv public.memories"

# Check foreign keys
psql -c "\d memory.memory_records"
```

### Data Migration Verification
```sql
-- Count records migrated
SELECT COUNT(*) FROM memory.memory_records;

-- Verify no data loss
SELECT COUNT(*) FROM public.memories;  -- Should match via view

-- Check embedding dimensions
SELECT vector_dims(embedding) FROM memory.memory_records LIMIT 1;  -- Should be 1536
```

---

## 📈 Future Schema Evolution

### Planned Additions

1. **`graph` schema** (SPEC-094)
   - `graph_nodes` - Knowledge graph nodes
   - `graph_edges` - Relationships between nodes
   - `graph_metrics` - Analytics on graph structure

2. **`billing` schema** (SPEC-025)
   - `invoices` - Financial records
   - `usage_stats` - Resource consumption tracking
   - `subscription_plans` - Pricing tiers

3. **`admin` schema**
   - `system_logs` - Audit trail
   - `health_checks` - Service monitoring
   - `rate_limits` - API throttling state

### Migration Best Practices

1. **Each schema has its own Alembic namespace** (future)
2. **Never modify applied migrations** - always add incremental updates
3. **Every file has a single responsibility** (schema, indexes, data, view)
4. **Fully qualify cross-schema references**
5. **Document breaking changes in migration docstring**

---

## 🔍 Querying Examples

### Rust (Canonical Access)
```rust
// Direct access to canonical table
let memories = sqlx::query_as!(
    Memory,
    "SELECT * FROM memory.memory_records WHERE user_id = $1",
    user_id
)
.fetch_all(&pool)
.await?;
```

### Python (Legacy via View)
```python
# Old ORM code still works
from server.db.models import Memory

memories = db.query(Memory).filter_by(user_id=user_id).all()
# This queries public.memories view, which reads from memory.memory_records
```

### Graph Service (Semantic Search)
```rust
// Vector similarity search
let similar = sqlx::query!(
    "SELECT id, text, 1 - (embedding <=> $1) as similarity
     FROM memory.memory_records
     WHERE user_id = $2
     ORDER BY embedding <=> $1
     LIMIT 10",
    query_embedding,
    user_id
)
.fetch_all(&pool)
.await?;
```

---

## ⚠️ Important Notes

1. **`memory.memory_records` is the ONLY canonical memory table**
   - Do not create alternative memory tables
   - All services must read/write this table

2. **`public.memories` is a VIEW, not a table**
   - Cannot write directly to it
   - Deprecated for new code
   - Will be removed in future versions

3. **Always use fully-qualified table names in cross-schema queries**
   ```sql
   -- ✅ Good
   SELECT * FROM memory.memory_records
   JOIN public.users ON memory.memory_records.user_id = public.users.id

   -- ❌ Bad (ambiguous)
   SELECT * FROM memory_records
   JOIN users ON memory_records.user_id = users.id
   ```

4. **pgvector embeddings are 1536 dimensions**
   - Matches OpenAI text-embedding-3-small
   - Matches OpenAI ada-002
   - If using different model, update vector dimension

---

## 📚 References

- **SPEC-019**: Database Management & Migration
- **SPEC-093**: Memory Service (Rust) - CRUD Implementation
- **SPEC-020**: Memory Provider Architecture
- **Migration 0124**: `0124_create_memory_schema_and_tables.py`
- **pgvector docs**: https://github.com/pgvector/pgvector

---

**Maintained by**: Database Team
**Questions**: #database-architecture on Slack
