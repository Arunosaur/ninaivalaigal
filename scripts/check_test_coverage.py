#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Check Test Coverage for New/Modified Files

Pre-commit hook to ensure new Python files have corresponding test files.
Also validates that modified files maintain test coverage.

Usage:
    python scripts/check_test_coverage.py --check-new-files
    python scripts/check_test_coverage.py --check-changed-files
    python scripts/check_test_coverage.py --file server/new_module.py
"""

import argparse
import subprocess
import sys
from pathlib import Path


def find_test_file(source_file: Path, root: Path = None) -> Path | None:
    """Find corresponding test file for a source file."""
    if root is None:
        root = Path.cwd()

    source_file = Path(source_file)

    # Normalize path
    if not source_file.is_absolute():
        source_file = root / source_file

    # Skip if not in server/ or services/
    if "server/" not in str(source_file) and "services/" not in str(source_file):
        return None

    # Skip test files themselves
    if "test_" in source_file.name or "tests/" in str(source_file):
        return None

    # Convert server/module/file.py -> tests/test_file.py or tests/module/test_file.py
    if "server/" in str(source_file):
        try:
            relative = source_file.relative_to(root / "server")

            # Handle __init__.py files specially
            if relative.name == "__init__.py":
                # For server/billing/__init__.py -> tests/test_billing_init.py
                module_name = relative.parent.name if relative.parent != Path(".") else "server"
                test_name = f"test_{module_name}_init.py"
            else:
                test_name = f"test_{relative.name}"

            # Try direct test file: tests/test_file.py
            test_path = root / "tests" / test_name
            if test_path.exists():
                return test_path

            # Try module-specific: tests/module/test_file.py
            if relative.parent != Path("."):
                if relative.name == "__init__.py":
                    # For server/billing/__init__.py -> tests/billing/test_billing_init.py
                    module_name = relative.parent.name
                    test_path = root / "tests" / relative.parent / f"test_{module_name}_init.py"
                else:
                    test_path = root / "tests" / relative.parent / f"test_{relative.name}"
                if test_path.exists():
                    return test_path

            # Try unit test directory
            if relative.name == "__init__.py":
                test_path = root / "tests" / "unit" / test_name
            else:
                test_path = root / "tests" / "unit" / f"test_{relative.name}"
            if test_path.exists():
                return test_path

            # Try integration test directory
            if relative.name == "__init__.py":
                test_path = root / "tests" / "integration" / test_name
            else:
                test_path = root / "tests" / "integration" / f"test_{relative.name}"
            if test_path.exists():
                return test_path

            # Try intelligence test directory
            if relative.name == "__init__.py":
                test_path = root / "tests" / "intelligence" / test_name
            else:
                test_path = root / "tests" / "intelligence" / f"test_{relative.name}"
            if test_path.exists():
                return test_path

            # Try server/tests/ directory structure (server/module/file.py -> server/tests/module/test_file.py)
            if relative.parent != Path("."):
                test_path = root / "server" / "tests" / relative.parent / f"test_{relative.name}"
                if test_path.exists():
                    return test_path

            # Try server/tests/performance/ for performance module
            if "performance" in str(relative.parent):
                test_path = root / "server" / "tests" / "performance" / f"test_{relative.name}"
                if test_path.exists():
                    return test_path

        except ValueError:
            # File not under server/ directory
            pass

    if "services/" in str(source_file):
        try:
            relative = source_file.relative_to(root / "services")

            # For services/core-api/lib/file.py or services/core-api/utils/file.py
            # Look for tests/test_file.py (flattened structure)
            test_name = f"test_{relative.name}"
            test_path = root / "tests" / test_name
            if test_path.exists():
                return test_path

            # Try service-specific test directory
            service_name = relative.parts[0] if len(relative.parts) > 1 else None
            if service_name:
                test_path = root / "tests" / service_name / f"test_{relative.name}"
                if test_path.exists():
                    return test_path

            # For services/core-api/lib/auth_audit.py -> tests/test_auth_audit.py
            # Extract just the filename without path
            if len(relative.parts) > 1:
                # services/core-api/lib/auth_audit.py -> auth_audit.py
                filename = relative.parts[-1]
                test_name = f"test_{filename}"
                test_path = root / "tests" / test_name
                if test_path.exists():
                    return test_path
        except ValueError:
            pass

    return None


def get_staged_files() -> list[Path]:
    """Get list of staged files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=A"], capture_output=True, text=True, check=True
        )
        return [Path(f) for f in result.stdout.strip().split("\n") if f and f.endswith(".py")]
    except subprocess.CalledProcessError:
        return []


def get_changed_files() -> list[Path]:
    """Get list of changed files (added or modified) in current branch."""
    try:
        # Get files changed compared to main/master
        result = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=AM", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        if not result.stdout.strip():
            # Try master instead of main
            result = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=AM", "origin/master...HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
        return [Path(f) for f in result.stdout.strip().split("\n") if f and f.endswith(".py")]
    except subprocess.CalledProcessError:
        return []


def check_new_files() -> bool:
    """Check if newly added Python files have test files."""
    root = Path.cwd()
    new_files = get_staged_files()

    # Exclude test runner scripts and utility scripts
    test_runner_patterns = [
        "run_memory_tests.py",
        "validate_memory_tests.py",
        "run_.*_tests.py",
        "validate_.*_tests.py",
    ]

    missing_tests = []
    for new_file in new_files:
        # Only check files in server/ or services/
        if "server/" not in str(new_file) and "services/" not in str(new_file):
            continue

        # Skip test files themselves
        if "test_" in new_file.name or "tests/" in str(new_file):
            continue

        # Skip test runner scripts (these are test harnesses, not modules under test)
        import re

        if any(re.search(pattern, new_file.name) for pattern in test_runner_patterns):
            continue

        test_file = find_test_file(new_file, root)
        if not test_file:
            missing_tests.append(new_file)

    if missing_tests:
        print("❌ New Python files found without corresponding test files:")
        print()
        for source in missing_tests:
            print(f"  📄 {source}")
            # Suggest test file location
            if "server/" in str(source):
                try:
                    # Normalize path: make it absolute if relative
                    source_path = source if source.is_absolute() else (root / source)
                    relative = source_path.relative_to(root / "server")
                    suggested = root / "tests" / f"test_{relative.name}"
                    print(f"     💡 Expected: {suggested.relative_to(root)}")
                except (ValueError, TypeError):
                    # If path can't be made relative, just suggest a generic test location
                    print(f"     💡 Expected: tests/test_{source.name}")
            print()
        print("⚠️  Please add test files before committing.")
        print("💡 Example: Create a test file with at least basic coverage.")
        return False

    print("✅ All new Python files have corresponding test files.")
    return True


def check_changed_files() -> bool:
    """Check if changed files maintain test coverage."""
    root = Path.cwd()
    changed_files = get_changed_files()

    if not changed_files:
        print("ℹ️  No changed files detected (not in a branch with commits?).")
        return True

    missing_tests = []
    for changed_file in changed_files:
        if "server/" not in str(changed_file) and "services/" not in str(changed_file):
            continue

        if "test_" in changed_file.name or "tests/" in str(changed_file):
            continue

        test_file = find_test_file(changed_file, root)
        if not test_file:
            missing_tests.append(changed_file)

    if missing_tests:
        print("⚠️  Changed Python files without corresponding test files:")
        print()
        for source in missing_tests:
            print(f"  📄 {source}")
            if "server/" in str(source):
                relative = Path(source).relative_to(root / "server")
                suggested = root / "tests" / f"test_{relative.name}"
                print(f"     💡 Expected: {suggested.relative_to(root)}")
            print()
        print("⚠️  Consider adding tests for modified functionality.")
        # Don't fail for changed files, just warn
        return True

    print("✅ All changed Python files have corresponding test files.")
    return True


def check_specific_file(file_path: str) -> bool:
    """Check if a specific file has a test file."""
    root = Path.cwd()
    source_file = Path(file_path)

    if not source_file.exists():
        print(f"❌ File not found: {file_path}")
        return False

    test_file = find_test_file(source_file, root)

    if test_file:
        print(f"✅ Test file found: {test_file.relative_to(root)}")
        return True
    else:
        print(f"❌ No test file found for: {file_path}")
        if "server/" in str(source_file):
            relative = source_file.relative_to(root / "server")
            suggested = root / "tests" / f"test_{relative.name}"
            print(f"💡 Suggested location: {suggested.relative_to(root)}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check test coverage for new or changed Python files")
    parser.add_argument(
        "--check-new-files", action="store_true", help="Check that newly added Python files have test files"
    )
    parser.add_argument(
        "--check-changed-files",
        action="store_true",
        help="Check that changed Python files have test files (warning only)",
    )
    parser.add_argument("--file", type=str, help="Check a specific file for test coverage")

    args = parser.parse_args()

    if args.file:
        success = check_specific_file(args.file)
    elif args.check_new_files:
        success = check_new_files()
    elif args.check_changed_files:
        success = check_changed_files()
    else:
        # Default: check new files
        success = check_new_files()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
