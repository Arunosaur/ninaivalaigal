#!/usr/bin/env python3

import os
import sys

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "server"))

try:
    from database import DatabaseManager

    print("✅ DatabaseManager imported successfully")

    # Check if get_user_by_id method exists
    if hasattr(DatabaseManager, "get_user_by_id"):
        print("✅ get_user_by_id method exists")
    else:
        print("❌ get_user_by_id method NOT found")
        print(
            "Available methods:",
            [method for method in dir(DatabaseManager) if not method.startswith("_")],
        )

except Exception as e:
    print(f"❌ Import failed: {e}")
