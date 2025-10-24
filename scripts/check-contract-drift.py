#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Unified Contract Drift Detection

Validates both API contracts and database schema for breaking changes.
Main entry point for US #87: Schema Drift Prevention CI.

This script combines:
- API contract validation (Proto + OpenAPI)
- Database schema drift detection (Alembic migrations)
- Breaking change detection
- Comprehensive reporting

Usage:
    python scripts/check-contract-drift.py
    python scripts/check-contract-drift.py --fail-on-warnings
    python scripts/check-contract-drift.py --api-only
    python scripts/check-contract-drift.py --db-only
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class UnifiedDriftDetector:
    """Unified detector for API and database schema drift."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.results: Dict[str, Dict] = {}

    def run_api_validation(self) -> bool:
        """Run API contract validation."""
        print("\n" + "=" * 70)
        print("📡 API CONTRACT VALIDATION")
        print("=" * 70)

        script_path = self.root_dir / "ci" / "validate-api-contracts.py"

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)], cwd=self.root_dir, capture_output=True, text=True
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["api_validation"] = {"passed": result.returncode == 0, "returncode": result.returncode}

            return result.returncode == 0

        except Exception as e:
            print(f"❌ API validation failed: {e}")
            self.results["api_validation"] = {"passed": False, "error": str(e)}
            return False

    def run_schema_validation(self, fail_on_warnings: bool = False) -> bool:
        """Run database schema drift detection."""
        print("\n" + "=" * 70)
        print("🗄️  DATABASE SCHEMA VALIDATION")
        print("=" * 70)

        script_path = self.root_dir / "scripts" / "check-schema-drift.py"

        cmd = [sys.executable, str(script_path)]
        if fail_on_warnings:
            cmd.append("--fail-on-warnings")

        try:
            result = subprocess.run(cmd, cwd=self.root_dir, capture_output=True, text=True)

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["schema_validation"] = {"passed": result.returncode == 0, "returncode": result.returncode}

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Schema validation failed: {e}")
            self.results["schema_validation"] = {"passed": False, "error": str(e)}
            return False

    def run_breaking_change_detection(self, base_ref: str, head_ref: str) -> bool:
        """Run breaking change detection (for CI/PRs)."""
        print("\n" + "=" * 70)
        print("🚨 BREAKING CHANGE DETECTION")
        print("=" * 70)

        script_path = self.root_dir / "ci" / "check-breaking-changes.py"

        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--base", base_ref, "--head", head_ref],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            self.results["breaking_changes"] = {"passed": result.returncode == 0, "returncode": result.returncode}

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Breaking change detection failed: {e}")
            self.results["breaking_changes"] = {"passed": False, "error": str(e)}
            return False

    def generate_summary(self) -> None:
        """Generate comprehensive summary report."""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)

        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r.get("passed", False))

        print(f"\nTotal Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")

        print("\nResults:")
        for check_name, result in self.results.items():
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            print(f"  {status} - {check_name.replace('_', ' ').title()}")

            if "error" in result:
                print(f"    Error: {result['error']}")

        print("=" * 70)

    def all_passed(self) -> bool:
        """Check if all validations passed."""
        return all(r.get("passed", False) for r in self.results.values())


def main():
    parser = argparse.ArgumentParser(
        description="Unified contract drift detection (API + Database)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all validations
  python scripts/check-contract-drift.py

  # Fail on warnings
  python scripts/check-contract-drift.py --fail-on-warnings

  # Only check API contracts
  python scripts/check-contract-drift.py --api-only

  # Only check database schema
  python scripts/check-contract-drift.py --db-only

  # Check for breaking changes (for CI/PR)
  python scripts/check-contract-drift.py --check-breaking --base origin/main --head HEAD
        """,
    )

    parser.add_argument("--api-only", action="store_true", help="Only validate API contracts (skip database schema)")
    parser.add_argument("--db-only", action="store_true", help="Only validate database schema (skip API contracts)")
    parser.add_argument(
        "--fail-on-warnings", action="store_true", help="Fail if warnings are found (default: only fail on errors)"
    )
    parser.add_argument(
        "--check-breaking",
        action="store_true",
        help="Check for breaking changes between git refs (requires --base and --head)",
    )
    parser.add_argument("--base", help="Base git ref for breaking change detection (e.g., origin/main)")
    parser.add_argument("--head", default="HEAD", help="Head git ref for breaking change detection (default: HEAD)")

    args = parser.parse_args()

    # Validate arguments
    if args.check_breaking and not args.base:
        parser.error("--check-breaking requires --base")

    if args.api_only and args.db_only:
        parser.error("Cannot specify both --api-only and --db-only")

    # Determine root directory
    root_dir = Path(__file__).parent.parent

    print("🔍 Unified Contract Drift Detection")
    print("=" * 70)
    print(f"Root Directory: {root_dir}")
    print(f"API Validation: {'Yes' if not args.db_only else 'No'}")
    print(f"Schema Validation: {'Yes' if not args.api_only else 'No'}")
    print(f"Breaking Changes: {'Yes' if args.check_breaking else 'No'}")
    print("=" * 70)

    # Run validations
    detector = UnifiedDriftDetector(root_dir)

    # API validation
    if not args.db_only:
        api_ok = detector.run_api_validation()
        if not api_ok and not args.check_breaking:
            # Early exit if API validation fails and we're not checking breaking changes
            detector.generate_summary()
            sys.exit(1)

    # Database schema validation
    if not args.api_only:
        schema_ok = detector.run_schema_validation(args.fail_on_warnings)
        if not schema_ok and not args.check_breaking:
            # Early exit if schema validation fails and we're not checking breaking changes
            detector.generate_summary()
            sys.exit(1)

    # Breaking change detection (optional, usually for CI/PRs)
    if args.check_breaking:
        detector.run_breaking_change_detection(args.base, args.head)

    # Generate summary
    detector.generate_summary()

    # Exit with appropriate code
    sys.exit(0 if detector.all_passed() else 1)


if __name__ == "__main__":
    main()
