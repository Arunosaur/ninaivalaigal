#!/usr/bin/env python3
"""Test database connection with dynamic IP resolution"""

import os
import sys
from pathlib import Path

# Add shared to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

# Set environment (matches rust-services/graphops/env.sh)
os.environ["NINA_ENV"] = "dev"
os.environ["NINA_DB_USER"] = "nina"
os.environ["NINA_DB_PASSWORD"] = "dev_password_change_in_production"

from utils.config import get_dynamic_database_url

print("="*60)
print("🧪 Testing Database Connection")
print("="*60)

# Get database URL
db_url = get_dynamic_database_url()
print(f"\n📊 Database URL: {db_url}")

# Test connection
try:
    from database import DatabaseManager
    
    print("\n🔌 Attempting to connect...")
    db = DatabaseManager(db_url)
    
    print("✅ DatabaseManager created")
    
    # Try a simple query
    from sqlalchemy import text
    session = db.get_session()
    result = session.execute(text("SELECT current_database(), current_user, version()"))
    row = result.fetchone()
    session.close()
    
    print(f"\n✅ Connected successfully!")
    print(f"   Database: {row[0]}")
    print(f"   User: {row[1]}")
    print(f"   Version: {row[2][:50]}...")
    
    # Check if users table exists
    session = db.get_session()
    result = session.execute(
        text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'")
    )
    table_exists = result.fetchone()[0] > 0
    session.close()
    
    if table_exists:
        print(f"\n✅ Users table exists")
        
        # Count users
        session = db.get_session()
        result = session.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.fetchone()[0]
        session.close()
        
        print(f"   Total users: {user_count}")
    else:
        print(f"\n⚠️  Users table does not exist (needs migration)")
    
    print("\n" + "="*60)
    print("✅ DATABASE CONNECTION TEST PASSED!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n" + "="*60)
    print("❌ DATABASE CONNECTION TEST FAILED!")
    print("="*60)
    sys.exit(1)
