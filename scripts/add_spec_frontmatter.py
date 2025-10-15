#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC

"""
Add Docusaurus frontmatter to SPEC files that are missing it.
This enables proper sidebar generation and navigation.
"""

import os
import re
from pathlib import Path


def extract_spec_info(content, spec_dir):
    """Extract SPEC metadata from content"""
    # Extract SPEC ID from directory name
    spec_id = spec_dir.split("-")[0]

    # Extract title from first heading
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else f"SPEC-{spec_id}"

    # Clean up title (remove "Feature Specification:" prefix if present)
    title = re.sub(r"^Feature Specification:\s*", "", title)

    # Extract status
    status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
    status = status_match.group(1) if status_match else "Unknown"

    return {
        "id": spec_id,
        "title": title.strip(),
        "status": status,
        "sidebar_label": f"SPEC-{spec_id}: {title.strip()}",
    }


def add_frontmatter(file_path):
    """Add frontmatter to a spec.md file if it doesn't have it"""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if already has frontmatter
    if content.startswith("---"):
        print("  ✓ Already has frontmatter")
        return False

    # Extract SPEC info
    spec_dir = os.path.basename(os.path.dirname(file_path))
    info = extract_spec_info(content, spec_dir)

    # Create frontmatter
    frontmatter = f"""---
id: spec-{info['id']}
title: {info['title']}
sidebar_label: SPEC-{info['id']}
sidebar_position: {int(info['id'])}
tags: [{info['status']}]
---

"""

    # Write updated content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter + content)

    print(f"  ✅ Added frontmatter: {info['sidebar_label']}")
    return True


def main():
    specs_dir = Path("specs")
    updated = 0
    skipped = 0

    # Find all spec.md files
    for spec_dir in sorted(specs_dir.iterdir()):
        if not spec_dir.is_dir():
            continue

        # Skip template and special directories
        if spec_dir.name in ["000-template", "PHASE_SUMMARIES", "templates"]:
            continue

        spec_file = spec_dir / "spec.md"
        if not spec_file.exists():
            continue

        print(f"\n{spec_dir.name}:")
        if add_frontmatter(spec_file):
            updated += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"✅ Updated: {updated} files")
    print(f"⏭️  Skipped: {skipped} files (already had frontmatter)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
