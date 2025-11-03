#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Monthly SPEC Status Report Generator
Generates comprehensive monthly status report with trends and recommendations
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def extract_spec_stats(index_path: Path) -> Dict:
    """Extract statistics from SPEC_INDEX.md"""
    content = index_path.read_text()

    stats = {
        "total": 0,
        "complete": 0,
        "in_progress": 0,
        "planned": 0,
        "partial": 0,
        "deprecated": 0,
        "reserved": 0,
        "reference": 0,
    }

    # Pattern to match table rows: | 027 | Title | Status | Phase |
    pattern = r"^\s*\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|"

    for line in content.split("\n"):
        match = re.match(pattern, line)
        if match:
            stats["total"] += 1
            status = match.group(3).strip().lower()

            # Count by status
            if any(x in status for x in ["complete", "✅", "done", "finished"]):
                stats["complete"] += 1
            elif any(x in status for x in ["in progress", "🔄", "🚧", "active"]):
                stats["in_progress"] += 1
            elif any(x in status for x in ["planned", "📋", "proposed", "scheduled"]):
                stats["planned"] += 1
            elif any(x in status for x in ["partial", "🔄"]):
                stats["partial"] += 1
            elif any(x in status for x in ["deprecated", "🗑️", "❌"]):
                stats["deprecated"] += 1
            elif any(x in status for x in ["reserved"]):
                stats["reserved"] += 1
            elif any(x in status for x in ["reference", "📚", "template"]):
                stats["reference"] += 1

    return stats


def read_previous_report(month: str, year: str) -> Optional[Dict]:
    """Read previous month's report if available"""
    prev_month = int(month) - 1
    prev_year = year

    if prev_month == 0:
        prev_month = 12
        prev_year = str(int(year) - 1)

    report_path = Path(f"governance/reports/SPEC_STATUS_MONTHLY_{prev_year}-{prev_month:02d}.md")

    if report_path.exists():
        content = report_path.read_text()
        # Extract stats from previous report
        # This is a simplified extraction - could be enhanced
        return None  # Placeholder for now
    return None


def calculate_health_score(stats: Dict) -> int:
    """Calculate health score based on various metrics"""
    score = 0

    # Completion rate (40 points max)
    if stats["total"] > 0:
        completion_rate = (stats["complete"] / stats["total"]) * 100
        score += min(40, int(completion_rate * 0.4))

    # In progress ratio (20 points max)
    if stats["total"] > 0:
        in_progress_ratio = (stats["in_progress"] / stats["total"]) * 100
        # Ideal: 10-15% in progress
        if 10 <= in_progress_ratio <= 15:
            score += 20
        elif 5 <= in_progress_ratio <= 20:
            score += 15
        else:
            score += 10

    # Low deprecated count (20 points max)
    deprecated_ratio = (stats["deprecated"] / max(1, stats["total"])) * 100
    if deprecated_ratio < 5:
        score += 20
    elif deprecated_ratio < 10:
        score += 15
    else:
        score += 10

    # Low reserved/placeholder count (20 points max)
    reserved_ratio = ((stats["reserved"] + stats["reference"]) / max(1, stats["total"])) * 100
    if reserved_ratio < 10:
        score += 20
    elif reserved_ratio < 20:
        score += 15
    else:
        score += 10

    return min(100, score)


def generate_monthly_report(stats: Dict, health_score: int, month: str, year: str) -> str:
    """Generate monthly status report"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    completion_rate = (stats["complete"] / max(1, stats["total"])) * 100
    in_progress_rate = (stats["in_progress"] / max(1, stats["total"])) * 100

    report = f"""# SPEC Status Monthly Report - {year}-{month}

**Generated**: {timestamp}
**Period**: {year}-{month}
**Health Score**: {health_score}/100

---

## 📊 Executive Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total SPECs** | {stats['total']} | 100% |
| **✅ Complete** | {stats['complete']} | {completion_rate:.1f}% |
| **🚧 In Progress** | {stats['in_progress']} | {in_progress_rate:.1f}% |
| **📋 Planned** | {stats['planned']} | {(stats['planned']/max(1,stats['total'])*100):.1f}% |
| **🔄 Partial** | {stats['partial']} | {(stats['partial']/max(1,stats['total'])*100):.1f}% |
| **🗑️ Deprecated** | {stats['deprecated']} | {(stats['deprecated']/max(1,stats['total'])*100):.1f}% |

### Health Score Breakdown

**Current Score**: {health_score}/100

- **Completion Rate**: {completion_rate:.1f}% ({min(40, int(completion_rate * 0.4))}/40 points)
- **In Progress Ratio**: {in_progress_rate:.1f}% (optimal: 10-15%)
- **Deprecated Ratio**: {(stats['deprecated']/max(1,stats['total'])*100):.1f}% (optimal: <5%)
- **Reserved/Reference**: {((stats['reserved']+stats['reference'])/max(1,stats['total'])*100):.1f}%

---

## 📈 Status Distribution

```
Complete:     {'█' * int(stats['complete'] / max(1, stats['total'] / 50))}
In Progress:  {'█' * int(stats['in_progress'] / max(1, stats['total'] / 50))}
Planned:      {'█' * int(stats['planned'] / max(1, stats['total'] / 50))}
Partial:      {'█' * int(stats['partial'] / max(1, stats['total'] / 50))}
Deprecated:   {'█' * int(stats['deprecated'] / max(1, stats['total'] / 50))}
```

---

## 🎯 Key Metrics

### Completion Rate
- **Current**: {completion_rate:.1f}%
- **Target**: 80%+
- **Gap**: {max(0, 80 - completion_rate):.1f} percentage points

### Work in Progress
- **Current**: {stats['in_progress']} SPECs
- **Optimal Range**: {int(stats['total'] * 0.10)}-{int(stats['total'] * 0.15)} SPECs
- **Status**: {"✅ Within range" if 10 <= in_progress_rate <= 15 else "⚠️ Outside optimal range"}

### Pipeline Health
- **Complete**: {stats['complete']}
- **In Progress**: {stats['in_progress']}
- **Planned**: {stats['planned']}
- **Pipeline Ratio**: {stats['complete']}/{stats['in_progress']} (complete:in-progress)

---

## 📋 Recommendations

"""

    # Add recommendations based on metrics
    if completion_rate < 70:
        report += f"- **Priority**: Increase completion rate from {completion_rate:.1f}% to 80%+\n"
        report += (
            f"  - Focus on completing {max(0, int((80 - completion_rate) / 100 * stats['total']))} planned SPECs\n"
        )

    if stats["in_progress"] < stats["total"] * 0.10:
        report += f"- **Priority**: Increase active development (only {stats['in_progress']} SPECs in progress)\n"
        report += f"  - Target: {int(stats['total'] * 0.12)} SPECs in progress\n"

    if stats["in_progress"] > stats["total"] * 0.20:
        report += f"- **Warning**: Too many SPECs in progress ({stats['in_progress']})\n"
        report += f"  - Consider pausing some to focus on completion\n"

    if stats["partial"] > 0:
        report += f"- **Action**: {stats['partial']} partial SPECs need completion\n"
        report += f"  - Review and prioritize completion\n"

    report += f"""
---

## 🔄 Changes from Previous Month

*Note: Historical comparison will be available after next month's report*

---

## 📝 Next Actions

1. Review SPECs in progress for blockers
2. Prioritize completion of partial SPECs
3. Plan new SPEC work based on pipeline capacity
4. Update status definitions if needed

---

## 📚 Related Documents

- [SPEC Status Definitions](../specs/SPEC_STATUS_DEFINITIONS.md)
- [SPEC Index](../specs/SPEC_INDEX.md)
- [Monthly Audit Automation Plan](./MONTHLY_AUDIT_AUTOMATION_PLAN.md)

---

*Generated by: `scripts/generate_monthly_spec_report.py`*
*Automated monthly report - Part of SPEC governance process*

"""

    return report


def main():
    """Generate monthly SPEC status report"""
    project_root = Path(__file__).parent.parent
    index_path = project_root / "specs" / "SPEC_INDEX.md"

    if not index_path.exists():
        print(f"❌ SPEC_INDEX.md not found at {index_path}")
        return 1

    print("📊 Generating Monthly SPEC Status Report...")
    print(f"   Reading from: {index_path}\n")

    # Extract stats
    print("📖 Extracting SPEC statistics...")
    stats = extract_spec_stats(index_path)
    print(f"   Found {stats['total']} SPECs")

    # Calculate health score
    print("🎯 Calculating health score...")
    health_score = calculate_health_score(stats)
    print(f"   Health Score: {health_score}/100")

    # Generate report
    now = datetime.now()
    month = f"{now.month:02d}"
    year = str(now.year)

    print(f"\n📝 Generating report for {year}-{month}...")
    report = generate_monthly_report(stats, health_score, month, year)

    # Save report
    output_dir = project_root / "governance" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"SPEC_STATUS_MONTHLY_{year}-{month}.md"

    output_path.write_text(report)
    print(f"✅ Report generated: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 MONTHLY REPORT SUMMARY")
    print("=" * 60)
    print(f"Total SPECs: {stats['total']}")
    print(f"✅ Complete: {stats['complete']} ({stats['complete']/max(1,stats['total'])*100:.1f}%)")
    print(f"🚧 In Progress: {stats['in_progress']} ({stats['in_progress']/max(1,stats['total'])*100:.1f}%)")
    print(f"📋 Planned: {stats['planned']} ({stats['planned']/max(1,stats['total'])*100:.1f}%)")
    print(f"Health Score: {health_score}/100")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
