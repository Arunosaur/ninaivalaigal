# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Test script for gRPC client prototype."""

import asyncio
import sys

from graphops_client.grpc_client_prototype import test_connection


async def main():
    """Run basic connection test."""
    print("Testing gRPC client prototype...")
    print("=" * 70)

    try:
        success = await test_connection()
        if success:
            print("\n✅ Prototype test PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Prototype test FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Prototype test ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
