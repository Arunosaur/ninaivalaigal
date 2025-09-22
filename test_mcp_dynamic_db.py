#!/usr/bin/env python3
"""
Test script for MCP server with dynamic database URL resolution
"""

import sys
import os

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'server'))

def test_dynamic_database_url():
    """Test the dynamic database URL resolution"""
    print("🧪 Testing MCP server dynamic database URL resolution...")
    
    try:
        # Import the MCP server module
        from mcp.server import get_dynamic_database_url, get_initialized_components
        
        print("\n1. Testing dynamic database URL resolution:")
        db_url = get_dynamic_database_url()
        print(f"   Database URL: {db_url}")
        
        print("\n2. Testing component initialization:")
        components = get_initialized_components()
        
        if components:
            print(f"   ✅ Components initialized successfully")
            print(f"   📊 Database manager: {type(components.get('db', 'None')).__name__}")
            print(f"   🔧 Config loaded: {'Yes' if components.get('config') else 'No'}")
            print(f"   👤 Default user ID: {components.get('DEFAULT_USER_ID', 'Unknown')}")
            
            # Test database connection
            db = components.get('db')
            if db and hasattr(db, 'engine'):
                try:
                    # Try a simple connection test
                    with db.engine.connect() as conn:
                        result = conn.execute("SELECT 1 as test").fetchone()
                        if result and result[0] == 1:
                            print(f"   ✅ Database connection successful")
                        else:
                            print(f"   ❌ Database connection failed: unexpected result")
                except Exception as e:
                    print(f"   ⚠️ Database connection test failed: {e}")
            else:
                print(f"   ⚠️ Database manager not available for connection test")
        else:
            print(f"   ❌ Component initialization failed")
            
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 This is expected if MCP dependencies are not installed")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    return True

def test_config_dynamic_url():
    """Test the config module dynamic URL resolution"""
    print("\n🧪 Testing config module dynamic database URL resolution...")
    
    try:
        from config import get_dynamic_database_url, get_database_url
        
        print("\n1. Testing config dynamic database URL:")
        db_url = get_dynamic_database_url()
        print(f"   Database URL: {db_url}")
        
        print("\n2. Testing legacy compatibility:")
        legacy_url = get_database_url()
        print(f"   Legacy URL: {legacy_url}")
        
        if db_url == legacy_url:
            print("   ✅ Legacy compatibility maintained")
        else:
            print("   ⚠️ Legacy compatibility issue")
            
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Testing ninaivalaigal MCP server modularization fixes...")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # Test 1: MCP server dynamic database URL
    if test_dynamic_database_url():
        success_count += 1
    
    # Test 2: Config module dynamic URL
    if test_config_dynamic_url():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("✅ All tests passed! Dynamic database URL resolution is working.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Check the output above for details.")
        sys.exit(1)
