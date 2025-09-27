#!/usr/bin/env python3
"""
Auth Protection Check - Prevents accidental re-enabling of broken middleware
Run this before starting the server to ensure auth routes won't hang
"""

import os
import sys


def check_auth_protection():
    """Check if the auth fix is still in place"""

    print("🔍 Checking auth protection status...")

    # Check security_integration.py
    security_file = "/app/server/security_integration.py"
    if os.path.exists(security_file):
        with open(security_file, "r") as f:
            content = f.read()

        if "TEMPORARILY DISABLED DUE TO REDIS HANG" not in content:
            print("🚨 CRITICAL: Auth middleware fix is MISSING!")
            print("❌ security_integration.py does not have the Redis hang protection")
            print("💥 Auth routes WILL HANG if you start the server!")
            return False
        else:
            print("✅ security_integration.py: Auth middleware properly disabled")

    # Check main.py
    main_file = "/app/server/main.py"
    if os.path.exists(main_file):
        with open(main_file, "r") as f:
            content = f.read()

        if "configure_security(app)" in content and not content.count(
            "# configure_security(app)"
        ):
            print("🚨 CRITICAL: configure_security is ENABLED!")
            print("❌ main.py has configure_security(app) uncommented")
            print("💥 Auth routes WILL HANG if you start the server!")
            return False
        else:
            print("✅ main.py: configure_security properly disabled")

    print("🎉 Auth protection is ACTIVE - safe to start server!")
    return True


if __name__ == "__main__":
    if not check_auth_protection():
        print("\n🛑 STOPPING: Fix the auth protection before starting server!")
        sys.exit(1)
    else:
        print("\n🚀 SAFE TO START: Auth protection verified!")
        sys.exit(0)
