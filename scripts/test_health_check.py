#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Test Health Check

Quick health check for test infrastructure:
- Verifies test files are accessible
- Checks test dependencies
- Validates test configuration
- Reports test infrastructure status

Usage:
    python scripts/test_health_check.py
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def check_pytest_available() -> bool:
    """Check if pytest is available"""
    try:
        result = subprocess.run(["python", "-m", "pytest", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def check_test_directories() -> Dict[str, bool]:
    """Check if test directories exist"""
    root = Path(__file__).parent.parent
    directories = {
        "tests/": root / "tests",
        "tests/unit/": root / "tests" / "unit",
        "tests/integration/": root / "tests" / "integration",
        "tests/e2e/": root / "tests" / "e2e",
    }

    results = {}
    for name, path in directories.items():
        results[name] = path.exists() and path.is_dir()

    return results


def count_test_files() -> Dict[str, int]:
    """Count test files by type"""
    root = Path(__file__).parent.parent

    counts = {
        "python": 0,
        "typescript": 0,
        "rust": 0,
        "go": 0,
    }

    # Python tests
    for test_file in root.rglob("test_*.py"):
        if "tests/" in str(test_file) or "__tests__" in str(test_file):
            counts["python"] += 1

    # TypeScript tests
    for test_file in root.rglob("*.test.ts"):
        counts["typescript"] += 1
    for test_file in root.rglob("*.test.tsx"):
        counts["typescript"] += 1

    # Rust tests
    for test_file in root.rglob("*_test.rs"):
        counts["rust"] += 1

    # Go tests
    for test_file in root.rglob("*_test.go"):
        counts["go"] += 1

    return counts


def check_test_configuration() -> Dict[str, bool]:
    """Check test configuration files"""
    root = Path(__file__).parent.parent

    configs = {
        "pytest.ini": root / "pytest.ini",
        "conftest.py": root / "tests" / "conftest.py",
        ".pre-commit-config.yaml": root / ".pre-commit-config.yaml",
    }

    results = {}
    for name, path in configs.items():
        results[name] = path.exists()

    return results


def check_test_scripts() -> Dict[str, bool]:
    """Check if test utility scripts exist"""
    scripts_dir = Path(__file__).parent

    scripts = {
        "check_test_coverage.py": scripts_dir / "check_test_coverage.py",
        "check_multi_lang_test_coverage.py": scripts_dir / "check_multi_lang_test_coverage.py",
        "run_all_tests.py": scripts_dir / "run_all_tests.py",
        "generate_test_report.py": scripts_dir / "generate_test_report.py",
    }

    results = {}
    for name, path in scripts.items():
        results[name] = path.exists()

    return results


def print_health_report():
    """Print comprehensive health check report"""
    print("🏥 Test Infrastructure Health Check")
    print("=" * 80)

    # Check pytest
    pytest_available = check_pytest_available()
    status = "✅" if pytest_available else "❌"
    print(f"\n{status} pytest: {'Available' if pytest_available else 'Not available'}")

    # Check directories
    print("\n📁 Test Directories:")
    dirs = check_test_directories()
    for name, exists in dirs.items():
        status = "✅" if exists else "⚠️"
        print(f"  {status} {name}")

    # Count test files
    print("\n📊 Test Files:")
    counts = count_test_files()
    for lang, count in counts.items():
        print(f"  {lang.capitalize()}: {count} test files")

    # Check configuration
    print("\n⚙️  Configuration Files:")
    configs = check_test_configuration()
    for name, exists in configs.items():
        status = "✅" if exists else "⚠️"
        print(f"  {status} {name}")

    # Check scripts
    print("\n🔧 Test Scripts:")
    scripts = check_test_scripts()
    for name, exists in scripts.items():
        status = "✅" if exists else "⚠️"
        print(f"  {status} {name}")

    # Overall health
    print("\n" + "=" * 80)
    all_checks = (
        pytest_available
        and all(dirs.values())
        and sum(counts.values()) > 0
        and all(configs.values())
        and all(scripts.values())
    )

    if all_checks:
        print("🎉 Test infrastructure is healthy!")
        return True
    else:
        print("⚠️  Some test infrastructure components need attention")
        return False


def main():
    """Main function"""
    healthy = print_health_report()
    sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()




