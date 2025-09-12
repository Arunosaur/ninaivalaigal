#!/usr/bin/env python3
"""
SQLite to PostgreSQL data migration script for mem0
Migrates all existing data from SQLite to PostgreSQL database
"""

import sqlite3
import psycopg2
import json
import sys
from datetime import datetime

def migrate_data():
    """Migrate data from SQLite to PostgreSQL"""
    
    # Database connections
    sqlite_db = "/Users/asrajag/Workspace/mem0/mem0.db"
    pg_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'mem0db',
        'user': 'mem0user'
    }
    
    print("🔄 Starting SQLite to PostgreSQL migration...")
    
    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        print(f"✅ Connected to SQLite: {sqlite_db}")
    except Exception as e:
        print(f"❌ Failed to connect to SQLite: {e}")
        return False
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(**pg_config)
        pg_cur = pg_conn.cursor()
        print(f"✅ Connected to PostgreSQL: {pg_config['database']}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return False
    
    try:
        # Get SQLite table info
        sqlite_cur = sqlite_conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cur.fetchall()]
        print(f"📋 Found SQLite tables: {tables}")
        
        # Migrate memories table
        if 'memories' in tables:
            print("\n🔄 Migrating memories...")
            sqlite_cur = sqlite_conn.execute("SELECT * FROM memories")
            memories = sqlite_cur.fetchall()
            
            migrated_count = 0
            for memory in memories:
                try:
                    # Handle JSON data
                    data = memory['data']
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except:
                            data = {"raw": data}
                    
                    # Map SQLite memory to PostgreSQL structure
                    # First, find or create context
                    context_name = memory['context']
                    user_id = memory.get('user_id', 1)
                    
                    # Check if context exists
                    pg_cur.execute(
                        "SELECT id FROM contexts WHERE name = %s AND user_id = %s",
                        (context_name, user_id)
                    )
                    context_result = pg_cur.fetchone()
                    
                    if context_result:
                        context_id = context_result[0]
                    else:
                        # Create context
                        pg_cur.execute(
                            "INSERT INTO contexts (name, user_id, created_at) VALUES (%s, %s, %s) RETURNING id",
                            (context_name, user_id, memory['created_at'])
                        )
                        context_id = pg_cur.fetchone()[0]
                    
                    # Insert memory
                    pg_cur.execute(
                        "INSERT INTO memories (context_id, user_id, type, source, data, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
                        (
                            context_id,
                            user_id,
                            memory['type'],
                            memory.get('source', 'unknown'),
                            json.dumps(data),
                            memory['created_at']
                        )
                    )
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Failed to migrate memory {memory.get('id', 'unknown')}: {e}")
                    continue
            
            print(f"✅ Migrated {migrated_count}/{len(memories)} memories")
        
        # Commit all changes
        pg_conn.commit()
        print("\n🎉 Migration completed successfully!")
        
        # Verify migration
        pg_cur.execute("SELECT COUNT(*) FROM memories")
        memory_count = pg_cur.fetchone()[0]
        
        pg_cur.execute("SELECT COUNT(*) FROM contexts")
        context_count = pg_cur.fetchone()[0]
        
        print(f"📊 PostgreSQL now contains:")
        print(f"   - {memory_count} memories")
        print(f"   - {context_count} contexts")
        
        return True
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Migration failed: {e}")
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    success = migrate_data()
    sys.exit(0 if success else 1)
