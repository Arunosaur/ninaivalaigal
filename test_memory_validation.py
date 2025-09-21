#!/usr/bin/env python3
"""
Memory Validation Script for mem0
Tests JWT token retrieval, memory creation, and validation
"""

import time

import requests

BASE_URL = "http://localhost:8000"

def get_jwt_token(email, password):
    """Login and get JWT token"""
    login_data = {
        "email": email,
        "password": password
    }

    print(f"🔐 Logging in as {email}...")

    try:
        response = requests.post(f"{BASE_URL}/auth/login",
                               json=login_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                user_info = result.get('user', {})
                token = user_info.get('jwt_token') or result.get('access_token')

                print("✅ Login successful!")
                print(f"   User: {user_info.get('name')}")
                print(f"   Account Type: {user_info.get('account_type')}")
                print(f"   User ID: {user_info.get('user_id')}")
                print(f"   JWT Token: {token[:50] if token else 'None'}...")

                return token, user_info
            else:
                print(f"❌ Login failed: {result.get('detail')}")
                return None, None
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during login: {e}")
        return None, None

def create_test_context(token, context_name):
    """Create a test recording context"""
    context_data = {
        "name": context_name,
        "description": f"Test context for {context_name}"
    }

    print(f"\n📝 Creating context: {context_name}")

    try:
        response = requests.post(f"{BASE_URL}/contexts",
                               json=context_data,
                               headers={"Authorization": f"Bearer {token}"},
                               timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Context created successfully!")
            print(f"   Context ID: {result.get('id')}")
            print(f"   Name: {result.get('name')}")
            return result
        else:
            print(f"❌ Context creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during context creation: {e}")
        return None

def record_test_memory(token, context_name, memory_content):
    """Record a test memory in the context"""
    memory_data = {
        "content": memory_content,
        "context": context_name
    }

    print(f"\n💾 Recording memory in context '{context_name}':")
    print(f"   Content: {memory_content}")

    try:
        response = requests.post(f"{BASE_URL}/memory/record",
                               json=memory_data,
                               headers={"Authorization": f"Bearer {token}"},
                               timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Memory recorded successfully!")
            print(f"   Memory ID: {result.get('memory_id')}")
            return result
        else:
            print(f"❌ Memory recording failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during memory recording: {e}")
        return None

def recall_memories(token, context_name, query=None):
    """Recall memories from a context"""
    params = {"context": context_name}
    if query:
        params["query"] = query

    print(f"\n🔍 Recalling memories from context '{context_name}'")
    if query:
        print(f"   Query: {query}")

    try:
        response = requests.get(f"{BASE_URL}/memory/recall",
                              params=params,
                              headers={"Authorization": f"Bearer {token}"},
                              timeout=10)

        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])

            print(f"✅ Found {len(memories)} memories:")
            for i, memory in enumerate(memories, 1):
                print(f"   {i}. {memory.get('content', 'No content')[:100]}...")
                print(f"      Created: {memory.get('created_at', 'Unknown')}")
                print(f"      Context: {memory.get('context', 'Unknown')}")

            return memories
        else:
            print(f"❌ Memory recall failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during memory recall: {e}")
        return []

def list_contexts(token):
    """List all contexts for the user"""
    print("\n📋 Listing all contexts...")

    try:
        response = requests.get(f"{BASE_URL}/contexts",
                              headers={"Authorization": f"Bearer {token}"},
                              timeout=10)

        if response.status_code == 200:
            result = response.json()
            contexts = result.get('contexts', [])

            print(f"✅ Found {len(contexts)} contexts:")
            for i, context in enumerate(contexts, 1):
                print(f"   {i}. {context.get('name')} (ID: {context.get('id')})")
                print(f"      Description: {context.get('description', 'No description')}")
                print(f"      Created: {context.get('created_at', 'Unknown')}")

            return contexts
        else:
            print(f"❌ Context listing failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during context listing: {e}")
        return []

def main():
    """Main testing function"""
    print("🎯 mem0 Memory Validation Suite")
    print("=" * 50)

    # Test user credentials (update these with your registered user)
    test_email = input("Enter your test user email (or press Enter for john.developer@example.com): ").strip()
    if not test_email:
        test_email = "john.developer@example.com"

    test_password = input("Enter password (or press Enter for password123): ").strip()
    if not test_password:
        test_password = "password123"

    # Step 1: Get JWT token
    token, user_info = get_jwt_token(test_email, test_password)
    if not token:
        print("\n❌ Cannot proceed without valid token")
        return

    print(f"\n🎫 JWT Token obtained: {token}")

    # Step 2: List existing contexts
    existing_contexts = list_contexts(token)

    # Step 3: Create a test context
    test_context_name = f"test-validation-{int(time.time())}"
    context_result = create_test_context(token, test_context_name)

    if context_result:
        # Step 4: Record test memories
        test_memories = [
            "Working on mem0 user authentication system with JWT tokens",
            "Created FastAPI endpoints for signup, login, and dashboard",
            "Implemented PostgreSQL database with user isolation",
            "Built responsive frontend with Tailwind CSS",
            "Testing memory storage and retrieval functionality"
        ]

        print(f"\n📚 Recording {len(test_memories)} test memories...")
        for memory in test_memories:
            record_test_memory(token, test_context_name, memory)
            time.sleep(0.5)  # Brief pause between requests

        # Step 5: Recall all memories
        all_memories = recall_memories(token, test_context_name)

        # Step 6: Test query-based recall
        query_memories = recall_memories(token, test_context_name, "authentication JWT")

        # Step 7: List contexts again to see the new one
        updated_contexts = list_contexts(token)

    print("\n" + "=" * 50)
    print("✅ Memory validation complete!")
    print("\nNext steps:")
    print("1. Use this JWT token in your CLI tools")
    print("2. Test shell integration with this context")
    print("3. Try the MCP server with this user")
    print(f"\nYour JWT Token: {token}")
    print(f"Test Context: {test_context_name}")

if __name__ == "__main__":
    main()
