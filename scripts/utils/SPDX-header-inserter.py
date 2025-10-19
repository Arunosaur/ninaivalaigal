#!/usr/bin/env python3
"""
SPDX Header Inserter for Ninaivalaigal Project

Automatically adds SPDX license identifiers to source files based on their location.

Usage:
    python3 SPDX-header-inserter.py [--dry-run] [--path PATH] [--license LICENSE]

Options:
    --dry-run        Show what would be changed without modifying files
    --path PATH      Only process files in this directory (default: entire repo)
    --license TYPE   Force a specific license (MIT, Apache-2.0, Elastic-2.0, Proprietary)
    --remove         Remove existing SPDX headers
    --check          Check if headers are present (exit 1 if missing)

Examples:
    # Dry run to see what would change
    python3 SPDX-header-inserter.py --dry-run

    # Add headers to frontend only
    python3 SPDX-header-inserter.py --path frontend-nextjs-customer

    # Force MIT license on specific directory
    python3 SPDX-header-inserter.py --path packages/ui --license MIT

    # Check if all files have headers (for CI)
    python3 SPDX-header-inserter.py --check

SPDX-License-Identifier: MIT
Copyright (c) 2025 Medhasys LLC
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# License mapping based on directory
LICENSE_MAP = {
    "frontend-nextjs-customer": "MIT",
    "frontend-nextjs-admin": "MIT",
    "frontend-shared": "MIT",
    "packages/ui": "MIT",
    "packages/api-client": "MIT",
    "scripts": "MIT",
    "cli": "Apache-2.0",
    "sdk": "Apache-2.0",
    "server": "Proprietary",
    "containers": "Elastic-2.0",
    "k8s": "Elastic-2.0",
    "terraform": "Elastic-2.0",
}

# File extensions to process
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".sh": "shell",
    ".yml": "yaml",
    ".yaml": "yaml",
}

# Comment styles for different languages
COMMENT_STYLES = {
    "python": {"start": "#", "end": ""},
    "typescript": {"start": "//", "end": ""},
    "javascript": {"start": "//", "end": ""},
    "shell": {"start": "#", "end": ""},
    "yaml": {"start": "#", "end": ""},
}

# Directories and files to skip
SKIP_PATTERNS = [
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".next",
    "coverage",
    ".venv",
    "venv",
    ".mypy_cache",
    "LICENSE",  # Don't modify LICENSE files
    ".md",  # Don't modify markdown files
    ".json",  # Don't modify JSON files
    ".lock",  # Don't modify lockfiles
]


def should_skip(path: Path) -> bool:
    """Check if file or directory should be skipped."""
    for pattern in SKIP_PATTERNS:
        if pattern in str(path):
            return True
    return False


def determine_license(file_path: Path, force_license: Optional[str] = None) -> str:
    """Determine which license applies to a file based on its path."""
    if force_license:
        return force_license

    # Check each license mapping
    for directory, license_type in LICENSE_MAP.items():
        if str(file_path).startswith(directory):
            return license_type

    # Default to Proprietary for unspecified paths
    return "Proprietary"


def get_language(file_path: Path) -> Optional[str]:
    """Determine the programming language from file extension."""
    return SUPPORTED_EXTENSIONS.get(file_path.suffix)


def create_header(license_type: str, language: str, file_path: Path) -> List[str]:
    """Create SPDX header based on license type and language."""
    comment_style = COMMENT_STYLES.get(language)
    if not comment_style:
        return []

    comment_start = comment_style["start"]

    header_lines = []

    # Add shebang for Python/Shell files if missing
    if language in ["python", "shell"]:
        header_lines.append(f"#!/usr/bin/env {'python3' if language == 'python' else 'bash'}\n")

    # SPDX identifier
    header_lines.append(f"{comment_start} SPDX-License-Identifier: {license_type}\n")

    # Copyright notice
    header_lines.append(f"{comment_start} Copyright (c) 2025 Medhasys LLC\n")

    # Add description line for proprietary code
    if license_type == "Proprietary":
        header_lines.append(f"{comment_start}\n")
        header_lines.append(f"{comment_start} This file contains proprietary code owned by Medhasys LLC.\n")
        header_lines.append(f"{comment_start} Unauthorized copying, modification, or distribution is prohibited.\n")
        header_lines.append(f"{comment_start} See LICENSE file in the server/ directory for details.\n")

    # Blank line after header
    header_lines.append(f"{comment_start}\n")

    return header_lines


def has_spdx_header(content: str) -> bool:
    """Check if file already has an SPDX header."""
    return "SPDX-License-Identifier" in content


def remove_existing_header(lines: List[str], language: str) -> List[str]:
    """Remove existing SPDX header if present."""
    comment_start = COMMENT_STYLES[language]["start"]

    # Find where header ends
    header_end = 0
    for i, line in enumerate(lines):
        if line.strip().startswith(comment_start) or line.strip() == "":
            if "SPDX-License-Identifier" in line or "Copyright" in line:
                header_end = i + 1
        else:
            break

    # Remove header lines
    return lines[header_end:]


def process_file(
    file_path: Path,
    dry_run: bool = False,
    force_license: Optional[str] = None,
    remove_headers: bool = False,
) -> Tuple[bool, str]:
    """
    Process a single file to add/update SPDX header.

    Returns:
        Tuple of (modified: bool, message: str)
    """
    language = get_language(file_path)
    if not language:
        return False, f"Skipped {file_path}: Unsupported file type"

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
            lines = original_content.splitlines(keepends=True)
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

    # Remove existing header if requested
    if remove_headers:
        if has_spdx_header(original_content):
            new_lines = remove_existing_header(lines, language)
            new_content = "".join(new_lines)

            if not dry_run:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
            return True, f"Removed header from {file_path}"
        else:
            return False, f"No header found in {file_path}"

    # Skip if already has header
    if has_spdx_header(original_content):
        return False, f"Skipped {file_path}: Already has SPDX header"

    # Determine license and create header
    license_type = determine_license(file_path, force_license)
    header_lines = create_header(license_type, language, file_path)

    if not header_lines:
        return False, f"Skipped {file_path}: Could not create header"

    # Handle shebang preservation
    if lines and lines[0].startswith("#!"):
        # Keep existing shebang, add header after it
        new_content = lines[0] + "".join(header_lines[1:]) + "".join(lines[1:])
    else:
        # Add header at the beginning
        new_content = "".join(header_lines) + original_content

    # Write file if not dry run
    if not dry_run:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
        except Exception as e:
            return False, f"Error writing {file_path}: {e}"

    return True, f"{'Would add' if dry_run else 'Added'} {license_type} header to {file_path}"


def find_source_files(root_path: Path) -> List[Path]:
    """Find all source files in the given path."""
    source_files = []

    for file_path in root_path.rglob("*"):
        # Skip directories
        if file_path.is_dir():
            continue

        # Skip files/directories in skip list
        if should_skip(file_path):
            continue

        # Check if file extension is supported
        if file_path.suffix in SUPPORTED_EXTENSIONS:
            source_files.append(file_path)

    return source_files


def check_headers(root_path: Path) -> Tuple[bool, List[str]]:
    """Check if all files have SPDX headers."""
    source_files = find_source_files(root_path)
    missing_headers = []

    for file_path in source_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if not has_spdx_header(content):
                    missing_headers.append(str(file_path))
        except Exception:
            continue

    all_have_headers = len(missing_headers) == 0
    return all_have_headers, missing_headers


def main():
    """Main entry point for SPDX header inserter."""
    parser = argparse.ArgumentParser(
        description="Add SPDX headers to Ninaivalaigal source files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Process files only in this directory (default: current directory)",
    )

    parser.add_argument(
        "--license",
        type=str,
        choices=["MIT", "Apache-2.0", "Elastic-2.0", "Proprietary"],
        help="Force a specific license for all processed files",
    )

    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove existing SPDX headers instead of adding them",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if headers are present (exit 1 if any are missing)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output",
    )

    args = parser.parse_args()

    root_path = Path(args.path).resolve()

    if not root_path.exists():
        print(f"Error: Path {root_path} does not exist", file=sys.stderr)
        sys.exit(1)

    # Check mode
    if args.check:
        all_have_headers, missing_headers = check_headers(root_path)

        if all_have_headers:
            print("✅ All source files have SPDX headers")
            sys.exit(0)
        else:
            print(f"❌ {len(missing_headers)} files missing SPDX headers:")
            for file_path in missing_headers:
                print(f"  - {file_path}")
            sys.exit(1)

    # Find all source files
    source_files = find_source_files(root_path)

    if not source_files:
        print(f"No source files found in {root_path}")
        sys.exit(0)

    print(f"Found {len(source_files)} source files to process")

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Process files
    modified_count = 0
    skipped_count = 0

    for file_path in source_files:
        modified, message = process_file(
            file_path,
            dry_run=args.dry_run,
            force_license=args.license,
            remove_headers=args.remove,
        )

        if modified:
            modified_count += 1
            if args.verbose:
                print(f"✓ {message}")
        else:
            skipped_count += 1
            if args.verbose:
                print(f"- {message}")

    # Summary
    print("\n" + ("=" * 60))
    print("Summary:")
    print(f"  Total files found: {len(source_files)}")
    print(f"  {'Would modify' if args.dry_run else 'Modified'}: {modified_count}")
    print(f"  Skipped: {skipped_count}")
    print(("=" * 60) + "\n")

    if args.dry_run and modified_count > 0:
        print("⚠️  Run without --dry-run to apply these changes")


if __name__ == "__main__":
    main()
