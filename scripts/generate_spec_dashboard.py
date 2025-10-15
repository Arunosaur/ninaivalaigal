#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC

"""Generate comprehensive SPEC dashboard JSON with all SPECs for Docusaurus."""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def extract_spec_metadata(readme_path: Path):
    """Extract metadata from SPEC README.md file."""
    try:
        content = readme_path.read_text(encoding="utf-8")

        # Extract SPEC ID from directory name
        spec_dir = readme_path.parent.name
        match = re.match(r"(\d+)-(.+)", spec_dir)
        if match:
            spec_num, slug = match.groups()
            spec_id = f"SPEC-{spec_num}"
        else:
            spec_id = spec_dir

        # Extract title
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else spec_id

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(.+?)(?:\n|$)", content)
        status_raw = status_match.group(1).strip().split(",")[0] if status_match else "Unknown"
        status_raw = re.sub(r"[🚧✅📝⚠️]", "", status_raw).strip()

        # Normalize status to standard categories
        status_lower = status_raw.lower()
        if any(x in status_lower for x in ["complete", "implemented", "done"]):
            status = "Complete"
        elif any(x in status_lower for x in ["progress", "in-progress", "wip", "active"]):
            status = "In Progress"
        elif any(x in status_lower for x in ["planned", "ready"]):
            status = "Planned"
        elif any(x in status_lower for x in ["draft", "proposed"]):
            status = "Draft"
        elif any(x in status_lower for x in ["partial"]):
            status = "Partial"
        else:
            status = status_raw if status_raw != "Unknown" else "Not Started"

        # Extract phase
        phase_match = re.search(r"\*\*Phase\*\*:\s*(.+?)(?:\n|$)", content)
        phase_raw = phase_match.group(1).strip() if phase_match else None

        # If no phase found, try to infer from SPEC number
        if not phase_raw:
            if spec_num:
                num = int(spec_num)
                if num <= 20:
                    phase_raw = "1"  # Foundation
                elif num <= 50:
                    phase_raw = "2"  # Core Features
                elif num <= 90:
                    phase_raw = "3"  # Advanced Features
                elif num <= 110:
                    phase_raw = "4"  # Enterprise
                else:
                    phase_raw = "5"  # Scale & Polish
            else:
                phase_raw = "Unspecified"

        # Map phase abbreviations to full names
        phase_map = {
            "1": "Phase 1: Foundation",
            "2": "Phase 2: Core Features",
            "2A": "Phase 2A: Intelligence Foundation",
            "2B": "Phase 2B: Bulletproof Foundation",
            "3": "Phase 3: Advanced Features",
            "3A": "Phase 3A: Operational Maturity",
            "3B": "Phase 3B: Graph Intelligence",
            "4": "Phase 4: Enterprise",
            "5": "Phase 5: Scale & Polish",
        }

        # Clean and map phase - extract just the code part
        phase = phase_raw.split(",")[0].strip()
        phase_code_match = re.match(r"^(\d[AB]?)", phase)
        if phase_code_match:
            phase_code = phase_code_match.group(1)
            if phase_code in phase_map:
                phase = phase_map[phase_code]
        else:
            # Try direct match
            for key, full_name in phase_map.items():
                if key in phase or key == phase:
                    phase = full_name
                    break

        # Handle other common phase names
        if "Infrastructure" in phase_raw:
            phase = "Infrastructure"
        elif "Foundation" in phase_raw and phase == phase_raw:
            phase = "Phase 1: Foundation"
        elif "Testing" in phase_raw:
            phase = "Testing"
        elif "AI" in phase_raw:
            phase = "AI & Intelligence"
        elif "Frontend" in phase_raw:
            phase = "Frontend"
        elif "Security" in phase_raw:
            phase = "Security"

        # Extract owner
        owner_match = re.search(r"\*\*Owner\*\*:\s*(.+?)(?:\n|$)", content)
        owner = owner_match.group(1).strip() if owner_match else "unassigned"

        # Extract dates
        created_match = re.search(r"\*\*Created\*\*:\s*(.+?)(?:\n|$)", content)
        updated_match = re.search(r"\*\*Updated\*\*:\s*(.+?)(?:\n|$)", content)

        created = created_match.group(1).strip() if created_match else None
        updated = updated_match.group(1).strip() if updated_match else None

        # Parse dates properly - convert to ISO format
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Try parsing common formats
                from dateutil import parser

                parsed = parser.parse(date_str)
                return parsed.strftime("%Y-%m-%d")
            except Exception:  # noqa: B001
                return None

        created_iso = parse_date(created)
        updated_iso = parse_date(updated)

        # Generate start/end dates for Gantt
        if created_iso:
            start_date = created_iso
        elif updated_iso:
            start_date = updated_iso
        else:
            # Default to Q3 2025 for older specs
            start_date = "2025-07-01"

        if updated_iso:
            end_date = updated_iso
        elif "Complete" in status or "Implemented" in status:
            end_date = datetime.now().strftime("%Y-%m-%d")
        else:
            # For in-progress specs, estimate end date
            end_date = "2025-12-31"

        # Generate Docusaurus URL
        spec_url = f"/ninaivalaigal/specs/{spec_dir}"

        return {
            "id": spec_id,
            "title": title,
            "phase": phase,
            "status": status,
            "owner": owner,
            "created": created,
            "updated": updated,
            "start": start_date,
            "end": end_date,
            "path": str(readme_path),
            "url": spec_url,
        }
    except Exception as e:
        print(f"Error processing {readme_path}: {e}")
        return None


def main():
    """Generate spec_dashboard.json with all SPECs."""
    specs_dir = Path("specs")
    output_file = Path("docusaurus/static/spec_dashboard.json")

    # Find all SPEC documentation files (README.md or spec.md)
    readme_files = []

    # First, find all SPEC directories
    for spec_dir in sorted(specs_dir.glob("[0-9]*")):
        if not spec_dir.is_dir():
            continue

        # Check for README.md first, then spec.md, then any SPEC-*.md file
        readme = spec_dir / "README.md"
        if readme.exists():
            readme_files.append(readme)
        else:
            specmd = spec_dir / "spec.md"
            if specmd.exists():
                readme_files.append(specmd)
            else:
                # Look for SPEC-NNN-*.md files
                spec_mds = list(spec_dir.glob("SPEC-*.md"))
                if spec_mds:
                    readme_files.append(spec_mds[0])  # Take the first one

    # Exclude templates and archives
    readme_files = [
        f for f in readme_files if not any(x in str(f) for x in ["000-template", "archive", "templates", "_external"])
    ]

    print(f"Found {len(readme_files)} SPEC documentation files")

    # Extract metadata
    all_specs = []
    for readme in sorted(readme_files):
        metadata = extract_spec_metadata(readme)
        if metadata:
            all_specs.append(metadata)

    # Calculate summary statistics
    phase_completion = defaultdict(lambda: {"total": 0, "complete": 0})
    status_count = defaultdict(int)
    owner_count = defaultdict(int)

    gantt_data = []

    for spec in all_specs:
        # Phase stats
        phase = spec["phase"]
        phase_completion[phase]["total"] += 1
        if any(x in spec["status"] for x in ["Complete", "Implemented", "COMPLETE"]):
            phase_completion[phase]["complete"] += 1

        # Status stats
        status_count[spec["status"]] += 1

        # Owner stats
        owner_count[spec["owner"]] += 1

        # Gantt data (all specs with URLs)
        gantt_data.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "phase": spec["phase"],
                "status": spec["status"],
                "start": spec["start"],
                "end": spec["end"],
                "url": spec["url"],
            }
        )

    # Calculate percentages
    for phase_data in phase_completion.values():
        total = phase_data["total"]
        complete = phase_data["complete"]
        phase_data["percent_complete"] = round((complete / total * 100) if total > 0 else 0, 1)

    # Build dashboard JSON
    dashboard = {
        "generated_at": datetime.now().isoformat(),
        "project": "ninaivalaigal",
        "spec_count": len(all_specs),
        "summary": {
            "phase_completion": dict(phase_completion),
            "by_status": dict(status_count),
            "by_owner": dict(owner_count),
            "latest_updates": sorted(
                [{"id": s["id"], "title": s["title"], "updated": s["updated"]} for s in all_specs if s.get("updated")],
                key=lambda x: x["updated"],
                reverse=True,
            )[:10],
        },
        "gantt": gantt_data,
        "all_specs": all_specs,
    }

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    print(f"✅ Generated {output_file}")
    print(f"📊 Total SPECs: {len(all_specs)}")
    print(f"📈 Gantt entries: {len(gantt_data)}")
    print(f"📋 Phases: {len(phase_completion)}")


if __name__ == "__main__":
    main()
