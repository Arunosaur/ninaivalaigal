#!/usr/bin/env python3
"""Validate SPEC directory structure and continuity.

This script ensures the /specs/ directory maintains a living specification system by:
1. Verifying SPEC numbering continuity (no gaps in sequence)
2. Ensuring each SPEC folder contains a README.md
3. Validating all markdown files are properly organized

Usage:
    python scripts/validate_specs.py

Exit codes:
    0 - All validations passed
    1 - Validation failures detected
"""

import sys
from pathlib import Path
from typing import List, Tuple


def get_spec_folders(specs_dir: Path) -> List[Path]:
    """Get all SPEC folders (formatted as NNN-description)."""
    spec_folders = []
    for item in specs_dir.iterdir():
        if item.is_dir() and item.name[0].isdigit():
            # Match pattern: 001-name, 116-internal-frontend-migration, etc.
            spec_folders.append(item)
    return sorted(spec_folders)


def extract_spec_number(folder: Path) -> int:
    """Extract SPEC number from folder name (e.g., '116-...' -> 116)."""
    try:
        return int(folder.name.split("-")[0])
    except (ValueError, IndexError):
        return -1


def validate_spec_continuity(spec_folders: List[Path]) -> Tuple[bool, List[str]]:
    """Validate SPEC numbering is continuous."""
    errors = []
    spec_numbers = [extract_spec_number(f) for f in spec_folders]
    spec_numbers = [n for n in spec_numbers if n > 0]  # Filter invalid

    if not spec_numbers:
        return True, []

    spec_numbers.sort()
    min_spec = spec_numbers[0]
    max_spec = spec_numbers[-1]

    # Check for gaps in sequence
    expected_range = set(range(min_spec, max_spec + 1))
    actual_set = set(spec_numbers)
    missing = expected_range - actual_set

    if missing:
        errors.append(
            f"❌ SPEC numbering gaps detected: {sorted(missing)}\n"
            f"   Expected continuous range: {min_spec}-{max_spec}"
        )

    # Check for duplicates
    if len(spec_numbers) != len(set(spec_numbers)):
        duplicates = [n for n in spec_numbers if spec_numbers.count(n) > 1]
        errors.append(f"❌ Duplicate SPEC numbers found: {sorted(set(duplicates))}")

    return len(errors) == 0, errors


def validate_readme_existence(spec_folders: List[Path]) -> Tuple[bool, List[str]]:
    """Ensure each SPEC folder contains README.md."""
    errors = []
    for folder in spec_folders:
        readme_path = folder / "README.md"
        if not readme_path.exists():
            errors.append(f"❌ Missing README.md in {folder.name}")

    return len(errors) == 0, errors


def validate_markdown_organization(specs_dir: Path) -> Tuple[bool, List[str]]:
    """Validate all markdown files are properly organized."""
    errors = []
    warnings = []

    # Find all .md files in specs directory
    all_md_files = list(specs_dir.rglob("*.md"))

    # Exclude allowed files in root
    allowed_root_files = {"SPEC_INDEX.md"}
    root_md_files = [f for f in specs_dir.glob("*.md") if f.name not in allowed_root_files]

    if root_md_files:
        warnings.append(
            f"⚠️  Markdown files in /specs/ root (should be in subfolders):\n"
            f"   {', '.join(f.name for f in root_md_files)}"
        )

    # Check PHASE_SUMMARIES organization
    phase_summaries = specs_dir / "PHASE_SUMMARIES"
    if phase_summaries.exists():
        phase_md_files = list(phase_summaries.glob("*.md"))
        if len(phase_md_files) > 20:
            warnings.append(
                f"⚠️  PHASE_SUMMARIES has {len(phase_md_files)} files " f"(consider archiving old summaries)"
            )

    # Print warnings but don't fail
    for warning in warnings:
        print(warning)

    return len(errors) == 0, errors


def main():
    """Run all SPEC validations."""
    specs_dir = Path(__file__).parent.parent / "specs"

    if not specs_dir.exists():
        print(f"❌ SPEC directory not found: {specs_dir}")
        sys.exit(1)

    print("🔍 Validating SPEC structure...")
    print(f"📂 Directory: {specs_dir}\n")

    all_passed = True
    all_errors = []

    # Get SPEC folders
    spec_folders = get_spec_folders(specs_dir)
    print(f"✅ Found {len(spec_folders)} SPEC folders\n")

    # Run validations
    validations = [
        ("SPEC Numbering Continuity", validate_spec_continuity, spec_folders),
        ("README.md Existence", validate_readme_existence, spec_folders),
        ("Markdown Organization", validate_markdown_organization, specs_dir),
    ]

    for name, validator, *args in validations:
        print(f"Running: {name}")
        passed, errors = validator(*args) if args else validator()

        if passed:
            print(f"  ✅ {name} passed\n")
        else:
            print(f"  ❌ {name} failed:")
            for error in errors:
                print(f"     {error}")
            print()
            all_passed = False
            all_errors.extend(errors)

    # Final summary
    print("=" * 60)
    if all_passed:
        print("✅ All SPEC validations passed!")
        print("Your living SPEC system is healthy 🌲")
        sys.exit(0)
    else:
        print("❌ SPEC validation failed!")
        print(f"\nTotal errors: {len(all_errors)}")
        print("\nPlease fix the issues above before merging.")
        sys.exit(1)


if __name__ == "__main__":
    main()
