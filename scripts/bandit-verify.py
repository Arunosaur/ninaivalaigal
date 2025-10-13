#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Bandit Security Verification Script.

Validates that all Bandit exclusions and nosec comments are documented
and justified. Ensures security exceptions are traceable and auditable.
"""

import json
import re
import sys
from pathlib import Path
from typing import List


class BanditVerifier:
    """Verify Bandit security configuration and inline suppressions."""

    def __init__(self, repo_root: Path):
        """Initialize verifier."""
        self.repo_root = repo_root
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def verify_nosec_comments(self) -> bool:
        """Verify all # nosec comments have proper justification."""
        print("🔍 Verifying # nosec comments...")

        server_dir = self.repo_root / "server"
        nosec_pattern = re.compile(r"#\s*nosec\s*(B\d+)?")

        files_checked = 0
        nosec_found = 0

        for py_file in server_dir.rglob("*.py"):
            files_checked += 1
            with open(py_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    match = nosec_pattern.search(line)
                    if match:
                        nosec_found += 1
                        test_id = match.group(1) or "UNKNOWN"

                        # Check if comment has justification
                        if len(line) < 50 or " - " not in line:
                            self.warnings.append(
                                f"{py_file.relative_to(self.repo_root)}:{line_num}: "
                                f"# nosec {test_id} without clear justification"
                            )

        print(f"  ✓ Checked {files_checked} files")
        print(f"  ℹ️  Found {nosec_found} # nosec comments")

        return True

    def verify_bandit_config(self) -> bool:
        """Verify .bandit configuration is documented."""
        print("🔍 Verifying .bandit configuration...")

        bandit_file = self.repo_root / ".bandit"
        policy_file = self.repo_root / "docs" / "SECURITY_BANDIT_POLICY.md"

        if not bandit_file.exists():
            self.errors.append("Missing .bandit configuration file")
            return False

        if not policy_file.exists():
            self.warnings.append("Missing SECURITY_BANDIT_POLICY.md documentation")

        # Read skip rules
        with open(bandit_file, "r") as f:
            content = f.read()
            skip_match = re.search(r"skips:\s*\[([^\]]+)\]", content)
            if skip_match:
                skips = skip_match.group(1).replace("'", "").replace('"', "").split(",")
                skips = [s.strip() for s in skips]
                print(f"  ✓ Found {len(skips)} skip rules: {', '.join(skips)}")
            else:
                self.warnings.append("No skip rules found in .bandit")

        return True

    def verify_scan_results(self) -> bool:
        """Verify latest Bandit scan results meet security threshold."""
        print("🔍 Verifying Bandit scan results...")

        report_file = self.repo_root / "bandit-report.json"

        if not report_file.exists():
            print("  ⚠️  No bandit-report.json found (run: bandit -c .bandit -r server/ -f json -o bandit-report.json)")
            return True

        with open(report_file, "r") as f:
            data = json.load(f)

        metrics = data["metrics"]["_totals"]
        high = metrics["SEVERITY.HIGH"]
        medium = metrics["SEVERITY.MEDIUM"]
        low = metrics["SEVERITY.LOW"]

        print("  📊 Security Issues:")
        print(f"     HIGH: {high}")
        print(f"     MEDIUM: {medium}")
        print(f"     LOW: {low}")

        if high > 0:
            self.errors.append(f"CRITICAL: {high} HIGH severity security issues detected")
            return False

        if medium > 0:
            self.warnings.append(f"{medium} MEDIUM severity issues (should be reviewed)")

        print("  ✅ No HIGH severity issues")
        return True

    def generate_report(self) -> None:
        """Generate verification report."""
        print("\n" + "=" * 60)
        print("📋 BANDIT VERIFICATION REPORT")
        print("=" * 60 + "\n")

        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors:
                print(f"  • {error}")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  • {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ ALL CHECKS PASSED - No issues found!\n")
        elif not self.errors:
            print("✅ VERIFICATION PASSED (with warnings)\n")
        else:
            print("❌ VERIFICATION FAILED\n")

    def run(self) -> bool:
        """Run all verification checks."""
        print("🔒 Bandit Security Verification\n")

        checks = [
            self.verify_bandit_config(),
            self.verify_nosec_comments(),
            self.verify_scan_results(),
        ]

        self.generate_report()

        return all(checks) and len(self.errors) == 0


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    verifier = BanditVerifier(repo_root)

    success = verifier.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
