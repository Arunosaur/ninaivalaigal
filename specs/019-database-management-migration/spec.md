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

#### 1.1 Core Database Components
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

### 3. pgvector Extension Management

#### 3.1 Vector Extension Setup
```sql
-- Extension installation (in migration)
CREATE EXTENSION IF NOT EXISTS vector;

-- Vector column definition
ALTER TABLE memories ADD COLUMN embedding vector(1536);

-- Vector index creation
CREATE INDEX memories_embedding_idx ON memories 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

#### 3.2 Vector Operations
```python
# Vector similarity search
from pgvector.sqlalchemy import Vector
from sqlalchemy import text

class Memory(Base):
    __tablename__ = "memories"
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))  # OpenAI embedding dimension
    
    @classmethod
    def find_similar(cls, session, query_embedding, limit=10):
        """Find memories similar to query embedding"""
        return session.query(cls).order_by(
            cls.embedding.cosine_distance(query_embedding)
        ).limit(limit).all()
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
