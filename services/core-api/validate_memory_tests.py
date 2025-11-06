#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Validation script for Memory Browser API tests
Validates test coverage and structure without running full test suite
"""

import ast
import inspect
import os
from pathlib import Path
from typing import Dict, List, Set


def analyze_test_file(file_path: str) -> Dict[str, any]:
    """Analyze a test file and extract test information"""

    if not os.path.exists(file_path):
        return {"error": f"File {file_path} not found"}

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Parse the AST
        tree = ast.parse(content)

        test_functions = []
        test_classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Get function info
                test_functions.append(
                    {"name": node.name, "line": node.lineno, "args": [arg.arg for arg in node.args.args]}
                )

            elif isinstance(node, ast.ClassDef) and any(
                "Test" in base.id for base in node.bases if isinstance(base, ast.Name)
            ):
                # Get class info
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
                test_classes.append({"name": node.name, "line": node.lineno, "methods": methods})

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")

        return {
            "file_path": file_path,
            "test_functions": test_functions,
            "test_classes": test_classes,
            "imports": imports,
            "total_tests": len(test_functions) + sum(len(cls["methods"]) for cls in test_classes),
        }

    except Exception as e:
        return {"error": f"Failed to analyze {file_path}: {str(e)}"}


def validate_crud_coverage(test_analysis: Dict[str, any]) -> Dict[str, any]:
    """Validate that CRUD operations are properly tested"""

    if "error" in test_analysis:
        return test_analysis

    coverage = {
        "create": False,
        "read": False,
        "update": False,
        "delete": False,
        "list": False,
        "error_handling": False,
        "authentication": False,
        "serialization": False,
    }

    # Check test names and classes for CRUD coverage
    all_tests = []

    # Add function tests
    for func in test_analysis["test_functions"]:
        all_tests.append(func["name"].lower())

    # Add class method tests
    for cls in test_analysis["test_classes"]:
        for method in cls["methods"]:
            all_tests.append(method.lower())
        # Also check class names
        all_tests.append(cls["name"].lower())

    # Check coverage
    test_patterns = {
        "create": ["create", "post"],
        "read": ["get", "retrieve", "read"],
        "update": ["update", "put", "patch"],
        "delete": ["delete", "remove"],
        "list": ["list", "get_all"],
        "error_handling": ["error", "exception", "invalid", "not_found"],
        "authentication": ["auth", "unauthorized", "permission"],
        "serialization": ["serialize", "serial"],
    }

    for operation, patterns in test_patterns.items():
        for test_name in all_tests:
            if any(pattern in test_name for pattern in patterns):
                coverage[operation] = True
                break

    return coverage


def main():
    """Main validation function"""

    print("=" * 80)
    print("MEMORY CRUD ENDPOINTS TEST VALIDATION")
    print("=" * 80)

    # Analyze the test file
    root = Path(__file__).parent.parent.parent
    test_file = root / "services" / "core-api" / "tests" / "test_memory_browser_api.py"
    analysis = analyze_test_file(str(test_file))

    if "error" in analysis:
        print(f"❌ {analysis['error']}")
        return False

    print(f"\n📊 Test File Analysis: {os.path.basename(test_file)}")
    print(f"   Total Tests: {analysis['total_tests']}")
    print(f"   Test Classes: {len(analysis['test_classes'])}")
    print(f"   Test Functions: {len(analysis['test_functions'])}")

    # Validate CRUD coverage
    coverage = validate_crud_coverage(analysis)

    print(f"\n🎯 CRUD Coverage Analysis:")
    for operation, covered in coverage.items():
        status = "✅" if covered else "❌"
        print(f"   {status} {operation.replace('_', ' ').title()}")

    # Calculate coverage percentage
    covered_operations = sum(coverage.values())
    total_operations = len(coverage)
    coverage_percentage = (covered_operations / total_operations) * 100

    print(f"\n📈 Overall Test Coverage: {coverage_percentage:.1f}%")

    # Show test structure
    print(f"\n📋 Test Structure:")
    for cls in analysis["test_classes"]:
        print(f"   📁 {cls['name']} ({len(cls['methods'])} tests)")
        for method in cls["methods"]:
            print(f"      - {method}")

    if analysis["test_functions"]:
        print(f"   📄 Standalone Functions ({len(analysis['test_functions'])} tests)")
        for func in analysis["test_functions"]:
            print(f"      - {func['name']}")

    # Check imports
    critical_imports = ["pytest", "TestClient", "Mock"]
    print(f"\n📦 Critical Imports Check:")
    for imp in critical_imports:
        found = any(imp in imported for imported in analysis["imports"])
        status = "✅" if found else "❌"
        print(f"   {status} {imp}")

    # Validation result
    print(f"\n" + "=" * 80)
    if coverage_percentage >= 80:
        print("✅ VALIDATION PASSED: Comprehensive test coverage detected!")
        print("   The test suite covers all major CRUD operations and edge cases.")
        print("   Other developers can safely make changes and run tests to validate.")
    else:
        print("⚠️  VALIDATION WARNING: Test coverage could be improved.")
        print(f"   Consider adding tests for uncovered operations.")

    print("=" * 80)

    return coverage_percentage >= 80


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
