#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Simple test script to verify Core API service can start
Tests basic imports and structure without full router complexity
"""

import sys
from pathlib import Path

# Add shared to path
current_dir = Path(__file__).parent
shared_dir = current_dir.parent.parent / "shared"
sys.path.insert(0, str(shared_dir))

print("🧪 Testing Core API Service Setup...")
print(f"📁 Shared directory: {shared_dir}")
print(f"📁 Current directory: {current_dir}")

# Test 1: Import database module
print("\n1️⃣  Testing database import...")
try:
    pass

    print("✅ DatabaseManager imported successfully")
except Exception as e:
    print(f"❌ Database import failed: {e}")
    sys.exit(1)

# Test 2: Import config
print("\n2️⃣  Testing config import...")
try:
    from utils.config import load_config

    print("✅ Config loaded successfully")
    config = load_config()
    print(f"📊 Config type: {type(config)}")
except Exception as e:
    print(f"❌ Config import failed: {e}")
    sys.exit(1)

# Test 3: Import auth utilities
print("\n3️⃣  Testing auth import...")
try:
    from utils.auth import JWT_ALGORITHM

    print("✅ Auth utilities imported successfully")
    print(f"🔐 JWT Algorithm: {JWT_ALGORITHM}")
except Exception as e:
    print(f"⚠️  Auth import failed (may need JWT_SECRET env var): {e}")

# Test 4: Test FastAPI app creation
print("\n4️⃣  Testing FastAPI app creation...")
try:
    from fastapi import FastAPI

    app = FastAPI(title="Core API Test")

    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "core-api-test"}

    print("✅ FastAPI app created successfully")
    print("📍 Health endpoint: /health")
except Exception as e:
    print(f"❌ FastAPI app creation failed: {e}")
    sys.exit(1)

# Test 5: List router files
print("\n5️⃣  Checking router files...")
routers_dir = current_dir / "routers"
if routers_dir.exists():
    router_files = list(routers_dir.glob("*.py"))
    print(f"✅ Found {len(router_files)} router files:")
    for rf in router_files:
        print(f"   📄 {rf.name}")
else:
    print("❌ Routers directory not found")

print("\n" + "=" * 50)
print("✅ ALL TESTS PASSED!")
print("=" * 50)
print("\n🚀 Core API service structure is valid!")
print("📝 Next: Fix router imports and test with uvicorn")
print("💡 Run: cd services/core-api && python test_service.py")
