#!/usr/bin/env python3
"""
Reset user password for test users
Direct database access to update password hash
"""

import bcrypt
import sqlite3
import os
from pathlib import Path

def reset_password_sqlite(email, new_password):
    """Reset password using SQLite database"""
    db_path = Path("/Users/asrajag/Workspace/mem0/mem0.db")
    
    if not db_path.exists():
        print(f"❌ SQLite database not found at {db_path}")
        return False
    
    try:
        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, email FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {email} not found in database")
            conn.close()
            return False
        
        user_id, user_email = user
        print(f"✅ Found user: ID={user_id}, Email={user_email}")
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (password_hash.decode('utf-8'), email)
        )
        
        conn.commit()
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            print(f"✅ Password updated successfully for {email}")
            print(f"   New password: {new_password}")
            conn.close()
            return True
        else:
            print(f"❌ No rows updated for {email}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error updating password: {e}")
        return False

def reset_password_postgresql(email, new_password):
    """Reset password using PostgreSQL database"""
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        # Get database URL from environment
        db_url = os.getenv('MEM0_DATABASE_URL')
        if not db_url:
            print("❌ MEM0_DATABASE_URL not set")
            return False
        
        # Parse database URL
        parsed = urlparse(db_url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        # Hash the new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Check if user exists
        cursor.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User {email} not found in PostgreSQL database")
            conn.close()
            return False
        
        user_id, user_email = user
        print(f"✅ Found user: ID={user_id}, Email={user_email}")
        
        # Update password
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s",
            (password_hash.decode('utf-8'), email)
        )
        
        conn.commit()
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            print(f"✅ Password updated successfully for {email}")
            print(f"   New password: {new_password}")
            conn.close()
            return True
        else:
            print(f"❌ No rows updated for {email}")
            conn.close()
            return False
            
    except ImportError:
        print("❌ psycopg2 not installed for PostgreSQL access")
        return False
    except Exception as e:
        print(f"❌ Error updating PostgreSQL password: {e}")
        return False

def test_login_after_reset(email, password):
    """Test login after password reset"""
    import requests
    
    try:
        response = requests.post(
            "http://localhost:8000/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login test successful!")
            print(f"   Token: {result.get('user', {}).get('jwt_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Login test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login test error: {e}")
        return False

def main():
    """Reset password for test user"""
    print("🔐 mem0 Password Reset Tool")
    print("=" * 40)
    
    email = "durai@example.com"
    new_password = "test1234"
    
    print(f"Resetting password for: {email}")
    print(f"New password: {new_password}")
    print()
    
    # Try PostgreSQL first
    print("🐘 Trying PostgreSQL...")
    if reset_password_postgresql(email, new_password):
        print("✅ PostgreSQL password reset successful")
        
        # Test login
        print("\n🧪 Testing login...")
        if test_login_after_reset(email, new_password):
            print("🎉 Password reset complete and verified!")
            return
    
    # Fall back to SQLite
    print("\n💾 Trying SQLite...")
    if reset_password_sqlite(email, new_password):
        print("✅ SQLite password reset successful")
        
        # Test login
        print("\n🧪 Testing login...")
        if test_login_after_reset(email, new_password):
            print("🎉 Password reset complete and verified!")
            return
    
    print("❌ Password reset failed on both databases")

if __name__ == "__main__":
    main()
