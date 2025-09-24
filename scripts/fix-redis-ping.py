#!/usr/bin/env python3
"""
Redis Ping Fix for Graph Intelligence
Updates Redis client usage to use proper ping() method
"""

import os
import re
from pathlib import Path


def find_redis_usage_files(project_root):
    """Find files that use RedisClient"""
    redis_files = []

    # Common patterns for Redis usage
    patterns = [
        "server/graph/graph_reasoner.py",
        "server/graph/graph_intelligence.py",
        "server/graph/*.py",
        "server/api/graph_intelligence.py",
        "server/api/routes/graph_intelligence.py",
    ]

    for pattern in patterns:
        for file_path in Path(project_root).glob(pattern):
            if file_path.is_file():
                with open(file_path, "r") as f:
                    content = f.read()
                    if "RedisClient" in content and "ping" in content:
                        redis_files.append(file_path)

    return redis_files


def fix_redis_ping_usage(file_path):
    """Fix Redis ping usage in a file"""
    print(f"🔧 Fixing Redis usage in {file_path}")

    with open(file_path, "r") as f:
        content = f.read()

    original_content = content

    # Fix patterns
    fixes = [
        # Fix direct ping() calls
        (r"redis\.ping\(\)", "await redis.ping()"),
        (r"self\.redis\.ping\(\)", "await self.redis.ping()"),
        (r"redis_client\.ping\(\)", "await redis_client.ping()"),
        # Fix hasattr checks
        (r"hasattr\(redis, 'ping'\)", "hasattr(redis, 'ping')"),
        # Add proper async/await if missing
        (r"def.*health.*check", "async def health_check"),
    ]

    for pattern, replacement in fixes:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    # Add import if needed
    if "import asyncio" not in content and "await" in content:
        content = "import asyncio\n" + content

    if content != original_content:
        # Backup original
        backup_path = f"{file_path}.backup"
        with open(backup_path, "w") as f:
            f.write(original_content)

        # Write fixed version
        with open(file_path, "w") as f:
            f.write(content)

        print(f"✅ Fixed {file_path} (backup: {backup_path})")
        return True
    else:
        print(f"ℹ️  No changes needed in {file_path}")
        return False


def main():
    """Main fix function"""
    project_root = "/Users/swami/WorkSpace/ninaivalaigal"

    print("🔍 Searching for Redis usage files...")
    redis_files = find_redis_usage_files(project_root)

    if not redis_files:
        print("❌ No Redis usage files found. Checking common locations...")
        # Check common server locations
        common_paths = [
            "server/graph/graph_reasoner.py",
            "server/api/routes/graph_intelligence.py",
            "server/graph_intelligence/health.py",
        ]

        for path in common_paths:
            full_path = Path(project_root) / path
            if full_path.exists():
                redis_files.append(full_path)

    if redis_files:
        print(f"📁 Found {len(redis_files)} files with Redis usage:")
        for file_path in redis_files:
            print(f"  - {file_path}")

        for file_path in redis_files:
            fix_redis_ping_usage(file_path)
    else:
        print("❌ No Redis files found. Manual inspection needed.")
        print("\n💡 Manual Fix Options:")
        print("1. Search for 'RedisClient' in your codebase:")
        print("   grep -r 'RedisClient.*ping' server/")
        print("\n2. Replace patterns like:")
        print("   redis.ping() → await redis.ping()")
        print("   redis_client.ping() → await redis_client.ping()")
        print("\n3. Or use hasattr check:")
        print("   hasattr(redis, 'ping')")


if __name__ == "__main__":
    main()
