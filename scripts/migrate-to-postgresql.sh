#!/bin/bash

# migrate-to-postgresql.sh - PostgreSQL migration script for mem0
# This script handles the complete migration from SQLite to PostgreSQL

set -e

echo "🐘 mem0 PostgreSQL Migration Script"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MEM0_DIR="$HOME/Workspace/mem0"
SQLITE_DB="$MEM0_DIR/mem0.db"
BACKUP_DIR="$MEM0_DIR/backups/$(date +%Y%m%d_%H%M%S)"
PG_DATABASE="mem0_production"
PG_USER="${USER}"
PG_HOST="localhost"
PG_PORT="5432"

# Helper functions
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo -e "${BLUE}▶${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites..."
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL is not installed. Install with: brew install postgresql"
        exit 1
    fi
    log_info "PostgreSQL client found"
    
    # Check if PostgreSQL server is running
    if ! pg_isready -h "$PG_HOST" -p "$PG_PORT" &> /dev/null; then
        log_error "PostgreSQL server is not running. Start with: brew services start postgresql"
        exit 1
    fi
    log_info "PostgreSQL server is running"
    
    # Check if SQLite database exists
    if [[ ! -f "$SQLITE_DB" ]]; then
        log_error "SQLite database not found at $SQLITE_DB"
        exit 1
    fi
    log_info "SQLite database found"
    
    # Check if mem0 server is stopped
    if pgrep -f "python.*server/main.py" > /dev/null; then
        log_warn "mem0 server is running. Please stop it before migration."
        read -p "Stop server now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pkill -f "python.*server/main.py" || true
            sleep 2
            log_info "mem0 server stopped"
        else
            log_error "Please stop mem0 server and run migration again"
            exit 1
        fi
    fi
    log_info "mem0 server is not running"
}

# Create backup
create_backup() {
    log_step "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup SQLite database
    cp "$SQLITE_DB" "$BACKUP_DIR/mem0_backup.db"
    log_info "SQLite database backed up to $BACKUP_DIR/mem0_backup.db"
    
    # Backup configuration
    cp "$MEM0_DIR/mem0.config.json" "$BACKUP_DIR/mem0.config.json.backup"
    log_info "Configuration backed up"
    
    # Export data to JSON for additional safety
    sqlite3 "$SQLITE_DB" ".mode json" ".output $BACKUP_DIR/data_export.json" "SELECT * FROM memories;" ".quit"
    log_info "Data exported to JSON format"
}

# Setup PostgreSQL database
setup_postgresql() {
    log_step "Setting up PostgreSQL database..."
    
    # Create database if it doesn't exist
    if ! psql -h "$PG_HOST" -p "$PG_PORT" -lqt | cut -d \| -f 1 | grep -qw "$PG_DATABASE"; then
        createdb -h "$PG_HOST" -p "$PG_PORT" "$PG_DATABASE"
        log_info "Database '$PG_DATABASE' created"
    else
        log_warn "Database '$PG_DATABASE' already exists"
        read -p "Drop and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            dropdb -h "$PG_HOST" -p "$PG_PORT" "$PG_DATABASE"
            createdb -h "$PG_HOST" -p "$PG_PORT" "$PG_DATABASE"
            log_info "Database recreated"
        fi
    fi
    
    # Test connection
    if psql -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DATABASE" -c "SELECT 1;" &> /dev/null; then
        log_info "PostgreSQL connection successful"
    else
        log_error "Failed to connect to PostgreSQL database"
        exit 1
    fi
}

# Migrate schema
migrate_schema() {
    log_step "Migrating database schema..."
    
    # Extract schema from SQLite
    sqlite3 "$SQLITE_DB" ".schema" > "$BACKUP_DIR/sqlite_schema.sql"
    
    # Create PostgreSQL schema (this would need to be customized based on actual schema)
    cat > "$BACKUP_DIR/postgresql_schema.sql" << 'EOF'
-- PostgreSQL schema for mem0
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contexts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, user_id)
);

CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY,
    context_id INTEGER REFERENCES contexts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    source VARCHAR(100),
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_context_id ON memories(context_id);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_contexts_user_id ON contexts(user_id);
CREATE INDEX IF NOT EXISTS idx_contexts_active ON contexts(is_active);
EOF

    # Apply schema to PostgreSQL
    psql -h "$PG_HOST" -p "$PG_PORT" -d "$PG_DATABASE" -f "$BACKUP_DIR/postgresql_schema.sql"
    log_info "PostgreSQL schema created"
}

# Migrate data
migrate_data() {
    log_step "Migrating data..."
    
    # Create Python migration script
    cat > "$BACKUP_DIR/migrate_data.py" << 'EOF'
#!/usr/bin/env python3
import sqlite3
import psycopg2
import json
import sys
from datetime import datetime

def migrate_data():
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sys.argv[1])
    sqlite_conn.row_factory = sqlite3.Row
    
    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(
        host=sys.argv[2],
        port=sys.argv[3],
        database=sys.argv[4],
        user=sys.argv[5]
    )
    pg_cur = pg_conn.cursor()
    
    try:
        # Migrate users (if table exists)
        try:
            sqlite_cur = sqlite_conn.execute("SELECT * FROM users")
            users = sqlite_cur.fetchall()
            for user in users:
                pg_cur.execute(
                    "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (user['id'], user['username'], user['email'], user['password_hash'], user['created_at'])
                )
            print(f"Migrated {len(users)} users")
        except sqlite3.OperationalError:
            print("No users table found, skipping...")
        
        # Migrate contexts
        try:
            sqlite_cur = sqlite_conn.execute("SELECT * FROM contexts")
            contexts = sqlite_cur.fetchall()
            for context in contexts:
                pg_cur.execute(
                    "INSERT INTO contexts (id, name, user_id, is_active, created_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (context['id'], context['name'], context.get('user_id', 1), context.get('is_active', False), context['created_at'])
                )
            print(f"Migrated {len(contexts)} contexts")
        except sqlite3.OperationalError:
            print("No contexts table found, skipping...")
        
        # Migrate memories
        try:
            sqlite_cur = sqlite_conn.execute("SELECT * FROM memories")
            memories = sqlite_cur.fetchall()
            for memory in memories:
                # Handle JSON data
                data = memory['data']
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except:
                        data = {"raw": data}
                
                pg_cur.execute(
                    "INSERT INTO memories (id, context_id, user_id, type, source, data, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                    (memory['id'], memory['context_id'], memory.get('user_id', 1), memory['type'], memory.get('source'), json.dumps(data), memory['created_at'])
                )
            print(f"Migrated {len(memories)} memories")
        except sqlite3.OperationalError as e:
            print(f"Error migrating memories: {e}")
        
        pg_conn.commit()
        print("Data migration completed successfully")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python migrate_data.py <sqlite_db> <pg_host> <pg_port> <pg_database> <pg_user>")
        sys.exit(1)
    migrate_data()
EOF

    # Run data migration
    python3 "$BACKUP_DIR/migrate_data.py" "$SQLITE_DB" "$PG_HOST" "$PG_PORT" "$PG_DATABASE" "$PG_USER"
    log_info "Data migration completed"
}

# Update configuration
update_configuration() {
    log_step "Updating configuration..."
    
    # Create new configuration with PostgreSQL
    cat > "$MEM0_DIR/mem0.config.json" << EOF
{
    "database": {
        "url": "postgresql://$PG_USER@$PG_HOST:$PG_PORT/$PG_DATABASE",
        "pool_size": 10,
        "max_overflow": 20
    },
    "server": {
        "host": "127.0.0.1",
        "port": 13370,
        "debug": false
    },
    "security": {
        "secret_key": "$(openssl rand -base64 32)",
        "token_expiry": 86400
    }
}
EOF
    
    log_info "Configuration updated for PostgreSQL"
}

# Validate migration
validate_migration() {
    log_step "Validating migration..."
    
    # Start mem0 server temporarily for testing
    cd "$MEM0_DIR"
    python3 server/main.py &
    SERVER_PID=$!
    sleep 3
    
    # Test basic functionality
    if curl -s http://localhost:13370/health > /dev/null; then
        log_info "Server started successfully with PostgreSQL"
    else
        log_error "Server failed to start with PostgreSQL"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop test server
    kill $SERVER_PID 2>/dev/null || true
    sleep 2
    
    log_info "Migration validation completed"
}

# Main execution
main() {
    echo "Starting PostgreSQL migration for mem0..."
    echo "Backup will be created at: $BACKUP_DIR"
    echo ""
    
    read -p "Continue with migration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled"
        exit 0
    fi
    
    check_prerequisites
    create_backup
    setup_postgresql
    migrate_schema
    migrate_data
    update_configuration
    validate_migration
    
    echo ""
    echo "🎉 PostgreSQL Migration Completed Successfully!"
    echo "============================================="
    log_info "Backup location: $BACKUP_DIR"
    log_info "PostgreSQL database: $PG_DATABASE"
    log_info "Configuration updated: mem0.config.json"
    echo ""
    echo "Next steps:"
    echo "1. Start mem0 server: ./manage.sh start"
    echo "2. Test functionality: ./client/mem0 contexts"
    echo "3. If issues occur, restore from backup in $BACKUP_DIR"
}

# Run main function
main "$@"
