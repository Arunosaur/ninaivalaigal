#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Validate document placement to ensure files are in the correct directories.

This script checks markdown files against the document organization rules
defined in docs/DOCUMENT_ORGANIZATION.md.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Document organization rules
RULES = {
    # Completion reports should be in governance/reports/
    r"^US\d+_COMPLETION": "governance/reports/",
    r"^US\d+_COMPLETION_SUMMARY": "governance/reports/",
    r"^US\d+_IMPLEMENTATION_STATUS": "governance/reports/",
    r"^US\d+_PROGRESS_REPORT": "governance/reports/",
    r"^US\d+_\d+_\d+_COMPLETION": "governance/reports/",
    # SPEC completion reports
    r"^SPEC_\d+_\d+_REFACTORING_COMPLETE": "governance/reports/",
    r"^SPEC_\d+_COMPLETE": "governance/reports/",
    r"^SPEC_STATUS_MONTHLY": "governance/reports/",
    r"^SPEC_AUDIT_COMPLETE": "governance/reports/",
    r"^SPEC_GOVERNANCE": "governance/reports/",
    # SPEC analysis should be in docs/spec-analysis/
    r"^SPEC_\d+_ANALYSIS": "docs/spec-analysis/",
    r"^SPEC_\d+_COMPREHENSIVE_ANALYSIS": "docs/spec-analysis/",
    r"^SPEC_\d+_CROSS_REFERENCE": "docs/spec-analysis/",
    r"^SPEC_\d+_TAIGA_STORIES": "docs/spec-analysis/",
    # Security docs should be in docs/security/
    r"_SECURITY\.md$": "docs/security/",
    r"^TENANCY_GUARD": "docs/security/",
    r"SECURITY.*\.md$": "docs/security/",
    # Architecture docs
    r"^FRONTEND_ARCHITECTURE": "docs/",
    r"ARCHITECTURE.*\.md$": "docs/",  # Allow in docs/ or docs/architecture/
    # Task-related (but not completion reports)
    r"^DEVELOPER_[A-Z]_TASKS": "tasks/active/",
    r"^US\d+_TASK": "tasks/",
}

# Directories that should NOT have certain document types
FORBIDDEN_PATTERNS = {
    "docs/": [
        (r"^US\d+_COMPLETION", "Completion reports should be in governance/reports/"),
        (r"^SPEC_\d+_COMPLETE$", "SPEC completion reports should be in governance/reports/"),
    ],
    "tasks/": [
        (r"^US\d+_COMPLETION", "Completion reports should be in governance/reports/"),
        (r"^SPEC_\d+_ANALYSIS", "SPEC analysis should be in docs/spec-analysis/"),
    ],
    ".": [
        (r"^US\d+_COMPLETION", "Completion reports should be in governance/reports/"),
        (r"^SPEC_\d+_COMPLETE$", "SPEC completion reports should be in governance/reports/"),
        (r"^SPEC_\d+_ANALYSIS", "SPEC analysis should be in docs/spec-analysis/"),
    ],
}

# Directories that are allowed to have any document type
ALLOWED_ANYWHERE = [
    "governance/reports/",
    "docs/spec-analysis/",
    "docs/security/",
    "docs/guides/",
    "docs/architecture/",
    "tasks/active/",
    "tasks/completed/",
    "tasks/archive/",
    "specs/",  # SPEC directories
    "shared/contracts/",  # Contract-related documentation
    "docs/MASTER_ARCHIVE/",  # Archived documents
    "rust-services/",  # Service-specific documentation
    "docs/developer-reviews/",  # Developer review documents
    "docs/specs/",  # SPEC implementation summaries
]

# Files that are exceptions (root level standard files)
EXCEPTIONS = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "CURRENT_STATUS.md",
    "MIGRATION_PROGRESS.md",
]


def check_file(file_path: Path) -> List[Tuple[str, str, str]]:
    """
    Check if a file is in the correct location.

    Returns list of (file_path, expected_location, issue_description)
    """
    issues = []
    file_name = file_path.name
    file_dir = str(file_path.parent) + "/"

    # Skip exceptions (root level standard files)
    if file_name in EXCEPTIONS:
        return issues

    # Skip if in allowed directory
    if any(file_dir.startswith(allowed) for allowed in ALLOWED_ANYWHERE):
        return issues

    # Check forbidden patterns
    for base_dir, patterns in FORBIDDEN_PATTERNS.items():
        if file_dir.startswith(base_dir) or (base_dir == "." and "/" not in file_dir):
            for pattern, message in patterns:
                if re.search(pattern, file_name):
                    issues.append((str(file_path), "governance/reports/", message))

    # Check positive rules (only for completion reports and SPEC analysis)
    # Be lenient with architecture/security docs in docs/ root
    strict_patterns = [
        r"^US\d+_COMPLETION",
        r"^US\d+_COMPLETION_SUMMARY",
        r"^US\d+_IMPLEMENTATION_STATUS",
        r"^SPEC_\d+_COMPLETE$",
        r"^SPEC_\d+_\d+_REFACTORING_COMPLETE",
        r"^SPEC_\d+_ANALYSIS",
    ]

    for pattern, expected_dir in RULES.items():
        if re.search(pattern, file_name, re.IGNORECASE):
            # Normalize paths for comparison
            expected_normalized = expected_dir.rstrip("/")
            file_dir_normalized = file_dir.rstrip("/")

            # Only enforce strict rules for completion reports and SPEC analysis
            is_strict = any(re.search(sp, file_name, re.IGNORECASE) for sp in strict_patterns)

            # For architecture/security docs in docs/ root, just warn if not in subdirectory
            if not is_strict and expected_dir in ["docs/architecture/", "docs/security/", "docs/"]:
                if file_dir_normalized.startswith("docs/"):
                    # Allow in docs/ or any docs/ subdirectory
                    continue

            if not file_dir_normalized.startswith(expected_normalized):
                issues.append(
                    (str(file_path), expected_dir, f"File matches pattern '{pattern}' but is not in {expected_dir}")
                )

    return issues


def validate_all_markdown_files(root_dir: Path = None) -> List[Tuple[str, str, str]]:
    """Validate all markdown files in the repository."""
    if root_dir is None:
        root_dir = Path(__file__).parent.parent

    all_issues = []

    # Exclude certain directories
    exclude_dirs = {
        "node_modules",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "htmlcov",
        "coverage",
        "dist",
        "build",
        "target",
        "docusaurus/.docusaurus",
        ".obsidian",
    }

    for md_file in root_dir.rglob("*.md"):
        # Skip excluded directories
        if any(excluded in md_file.parts for excluded in exclude_dirs):
            continue

        issues = check_file(md_file)
        all_issues.extend(issues)

    return all_issues


def main():
    """Main validation function."""
    root_dir = Path(__file__).parent.parent

    # Check files from git if available, otherwise check all
    if len(sys.argv) > 1:
        # Check specific files from command line
        files_to_check = [Path(f) for f in sys.argv[1:]]
    else:
        # Check all markdown files
        files_to_check = None

    if files_to_check:
        all_issues = []
        for file_path in files_to_check:
            if file_path.exists() and file_path.suffix == ".md":
                issues = check_file(file_path)
                all_issues.extend(issues)
    else:
        all_issues = validate_all_markdown_files(root_dir)

    if all_issues:
        print("❌ Document placement validation failed!\n")
        print("Found documents in incorrect locations:\n")

        for file_path, expected_location, issue in all_issues:
            print(f"  📄 {file_path}")
            print(f"     Expected: {expected_location}")
            print(f"     Issue: {issue}\n")

        print("\n💡 Fix:")
        print("  1. Move files to the correct directory")
        print("  2. See docs/DOCUMENT_ORGANIZATION.md for rules")
        print("  3. Run this script again to verify\n")

        return 1
    else:
        print("✅ All documents are in correct locations!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
