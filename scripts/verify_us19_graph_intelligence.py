#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""Verify US#19: Graph intelligence algorithms implementation"""

import os
import sys


def check_file_exists(filepath):
    """Check if file exists and return info"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        with open(filepath, "r") as f:
            lines = len(f.readlines())
        return True, size, lines
    return False, 0, 0


def check_implementation():
    """Check graph intelligence implementation"""
    print("=" * 70)
    print("US#19: Graph Intelligence Algorithms - Implementation Verification")
    print("=" * 70)
    print()

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Key files to check
    files_to_check = [
        ("server/graph/graph_reasoner.py", "Core GraphReasoner implementation"),
        ("server/graph/age_client.py", "Apache AGE client"),
        ("server/graph_intelligence_api.py", "Graph Intelligence API endpoints"),
        ("services/graph-service/routers/graph_intelligence_api.py", "Graph service API"),
        ("tests/unit/test_graph_reasoner_unit.py", "Unit tests"),
        ("tests/functional/test_graph_reasoner_functional.py", "Functional tests"),
        ("tests/performance/benchmark_reasoner.py", "Performance tests"),
    ]

    print("📋 Implementation Files:")
    print("-" * 70)

    all_exist = True
    total_lines = 0

    for filepath, description in files_to_check:
        full_path = os.path.join(base_path, filepath)
        exists, size, lines = check_file_exists(full_path)

        if exists:
            print(f"✅ {filepath}")
            print(f"   {description}")
            print(f"   Size: {size:,} bytes, Lines: {lines:,}")
            total_lines += lines
        else:
            print(f"❌ {filepath} - NOT FOUND")
            print(f"   {description}")
            all_exist = False
        print()

    # Check for key methods
    print("🔍 Key Methods Verification:")
    print("-" * 70)

    reasoner_path = os.path.join(base_path, "server/graph/graph_reasoner.py")
    if os.path.exists(reasoner_path):
        with open(reasoner_path, "r") as f:
            content = f.read()

        methods = [
            "explain_context",
            "infer_relevance",
            "feedback_loop",
            "analyze_memory_network",
        ]

        for method in methods:
            if f"def {method}" in content or f"async def {method}" in content:
                print(f"✅ {method}() implemented")
            else:
                print(f"❌ {method}() NOT FOUND")
    else:
        print("⚠️  Cannot verify methods - graph_reasoner.py not found")

    print()

    # Check API endpoints
    print("🌐 API Endpoints Verification:")
    print("-" * 70)

    api_path = os.path.join(base_path, "server/graph_intelligence_api.py")
    if os.path.exists(api_path):
        with open(api_path, "r") as f:
            content = f.read()

        endpoints = [
            "explain_context",
            "infer_relevance",
            "feedback",
            "analyze_network",
        ]

        for endpoint in endpoints:
            if endpoint in content.lower():
                print(f"✅ {endpoint} endpoint exists")
            else:
                print(f"⚠️  {endpoint} endpoint not found")
    else:
        print("⚠️  Cannot verify endpoints - graph_intelligence_api.py not found")

    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    files_found = sum(1 for f, _ in files_to_check if check_file_exists(os.path.join(base_path, f))[0])
    print(f"Files checked: {len(files_to_check)}")
    print(f"Files found: {files_found}")
    print(f"Total implementation lines: {total_lines:,}")
    print()

    if all_exist:
        print("✅ All core implementation files exist")
        print("✅ Graph intelligence algorithms implementation appears complete")
        print()
        print("Next steps:")
        print("  - Run unit tests: pytest tests/unit/test_graph_reasoner_unit.py")
        print("  - Run functional tests: pytest tests/functional/test_graph_reasoner_functional.py")
        print("  - Verify API endpoints are accessible")
    else:
        print("⚠️  Some files are missing")

    print()


if __name__ == "__main__":
    check_implementation()
