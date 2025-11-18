#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Comprehensive Test Runner

Runs all test suites across the codebase with proper environment setup,
coverage reporting, and result aggregation.

Usage:
    python scripts/run_all_tests.py [--unit] [--integration] [--e2e] [--coverage] [--verbose]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def setup_test_environment():
    """Set up test environment variables"""
    # Set test-specific environment
    os.environ["NINA_ENV"] = "test"
    os.environ["PYTEST_CURRENT_TEST"] = "1"

    # Test database URL (can be overridden by environment)
    if "DATABASE_URL" not in os.environ:
        os.environ["DATABASE_URL"] = os.getenv(
            "TEST_DATABASE_URL",
            "postgresql://nina:dev_password_change_in_production@localhost:5432/ninaivalaigal_test",
        )

    # Test JWT secret
    if "NINAIVALAIGAL_JWT_SECRET" not in os.environ:
        os.environ["NINAIVALAIGAL_JWT_SECRET"] = "test_jwt_secret_for_testing_only"

    print("✅ Test environment configured")


def run_pytest_tests(
    test_paths: List[str],
    markers: Optional[List[str]] = None,
    coverage: bool = False,
    verbose: bool = False,
) -> Dict[str, any]:
    """Run pytest tests with specified options"""
    root = Path(__file__).parent.parent

    cmd = ["python", "-m", "pytest"]

    # Add test paths
    for path in test_paths:
        full_path = root / path
        if full_path.exists():
            cmd.append(str(full_path))
        else:
            print(f"⚠️  Test path not found: {path}")

    # Add markers
    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])

    # Add coverage
    if coverage:
        cmd.extend(["--cov=server", "--cov=services", "--cov-report=term-missing", "--cov-report=html"])

    # Add verbosity
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # Add other useful options
    cmd.extend(["--tb=short", "--strict-markers"])

    print(f"\n🧪 Running pytest: {' '.join(cmd)}")
    print("=" * 80)

    try:
        result = subprocess.run(cmd, cwd=root, capture_output=False, text=True)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
        }
    except Exception as e:
        print(f"❌ Failed to run pytest: {e}")
        return {"success": False, "error": str(e)}


def run_unit_tests(coverage: bool = False, verbose: bool = False) -> Dict[str, any]:
    """Run unit tests"""
    print("\n" + "=" * 80)
    print("UNIT TESTS")
    print("=" * 80)

    test_paths = ["tests/unit", "tests"]
    return run_pytest_tests(test_paths, markers=["unit"], coverage=coverage, verbose=verbose)


def run_integration_tests(coverage: bool = False, verbose: bool = False) -> Dict[str, any]:
    """Run integration tests"""
    print("\n" + "=" * 80)
    print("INTEGRATION TESTS")
    print("=" * 80)

    test_paths = ["tests/integration"]
    return run_pytest_tests(test_paths, markers=["integration"], coverage=coverage, verbose=verbose)


def run_e2e_tests(coverage: bool = False, verbose: bool = False) -> Dict[str, any]:
    """Run end-to-end tests"""
    print("\n" + "=" * 80)
    print("END-TO-END TESTS")
    print("=" * 80)

    test_paths = ["tests/e2e", "tests/agentic"]
    return run_pytest_tests(test_paths, markers=["e2e"], coverage=coverage, verbose=verbose)


def run_all_test_suites(
    unit: bool = True,
    integration: bool = False,
    e2e: bool = False,
    coverage: bool = False,
    verbose: bool = False,
) -> Dict[str, any]:
    """Run all specified test suites"""
    results = {}

    if unit:
        results["unit"] = run_unit_tests(coverage=coverage, verbose=verbose)

    if integration:
        results["integration"] = run_integration_tests(coverage=coverage, verbose=verbose)

    if e2e:
        results["e2e"] = run_e2e_tests(coverage=coverage, verbose=verbose)

    return results


def print_summary(results: Dict[str, any]):
    """Print test execution summary"""
    print("\n" + "=" * 80)
    print("TEST EXECUTION SUMMARY")
    print("=" * 80)

    total_suites = len(results)
    passed_suites = sum(1 for r in results.values() if r.get("success", False))

    for suite_name, result in results.items():
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        print(f"  {suite_name.upper()}: {status}")

    print(f"\n📊 Overall: {passed_suites}/{total_suites} test suites passed")

    if passed_suites == total_suites:
        print("🎉 All test suites passed!")
        return True
    else:
        print("⚠️  Some test suites failed")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Run comprehensive test suite")
    parser.add_argument("--unit", action="store_true", default=True, help="Run unit tests (default)")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--all", action="store_true", help="Run all test suites")

    args = parser.parse_args()

    # If --all is specified, run all suites
    if args.all:
        args.unit = True
        args.integration = True
        args.e2e = True

    print("🧪 Comprehensive Test Runner")
    print("=" * 80)

    # Setup environment
    setup_test_environment()

    # Run tests
    results = run_all_test_suites(
        unit=args.unit,
        integration=args.integration,
        e2e=args.e2e,
        coverage=args.coverage,
        verbose=args.verbose,
    )

    # Print summary
    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()




