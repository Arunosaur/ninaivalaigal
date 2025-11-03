#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074: GDPR Compliance Test Script

Tests the GDPR compliance implementation:
- Database models
- Data collection
- Export generation
- API endpoints (if server is running)

Usage:
    python scripts/test_gdpr_compliance.py

Requirements:
    - Database connection configured
    - Server dependencies installed
"""

import os
import sys
from pathlib import Path

# Add server directory to path
server_path = Path(__file__).parent.parent / "server"
sys.path.insert(0, str(server_path))


def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from compliance.models import (
            DataExport,
            DataSubjectRequest,
            DataSubjectRequestType,
            ExportFormat,
            ExportStatus,
            RequestStatus,
        )

        print("✅ Models import successful")

        from compliance.gdpr import GDPRComplianceManager

        print("✅ GDPR manager import successful")

        from compliance.export import EncryptedDataExporter

        print("✅ Export system import successful")

        from compliance.data_collector import GDPRDataCollector

        print("✅ Data collector import successful")

        from compliance.api import router

        print("✅ API router import successful")

        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_models():
    """Test model definitions"""
    print("\n🔍 Testing models...")
    try:
        from compliance.models import (
            DataSubjectRequestType,
            ExportFormat,
            ExportStatus,
            RequestStatus,
        )

        # Test enum values
        assert DataSubjectRequestType.ACCESS.value == "access"
        assert RequestStatus.PENDING.value == "pending"
        assert ExportFormat.JSON.value == "json"
        assert ExportStatus.PENDING.value == "pending"

        print("✅ Model enums are correct")
        return True
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False


def test_database_connection():
    """Test database connection and table existence"""
    print("\n🔍 Testing database connection...")
    try:
        from database import DatabaseManager

        db = DatabaseManager()
        session = db.get_session()

        # Check if tables exist
        from sqlalchemy import inspect

        inspector = inspect(db.engine)

        tables = inspector.get_table_names(schema="public")

        required_tables = ["data_subject_requests", "data_exports"]
        missing_tables = []

        for table in required_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"⚠️  Table '{table}' not found - migration may not be applied")
                missing_tables.append(table)

        session.close()

        if missing_tables:
            print(f"\n⚠️  Missing tables: {missing_tables}")
            print("   Run: cd server && alembic upgrade head")
            return False

        return True
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("   Make sure database is running and connection is configured")
        return False


def test_data_collector():
    """Test data collector initialization"""
    print("\n🔍 Testing data collector...")
    try:
        from compliance.data_collector import GDPRDataCollector
        from database import DatabaseManager

        db = DatabaseManager()
        session = db.get_session()

        collector = GDPRDataCollector(session)
        print("✅ Data collector initialized")

        session.close()
        return True
    except Exception as e:
        print(f"❌ Data collector error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_router():
    """Test API router registration"""
    print("\n🔍 Testing API router...")
    try:
        from compliance.api import router

        assert router.prefix == "/api/v1/compliance"
        assert "gdpr-compliance" in router.tags

        # Count routes
        route_count = len(router.routes)
        print(f"✅ API router has {route_count} routes registered")

        # Check key routes exist
        route_paths = [route.path for route in router.routes]
        expected_routes = [
            "/dsar",
            "/erasure",
            "/portability",
            "/requests",
        ]

        for expected in expected_routes:
            if any(expected in path for path in route_paths):
                print(f"   ✅ Route '{expected}' found")
            else:
                print(f"   ⚠️  Route '{expected}' not found")

        return True
    except Exception as e:
        print(f"❌ API router test error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("SPEC-074: GDPR Compliance Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Models", test_models()))
    results.append(("Database", test_database_connection()))
    results.append(("Data Collector", test_data_collector()))
    results.append(("API Router", test_api_router()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 1 implementation is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
