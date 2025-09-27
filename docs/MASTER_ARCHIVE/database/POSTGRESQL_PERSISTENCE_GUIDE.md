# PostgreSQL Persistence Guide for Ninaivalaigal

## Current Setup Status

✅ **PostgreSQL is Running**: Local PostgreSQL 15.14 instance on port 5432
✅ **Database Exists**: `mem0db` with user `mem0user`
✅ **MCP Configuration**: Updated to use existing PostgreSQL instance
✅ **Persistence**: Data is stored in PostgreSQL, not SQLite

## Database Connection Details

```bash
Host: localhost
Port: 5432
Database: mem0db
User: mem0user
Password: mem0pass
URL: postgresql://mem0user:mem0pass@  # pragma: allowlist secretlocalhost:5432/mem0db
```

## How Persistence Works

### Current Architecture
- **PostgreSQL Service**: Running via Homebrew (`postgresql@15`)
- **Data Storage**: All memories, contexts, users stored in PostgreSQL
- **No Docker**: Using local PostgreSQL installation, not containerized
- **Automatic Startup**: PostgreSQL starts with system boot

### Service Management
```bash
# Check status
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@15

# Stop PostgreSQL
brew services stop postgresql@15

# Restart PostgreSQL
brew services restart postgresql@15

# Check if accepting connections
pg_isready -h localhost -p 5432 -U mem0user -d mem0db
```

## User and Schema Management

### Current Users
- **Application User**: `mem0user` (used by Ninaivalaigal server)
- **Database**: `mem0db` (main application database)

### Creating Additional Users
```sql
-- Connect as superuser
psql -h localhost -p 5432 -d mem0db

-- Create new user for team/organization
CREATE USER team_engineering WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mem0db TO team_engineering;
GRANT USAGE ON SCHEMA public TO team_engineering;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO team_engineering;
```

### Schema Updates
The database schema is managed through:
1. **Main Schema**: `/Users/asrajag/Workspace/mem0/scripts/create-postgresql-schema.sql`
2. **Team Merger Schema**: `/Users/asrajag/Workspace/mem0/scripts/create-team-merger-schema.sql`

## MCP Server Configuration

### VS Code MCP Setup
File: `/Users/asrajag/Workspace/mem0/.vscode/mcp.json`
```json
{
  "mcpServers": {
    "e^m": {
      "command": "/opt/homebrew/anaconda3/bin/python",
      "args": ["/Users/asrajag/Workspace/mem0/server/mcp_server.py"],
      "env": {
        "NINAIVALAIGAL_DATABASE_URL": "postgresql://mem0user:mem0pass@  # pragma: allowlist secretlocalhost:5432/mem0db",
        "NINAIVALAIGAL_JWT_SECRET": "ninaivalaigal-super-secret-jwt-signing-key-min-32-chars-2024",
        "NINAIVALAIGAL_USER_TOKEN": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
      }
    }
  }
}
```

## Data Backup and Recovery

### Manual Backup
```bash
# Create backup
pg_dump -h localhost -p 5432 -U mem0user -d mem0db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
psql -h localhost -p 5432 -U mem0user -d mem0db < backup_file.sql
```

### Automated Backup Script
```bash
#!/bin/bash
# /Users/asrajag/Workspace/mem0/scripts/backup-postgres.sh

BACKUP_DIR="/Users/asrajag/Workspace/mem0/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ninaivalaigal_backup_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"
pg_dump -h localhost -p 5432 -U mem0user -d mem0db > "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Keep only last 10 backups
ls -t "$BACKUP_DIR"/ninaivalaigal_backup_*.sql | tail -n +11 | xargs rm -f
```

## Database Schema Updates (2025-09-13)

### Schema Fixes Applied
Fixed critical schema mismatches between MCP server and database:

```sql
-- Added missing context column for MCP server compatibility
ALTER TABLE memories ADD COLUMN IF NOT EXISTS context VARCHAR(255);
CREATE INDEX IF NOT EXISTS idx_memories_context ON memories(context);

-- Added missing updated_at column with automatic updates
ALTER TABLE memories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Created trigger for automatic updated_at updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_memories_updated_at
BEFORE UPDATE ON memories
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Current Schema Status
✅ All required columns present in memories table
✅ Proper indexing for performance
✅ Automatic timestamp updates via triggers
✅ MCP server compatibility restored

## Troubleshooting

### PostgreSQL Not Running
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running, start it
brew services start postgresql@15

# Check logs if startup fails
tail -f /opt/homebrew/var/log/postgresql@15.log
```

### Connection Issues
```bash
# Test basic connection
pg_isready -h localhost -p 5432

# Test with credentials
psql -h localhost -p 5432 -U mem0user -d mem0db -c "SELECT version();"

# Check if database exists
psql -h localhost -p 5432 -U mem0user -l | grep mem0db
```

### Schema Validation
```bash
# Verify memories table structure
psql -h localhost -p 5432 -U mem0user -d mem0db -c "\d memories"

# Check for required columns
psql -h localhost -p 5432 -U mem0user -d mem0db -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'memories' AND column_name IN ('context', 'updated_at');"
```

### MCP Server Issues
```bash
# Test MCP server directly
cd /Users/asrajag/Workspace/mem0
export MEM0_DATABASE_URL="postgresql://mem0user:mem0pass@  # pragma: allowlist secretlocalhost:5432/mem0db"
export MEM0_JWT_SECRET="FcbdlNhk9AlKmeGjDNVmZK3CK12UZdQRrdaG1i8xesk"
export NINAIVALAIGAL_USER_ID="8"
python server/mcp_server.py
```

## Migration History

### Previous Migration (2025-09-12)
- ✅ Migrated from SQLite to PostgreSQL
- ✅ Created `mem0db` database with `mem0user`
- ✅ All data successfully migrated
- ✅ Server tested and validated

### Current Status
- **Database**: PostgreSQL 15.14 (persistent, local)
- **Data**: All memories and contexts in PostgreSQL
- **Backup**: Regular backups to `/Users/asrajag/Workspace/mem0/backups/`
- **Access**: MCP server connects via `mem0user` credentials

## Future Docker Migration

When Docker certificate issues are resolved, migration to containerized PostgreSQL:

1. **Export Current Data**:
   ```bash
   pg_dump -h localhost -p 5432 -U mem0user -d mem0db > migration_export.sql
   ```

2. **Start Docker PostgreSQL**:
   ```bash
   docker run -d --name ninaivalaigal_postgres \
     -e POSTGRES_DB=ninaivalaigal_db \
     -e POSTGRES_USER=ninaivalaigal_app \
     -e POSTGRES_PASSWORD=ninaivalaigal_secure_password_2024 \
     -p 5432:5432 \
     -v ninaivalaigal_postgres_data:/var/lib/postgresql/data \
     postgres:15
   ```

3. **Import Data**:
   ```bash
   psql -h localhost -p 5432 -U ninaivalaigal_app -d ninaivalaigal_db < migration_export.sql
   ```

4. **Update Configuration**: Change MCP config to use new credentials

## Security Notes

- **Credentials**: Database password is in configuration files (acceptable for local development)
- **JWT Secret**: Used for user authentication tokens
- **Row-Level Security**: Implemented in PostgreSQL for data isolation
- **Backup Security**: Backup files contain sensitive data, store securely

---

**Last Updated**: 2025-09-13T19:20:00-05:00
**PostgreSQL Version**: 15.14 (Homebrew)
**Status**: ✅ Operational and Persistent
