#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
SPEC Index Audit Script
Compares SPEC_INDEX.md against actual directory structure and README files
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_spec_from_index(index_path: Path) -> Dict[int, Dict]:
    """Extract SPEC entries from SPEC_INDEX.md"""
    index_content = index_path.read_text()
    specs = {}

    # Pattern to match table rows: | 027 | Title | Status | Phase |
    pattern = r"^\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"

    for line in index_content.split("\n"):
        match = re.match(pattern, line)
        if match:
            num = int(match.group(1))
            title = match.group(2).strip()
            status = match.group(3).strip()
            phase = match.group(4).strip()

            # Skip deprecated entries
            if "DEPRECATED" in title or "~~" in title:
                continue

            specs[num] = {"title": title, "status": status, "phase": phase, "source": "index"}

    return specs


def extract_spec_from_directory(specs_dir: Path) -> Dict[int, Dict]:
    """Extract SPEC info from directory names and README files"""
    specs = {}

    for dirpath in sorted(specs_dir.iterdir()):
        if not dirpath.is_dir():
            continue

        match = re.match(r"^(\d+)-", dirpath.name)
        if not match:
            continue

        num = int(match.group(1))
        readme_path = dirpath / "README.md"

        spec_info = {
            "dir": dirpath.name,
            "has_readme": readme_path.exists(),
            "title": None,
            "status": None,
            "phase": None,
            "source": "directory",
        }

        if readme_path.exists():
            content = readme_path.read_text()

            # Extract title - try multiple patterns
            title_patterns = [
                r"^#\s+SPEC-\d+:\s*(.+?)$",
                r"^#\s+(.+?)(?:\s+\*\*Status\*\*|$)",
                r'^title:\s*["\'](.+?)["\']',
            ]

            for pattern in title_patterns:
                match = re.search(pattern, content, re.MULTILINE)
                if match:
                    spec_info["title"] = match.group(1).strip()
                    break

            # Extract status
            status_patterns = [
                r"\*\*Status\*\*:\s*(.+?)(?:\n|$)",
                r"Status:\s*(.+?)(?:\n|$)",
            ]

            for pattern in status_patterns:
                match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                if match:
                    spec_info["status"] = match.group(1).strip()
                    break

        specs[num] = spec_info

    return specs


def normalize_status(status: str) -> str:
    """Normalize status strings for comparison"""
    if not status:
        return "Unknown"

    status_lower = status.lower()

    # Map various status formats to standard ones
    if any(x in status_lower for x in ["complete", "✅", "done", "finished"]):
        return "Complete"
    elif any(x in status_lower for x in ["in progress", "🔄", "active", "development"]):
        return "In Progress"
    elif any(x in status_lower for x in ["planned", "📋", "proposed", "scheduled"]):
        return "Planned"
    elif any(x in status_lower for x in ["reserved", "placeholder"]):
        return "Reserved"
    else:
        return status.strip()


def compare_specs(index_specs: Dict, dir_specs: Dict) -> Tuple[List, List, List, List]:
    """Compare index and directory specs, return mismatches"""

    index_nums = set(index_specs.keys())
    dir_nums = set(dir_specs.keys())

    missing_in_index = sorted(dir_nums - index_nums)
    missing_in_dirs = sorted(index_nums - dir_nums)

    # Check for mismatches in existing specs
    name_mismatches = []
    status_mismatches = []

    common_nums = index_nums & dir_nums
    for num in common_nums:
        index_spec = index_specs[num]
        dir_spec = dir_specs[num]

        # Check name mismatch
        if dir_spec.get("title"):
            # Simple comparison - check if words overlap
            index_title = index_spec["title"].lower()
            dir_title = dir_spec["title"].lower()

            # Allow for minor variations but flag significant differences
            if not any(word in dir_title for word in index_title.split() if len(word) > 4):
                name_mismatches.append(
                    {
                        "num": num,
                        "index_title": index_spec["title"],
                        "dir_title": dir_spec["title"],
                    }
                )

        # Check status mismatch
        index_status = normalize_status(index_spec["status"])
        dir_status = normalize_status(dir_spec.get("status", ""))

        if dir_status != "Unknown" and index_status != dir_status:
            status_mismatches.append(
                {
                    "num": num,
                    "index_status": index_spec["status"],
                    "dir_status": dir_spec.get("status", "Not found"),
                    "index_normalized": index_status,
                    "dir_normalized": dir_status,
                }
            )

    return missing_in_index, missing_in_dirs, name_mismatches, status_mismatches


def generate_audit_report(
    missing_in_index: List[int],
    missing_in_dirs: List[int],
    name_mismatches: List[Dict],
    status_mismatches: List[Dict],
    index_specs: Dict,
    dir_specs: Dict,
    output_path: Path,
):
    """Generate comprehensive audit report"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    report = f"""# SPEC Index Audit Report

**Date**: {datetime.now().strftime("%Y-%m-%d")}
**Generated**: {timestamp}
**Auditor**: Developer D - Automated Script

---

## 📊 Executive Summary

| Metric | Count |
|--------|-------|
| **Total SPECs in Index** | {len(index_specs)} |
| **Total SPEC Directories** | {len(dir_specs)} |
| **SPECs Missing from Index** | {len(missing_in_index)} |
| **SPECs in Index but No Directory** | {len(missing_in_dirs)} |
| **Name Mismatches** | {len(name_mismatches)} |
| **Status Mismatches** | {len(status_mismatches)} |

---

## ✅ Corrections Needed

### 1. SPECs Missing from Index ({len(missing_in_index)})

These SPEC directories exist but are not listed in SPEC_INDEX.md:

"""

    for num in missing_in_index:
        dir_spec = dir_specs[num]
        report += f"| **SPEC-{num:03d}** | `{dir_spec['dir']}` | {dir_spec.get('title', 'No title found')} | {dir_spec.get('status', 'Status unknown')} |\n"

    report += "\n### 2. SPECs in Index but No Directory ({})\n\n".format(len(missing_in_dirs))
    report += "These SPECs are listed in SPEC_INDEX.md but directories don't exist:\n\n"
    report += "| SPEC | Title | Status | Notes |\n"
    report += "|------|-------|--------|-------|\n"

    for num in missing_in_dirs:
        index_spec = index_specs[num]
        report += f"| **SPEC-{num:03d}** | {index_spec['title']} | {index_spec['status']} | May be deprecated or consolidated |\n"

    if name_mismatches:
        report += f"\n### 3. Name Mismatches ({len(name_mismatches)})\n\n"
        report += "SPEC titles in index don't match README.md:\n\n"
        report += "| SPEC | Index Title | README Title |\n"
        report += "|------|-------------|--------------|\n"

        for mismatch in name_mismatches:
            report += f"| **SPEC-{mismatch['num']:03d}** | {mismatch['index_title']} | {mismatch['dir_title']} |\n"

    if status_mismatches:
        report += f"\n### 4. Status Mismatches ({len(status_mismatches)})\n\n"
        report += "SPEC statuses in index don't match README.md:\n\n"
        report += "| SPEC | Index Status | README Status | Action |\n"
        report += "|------|--------------|---------------|--------|\n"

        for mismatch in status_mismatches:
            action = "Update index" if mismatch["dir_normalized"] != "Unknown" else "Verify README"
            report += f"| **SPEC-{mismatch['num']:03d}** | {mismatch['index_status']} | {mismatch['dir_status']} | {action} |\n"

    # Critical findings
    report += "\n---\n\n## 🚨 Critical Findings\n\n"

    if missing_in_index:
        report += f"### Missing from Index ({len(missing_in_index)})\n"
        report += "**Action Required**: Add these SPECs to SPEC_INDEX.md\n\n"
        for num in missing_in_index[:5]:  # Show first 5
            dir_spec = dir_specs[num]
            report += f"- **SPEC-{num:03d}**: {dir_spec.get('title', 'No title')}\n"
        if len(missing_in_index) > 5:
            report += f"- ... and {len(missing_in_index) - 5} more\n"

    # Priority corrections
    report += "\n---\n\n## 📋 Recommended Corrections\n\n"
    report += "### Priority 1: Add Missing SPECs\n"
    report += "Add the following SPECs to SPEC_INDEX.md:\n\n"

    for num in missing_in_index[:10]:
        dir_spec = dir_specs[num]
        status = normalize_status(dir_spec.get("status", ""))
        report += f"| {num:03d} | {dir_spec.get('title', 'Title TBD')} | {status} | Phase TBD |\n"

    report += "\n### Priority 2: Update Status Mismatches\n"
    report += "Verify and update these statuses in SPEC_INDEX.md:\n\n"

    for mismatch in status_mismatches[:10]:
        report += f"- **SPEC-{mismatch['num']:03d}**: Index says '{mismatch['index_status']}', README says '{mismatch['dir_status']}'\n"

    report += "\n---\n\n## 📈 Statistics\n\n"

    # Count by status
    status_counts = {}
    for spec in index_specs.values():
        status = normalize_status(spec["status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    report += "### Completion Status (Index)\n\n"
    report += "| Status | Count |\n"
    report += "|--------|-------|\n"
    for status, count in sorted(status_counts.items()):
        report += f"| {status} | {count} |\n"

    report += "\n---\n\n## ✅ Next Steps\n\n"
    report += "1. Review missing SPECs and add to index\n"
    report += "2. Verify status mismatches and update index\n"
    report += "3. Check name mismatches and align titles\n"
    report += "4. Update SPEC_INDEX.md with corrections\n"
    report += "5. Regenerate this report after corrections\n"

    report += "\n---\n\n*Generated by: `scripts/audit_spec_index.py`*\n"
    report += f"*Report saved to: `{output_path}`*\n"

    output_path.write_text(report)
    print(f"✅ Audit report generated: {output_path}")


def main():
    specs_dir = Path("specs")
    index_path = specs_dir / "SPEC_INDEX.md"

    if not index_path.exists():
        print(f"❌ SPEC_INDEX.md not found at {index_path}")
        return

    print("🔍 Starting SPEC Index Audit...")
    print(f"   Reading from: {specs_dir}")
    print(f"   Index file: {index_path}\n")

    # Extract specs
    print("📖 Extracting SPECs from index...")
    index_specs = extract_spec_from_index(index_path)
    print(f"   Found {len(index_specs)} SPECs in index")

    print("\n📁 Extracting SPECs from directories...")
    dir_specs = extract_spec_from_directory(specs_dir)
    print(f"   Found {len(dir_specs)} SPEC directories")

    # Compare
    print("\n🔍 Comparing index vs directories...")
    missing_in_index, missing_in_dirs, name_mismatches, status_mismatches = compare_specs(index_specs, dir_specs)

    # Generate report
    output_path = specs_dir.parent / "governance" / "reports" / "SPEC_INDEX_AUDIT_NOV1_2025.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\n📝 Generating audit report...")
    generate_audit_report(
        missing_in_index, missing_in_dirs, name_mismatches, status_mismatches, index_specs, dir_specs, output_path
    )

    # Print summary
    print("\n" + "=" * 60)
    print("📊 AUDIT SUMMARY")
    print("=" * 60)
    print(f"✅ SPECs in index: {len(index_specs)}")
    print(f"📁 SPEC directories: {len(dir_specs)}")
    print(f"⚠️  Missing from index: {len(missing_in_index)}")
    print(f"⚠️  Missing directories: {len(missing_in_dirs)}")
    print(f"⚠️  Name mismatches: {len(name_mismatches)}")
    print(f"⚠️  Status mismatches: {len(status_mismatches)}")
    print(f"\n📄 Full report: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
