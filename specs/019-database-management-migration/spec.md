# SPEC-019: Database Management & Migration

## Overview

This specification defines the comprehensive database management and migration system for ninaivalaigal, providing automated schema migrations, backup/restore capabilities, pgvector integration, and production-ready database operations.

## Motivation

- **Schema Evolution**: Automated database schema migrations with version control
- **Data Safety**: Comprehensive backup and restore capabilities with verification
- **Vector Search**: pgvector extension management for AI/ML memory features
- **Production Operations**: Database maintenance, monitoring, and optimization
- **Development Support**: Database seeding, testing, and reset capabilities

## Specification

### 1. Database Architecture

#### 1.1 Schema Namespace Strategy

**FOUNDATIONAL PRINCIPLE**: One canonical table per logical domain, one authoritative migration chain per schema.

```
ninaivalaigal_dev (database)
├── public schema      → Core identity & cross-domain entities
│   ├── users          → User accounts
│   ├── teams          → Team entities
│   ├── organizations  → Organization entities
│   └── memories (VIEW)→ Backward compatibility view (DEPRECATED)
│
├── memory schema      → Memory domain (owned by Memory Service)
│   ├── memory_records → Canonical memory storage with pgvector
│   └── memory_tags    → Memory tagging system
│
├── graph schema       → Graph intelligence (future)
│   └── (planned)
│
├── billing schema     → Financial records (future)
│   └── (planned)
│
└── admin schema       → System monitoring (future)
    └── (planned)
```

**Schema Ownership & Responsibility**:

| Schema | Owner Service | Purpose | Write Access | Read Access |
|--------|--------------|---------|--------------|-------------|
| `public` | Core API (Python) | Global identity model | Core API | All services |
| `memory` | Memory Service (Rust) | Memory persistence & AI operations | Memory Service | All services |
| `graph` | Graph Service (Rust) | Knowledge graph & intelligence | Graph Service | All services |
| `billing` | Business Service (Python) | Financial & usage tracking | Business Service | Admin/Business |
| `admin` | Admin Service | System monitoring & audit | Admin Service | Admin only |

**Why Schema Separation?**
1. **Logical Ownership**: Each domain team owns their schema
2. **Migration Control**: Independent migration chains prevent conflicts
3. **Security Boundaries**: Row-Level Security per schema
4. **Performance**: Schema-level partitioning and optimization
5. **Scalability**: Future multi-database sharding by schema

#### 1.2 Core Database Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Alembic       │    │   pgvector      │
│   15.x          │◄───│   Migrations    │    │   Extension     │
│   (Primary DB)  │    │   (Schema Mgmt) │    │   (Vector Ops)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Connection    │    │   Version       │    │   Memory        │
│   Pooling       │    │   Control       │    │   Embeddings    │
│   (PgBouncer)   │    │   (Git-based)   │    │   (Vector Ops)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### 1.2 Database Configuration
```yaml
PostgreSQL Configuration:
  Version: 15.x (latest stable)
  Extensions:
    - pgvector: Vector similarity search
    - uuid-ossp: UUID generation
    - pg_stat_statements: Query performance monitoring

Connection Settings:
  Host: localhost (development) / cloud endpoint (production)
  Port: 5433 (development) / 5432 (production)
  Database: nina
  User: nina
  SSL: Required in production
```

### 2. Alembic Migration System

#### 2.1 Migration Framework
```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from server.database import Base

# Import all models to ensure they're registered
from server.database import User, Team, Memory, Context, TeamMember

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

#### 2.2 Migration Directory Structure
```
alembic/
├── env.py                    # Alembic environment configuration
├── script.py.mako           # Migration template
├── alembic.ini              # Alembic configuration
└── versions/
    ├── 001_initial_schema.py
    ├── 002_add_teams.py
    ├── 003_add_pgvector.py
    ├── 004_add_contexts.py
    └── 005_add_rbac.py
```

#### 2.3 Migration Commands
```bash
# Generate new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Show migration history
alembic history

# Show current revision
alembic current
```

#### 2.4 Migration Best Practices

**Migration Discipline**:
1. **Single Responsibility**: Each migration has ONE clear purpose (schema, indexes, data, or view)
2. **Sequential Numbering**: Strictly follow `down_revision` chain (0001 → 0002 → 0003)
3. **Never Modify Applied**: Always add incremental `+update_*` files, never edit applied migrations
4. **Fully Qualified Names**: Cross-schema references must use `schema.table` notation
5. **Comprehensive Docstrings**: Document breaking changes, purpose, and architectural decisions

**Example Migration Structure**:
```
alembic/versions/
├── 0001_extensions.py              ← Enable pgvector, uuid-ossp
├── 0002_apache_age_graph.py        ← Graph database setup
├── 0003_core_tables.py             ← Create public.users, teams, orgs
├── 0124_create_memory_schema.py    ← Create memory schema & tables
├── 0125_add_memory_indexes.py      ← Add performance indexes
└── 0126_create_memory_views.py     ← Add backward compatibility views
```

**Cross-Schema Foreign Key Pattern**:
```python
# ✅ CORRECT - Fully qualified
op.execute("""
    CREATE TABLE memory.memory_records (
        user_id UUID REFERENCES public.users(id) ON DELETE CASCADE
    );
""")

# ❌ WRONG - Ambiguous
op.execute("""
    CREATE TABLE memory_records (
        user_id UUID REFERENCES users(id)
    );
""")
```

### 3. pgvector Extension Management

#### 3.1 Vector Extension Setup
```sql
-- Extension installation (in migration 0001_extensions.py)
CREATE EXTENSION IF NOT EXISTS vector;

-- Vector column definition (in migration 0124_create_memory_schema.py)
CREATE TABLE memory.memory_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id),
    text TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small / ada-002
    created_at TIMESTAMPTZ DEFAULT now()
);

-- HNSW index for fast similarity search (preferred over IVFFlat)
CREATE INDEX idx_memory_records_embedding ON memory.memory_records
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- GIN index for JSONB metadata queries
CREATE INDEX idx_memory_records_metadata ON memory.memory_records
USING gin (metadata);
```

**Index Performance Characteristics**:

| Index Type | Build Time | Query Speed | Accuracy | Best For |
|------------|-----------|-------------|----------|----------|
| HNSW | Medium | Very Fast | High (99%) | Most use cases, <10M vectors |
| IVFFlat | Fast | Fast | Good (95%) | Large datasets >10M vectors |
| Exact | Instant | Slow | Perfect (100%) | Small datasets <100K vectors |

**Recommendation**: Use HNSW for ninaivalaigal (expected dataset: <5M vectors)

#### 3.2 Vector Operations in Rust (Memory Service)
```rust
// Vector similarity search (Rust - Memory Service)
use sqlx::query_as;

#[derive(Debug, sqlx::FromRow)]
struct MemoryWithSimilarity {
    id: Uuid,
    text: String,
    similarity: f64,
}

async fn find_similar_memories(
    pool: &PgPool,
    user_id: Uuid,
    query_embedding: Vec<f32>,
    limit: i64,
) -> Result<Vec<MemoryWithSimilarity>> {
    sqlx::query_as!(
        MemoryWithSimilarity,
        r#"
        SELECT
            id,
            text,
            1 - (embedding <=> $1::vector) as similarity
        FROM memory.memory_records
        WHERE user_id = $2
        ORDER BY embedding <=> $1::vector
        LIMIT $3
        "#,
        query_embedding,
        user_id,
        limit
    )
    .fetch_all(pool)
    .await
}
```

#### 3.3 Vector Operations in Python (Legacy - Core API)
```python
# Vector similarity search (Python - via view for backward compatibility)
from pgvector.sqlalchemy import Vector
from sqlalchemy import text

class Memory(Base):
    __tablename__ = "memories"  # This is a VIEW → memory.memory_records
    __table_args__ = {"schema": "public"}

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False)
    data = Column(Text, nullable=False)  # Maps to 'text' column
    metadata = Column(JSONB)
    # Note: embedding not exposed in view (Rust owns embedding writes)

    @classmethod
    def find_similar(cls, session, user_id, query_embedding, limit=10):
        """
        Find memories similar to query embedding.
        NOTE: This queries the canonical memory.memory_records table directly,
        not the view, for vector operations.
        """
        result = session.execute(text("""
            SELECT id, text, metadata,
                   1 - (embedding <=> :embedding::vector) as similarity
            FROM memory.memory_records
            WHERE user_id = :user_id
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """), {
            "embedding": str(query_embedding),
            "user_id": user_id,
            "limit": limit
        })
        return result.fetchall()
```

#### 3.3 Vector Index Management
```python
# Index optimization
def optimize_vector_indexes(session):
    """Optimize vector indexes for better performance"""
    session.execute(text("REINDEX INDEX memories_embedding_idx;"))
    session.execute(text("ANALYZE memories;"))
```

### 4. Backup and Restore System

#### 4.1 Backup Strategy
```yaml
Backup Types:
  - Full Backup: Complete database dump with schema and data
  - Schema Only: Structure without data (for testing)
  - Data Only: Data without structure (for migrations)
  - Incremental: WAL-based continuous backup (production)

Backup Schedule:
  - Development: On-demand via make backup
  - Staging: Daily at 2 AM UTC
  - Production: Continuous WAL + daily full backup

Retention Policy:
  - Development: 7 days
  - Staging: 30 days
  - Production: 90 days + yearly archives
```

#### 4.2 Backup Implementation
```bash
#!/bin/bash
# scripts/backup-database.sh

set -euo pipefail

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Create database backup
pg_dump \
  --host=localhost \
  --port=5433 \
  --username=nina \
  --dbname=nina \
  --verbose \
  --clean \
  --if-exists \
  --create \
  --format=custom \
  --file="${BACKUP_FILE}.custom"

# Create SQL backup for readability
pg_dump \
  --host=localhost \
  --port=5433 \
  --username=nina \
  --dbname=nina \
  --verbose \
  --clean \
  --if-exists \
  --create \
  --file="${BACKUP_FILE}"

# Compress backups
gzip "${BACKUP_FILE}"

echo "✅ Backup created: ${BACKUP_FILE}.gz"
echo "✅ Custom backup: ${BACKUP_FILE}.custom"
```

#### 4.3 Restore Implementation
```bash
#!/bin/bash
# scripts/restore-database.sh

set -euo pipefail

BACKUP_FILE="$1"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop API server to prevent connections
echo "🛑 Stopping API server..."
make api-stop || true

# Drop existing connections
psql -h localhost -p 5433 -U nina -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'nina' AND pid <> pg_backend_pid();"

# Restore from backup
if [[ "$BACKUP_FILE" == *.custom ]]; then
    # Custom format restore
    pg_restore \
      --host=localhost \
      --port=5433 \
      --username=nina \
      --dbname=nina \
      --verbose \
      --clean \
      --if-exists \
      --create \
      "$BACKUP_FILE"
else
    # SQL format restore
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        gunzip -c "$BACKUP_FILE" | psql -h localhost -p 5433 -U nina
    else
        psql -h localhost -p 5433 -U nina -f "$BACKUP_FILE"
    fi
fi

echo "✅ Database restored from: $BACKUP_FILE"
```

### 5. Database Initialization and Seeding

#### 5.1 Database Setup Script
```python
# scripts/setup-database.py
import asyncio
from sqlalchemy import create_engine
from server.database import Base, DatabaseManager
from server.config import get_database_url

async def setup_database():
    """Initialize database with schema and extensions"""

    # Create database engine
    engine = create_engine(get_database_url())

    # Create all tables
    Base.metadata.create_all(engine)

    # Initialize database manager
    db_manager = DatabaseManager()

    # Create extensions
    await db_manager.execute_sql("""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """)

    print("✅ Database initialized successfully")

if __name__ == "__main__":
    asyncio.run(setup_database())
```

#### 5.2 Test Data Seeding
```python
# scripts/seed-test-data.py
import asyncio
from server.database import DatabaseManager, User, Team, Memory

async def seed_test_data():
    """Seed database with test data for development"""

    db_manager = DatabaseManager()

    # Create test users
    test_users = [
        {"username": "alice", "email": "alice@example.com"},
        {"username": "bob", "email": "bob@example.com"},
        {"username": "charlie", "email": "charlie@example.com"}
    ]

    for user_data in test_users:
        user = await db_manager.create_user(**user_data)
        print(f"✅ Created user: {user.username}")

    # Create test teams
    team = await db_manager.create_team(
        name="Test Team",
        description="Test team for development"
    )
    print(f"✅ Created team: {team.name}")

    # Create test memories
    memories = [
        "Remember to implement user authentication",
        "Database migration system is working well",
        "Need to add vector search capabilities"
    ]

    for content in memories:
        memory = await db_manager.create_memory(
            user_id=1,
            content=content
        )
        print(f"✅ Created memory: {memory.id}")

if __name__ == "__main__":
    asyncio.run(seed_test_data())
```

### 6. Database Monitoring and Maintenance

#### 6.1 Performance Monitoring
```sql
-- Query performance monitoring
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Connection monitoring
SELECT
    state,
    count(*) as connections
FROM pg_stat_activity
WHERE datname = 'nina'
GROUP BY state;

-- Database size monitoring
SELECT
    pg_size_pretty(pg_database_size('nina')) as database_size,
    pg_size_pretty(pg_total_relation_size('memories')) as memories_table_size;
```

#### 6.2 Maintenance Scripts
```bash
#!/bin/bash
# scripts/database-maintenance.sh

set -euo pipefail

echo "🔧 Starting database maintenance..."

# Update table statistics
psql -h localhost -p 5433 -U nina -d nina -c "ANALYZE;"

# Vacuum tables
psql -h localhost -p 5433 -U nina -d nina -c "VACUUM ANALYZE;"

# Reindex vector indexes
psql -h localhost -p 5433 -U nina -d nina -c "REINDEX INDEX memories_embedding_idx;"

# Check for bloat
psql -h localhost -p 5433 -U nina -d nina -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

echo "✅ Database maintenance completed"
```

### 7. Makefile Integration

#### 7.1 Database Management Commands
```makefile
# Database lifecycle
db-init:        # Initialize database schema
db-migrate:     # Run pending migrations
db-rollback:    # Rollback last migration
db-reset:       # Reset database (drop + recreate)
db-seed:        # Seed with test data

# Backup and restore
backup:         # Create database backup
restore:        # Restore from backup (interactive)
list-backups:   # List available backups
cleanup-backups: # Clean old backup files

# Maintenance
db-vacuum:      # Vacuum and analyze tables
db-reindex:     # Rebuild indexes
db-stats:       # Show database statistics
db-maintenance: # Full maintenance routine
```

#### 7.2 Implementation Examples
```makefile
db-migrate:
	@echo "🔄 Running database migrations..."
	@alembic upgrade head
	@echo "✅ Migrations completed"

backup:
	@echo "💾 Creating database backup..."
	@./scripts/backup-database.sh
	@echo "✅ Backup completed"

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		make db-stop || true; \
		make db-start; \
		alembic upgrade head; \
		echo "✅ Database reset completed"; \
	else \
		echo "❌ Database reset cancelled"; \
	fi
```

## Testing Strategy

### 1. Migration Testing
```python
# Test migration up and down
def test_migration_cycle():
    # Apply migration
    alembic.command.upgrade(alembic_cfg, "head")

    # Verify schema changes
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "memories" in tables

    # Test rollback
    alembic.command.downgrade(alembic_cfg, "-1")
```

### 2. Backup/Restore Testing
```bash
#!/bin/bash
# Test backup and restore cycle
make backup
BACKUP_FILE=$(ls -t backups/*.sql.gz | head -1)
make db-reset
./scripts/restore-database.sh "$BACKUP_FILE"
make health  # Verify restoration
```

### 3. Vector Operations Testing
```python
def test_vector_operations():
    # Test vector insertion
    memory = Memory(
        content="Test memory",
        embedding=[0.1] * 1536
    )
    session.add(memory)
    session.commit()

    # Test similarity search
    similar = Memory.find_similar(session, [0.1] * 1536, limit=5)
    assert len(similar) > 0
```

## Security Considerations

### 1. Database Security
```yaml
Security Measures:
  - SSL/TLS encryption for connections
  - Strong password policies
  - Limited database user privileges
  - Connection pooling with authentication
  - Backup encryption (production)
```

### 2. Migration Security
```yaml
Migration Safety:
  - Code review for all migrations
  - Staging environment testing
  - Rollback procedures tested
  - Data validation after migrations
  - Backup before major schema changes
```

## Success Criteria

### 1. Functional Requirements
- ✅ Migrations run successfully up and down
- ✅ Backups create and restore correctly
- ✅ pgvector operations work properly
- ✅ Database maintenance scripts function
- ✅ Performance monitoring provides insights

### 2. Operational Requirements
- ✅ Zero-downtime migrations (production)
- ✅ Backup/restore time < 5 minutes (development)
- ✅ Migration time < 30 seconds (typical)
- ✅ Database startup time < 10 seconds

### 3. Data Integrity Requirements
- ✅ No data loss during migrations
- ✅ Backup verification passes
- ✅ Foreign key constraints maintained
- ✅ Vector indexes remain consistent

## Future Enhancements

1. **Read Replicas**: Database read scaling with replica management
2. **Sharding**: Horizontal scaling for large datasets
3. **Point-in-Time Recovery**: WAL-based recovery capabilities
4. **Automated Failover**: High availability with automatic failover
5. **Performance Tuning**: Automated query optimization and index recommendations
6. **Data Archival**: Automated archival of old data

## Dependencies

- PostgreSQL 15.x (database server)
- Alembic (migration framework)
- pgvector (vector extension)
- SQLAlchemy (ORM)
- psycopg2 (PostgreSQL adapter)
- pg_dump/pg_restore (backup tools)

This specification ensures ninaivalaigal has enterprise-grade database management capabilities with proper migration control, backup safety, and production-ready operations.
