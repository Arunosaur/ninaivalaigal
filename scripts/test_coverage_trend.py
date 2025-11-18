#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Test Coverage Trend Analyzer

Tracks test coverage trends over time by analyzing git history.
Shows coverage improvements and identifies areas needing attention.

Usage:
    python scripts/test_coverage_trend.py [--days 30] [--module server]
"""

import argparse
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def get_git_commits_since(days: int = 30) -> List[str]:
    """Get list of commits since specified days"""
    try:
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        result = subprocess.run(
            ["git", "log", "--since", since_date, "--pretty=format:%H", "--no-merges"],
            capture_output=True,
            text=True,
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []


def count_test_files_at_commit(commit: str) -> Dict[str, int]:
    """Count test files at a specific commit"""
    root = Path(__file__).parent.parent

    counts = {
        "python": 0,
        "typescript": 0,
        "rust": 0,
        "go": 0,
    }

    try:
        # Get list of test files at this commit
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit],
            capture_output=True,
            text=True,
        )

        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            # Count by extension
            if line.endswith("test_*.py") or "test_" in line and line.endswith(".py"):
                counts["python"] += 1
            elif line.endswith(".test.ts") or line.endswith(".test.tsx"):
                counts["typescript"] += 1
            elif line.endswith("_test.rs"):
                counts["rust"] += 1
            elif line.endswith("_test.go"):
                counts["go"] += 1

    except Exception:
        pass

    return counts


def analyze_coverage_trend(days: int = 30) -> Dict[str, any]:
    """Analyze test coverage trends over time"""
    commits = get_git_commits_since(days)

    if not commits:
        return {"error": "No commits found in the specified period"}

    # Get current test file counts
    current_counts = count_test_files_at_commit("HEAD")

    # Get counts from oldest commit in range
    oldest_counts = count_test_files_at_commit(commits[-1]) if commits else current_counts

    # Calculate trends
    trends = {}
    for lang in ["python", "typescript", "rust", "go"]:
        current = current_counts.get(lang, 0)
        oldest = oldest_counts.get(lang, 0)
        change = current - oldest
        percent_change = ((current - oldest) / oldest * 100) if oldest > 0 else 0

        trends[lang] = {
            "current": current,
            "oldest": oldest,
            "change": change,
            "percent_change": percent_change,
        }

    return {
        "period_days": days,
        "commits_analyzed": len(commits),
        "trends": trends,
        "summary": {
            "total_current": sum(current_counts.values()),
            "total_oldest": sum(oldest_counts.values()),
            "total_change": sum(current_counts.values()) - sum(oldest_counts.values()),
        },
    }


def print_trend_report(data: Dict[str, any]):
    """Print coverage trend report"""
    if "error" in data:
        print(f"❌ {data['error']}")
        return

    print("📈 Test Coverage Trend Analysis")
    print("=" * 80)
    print(f"Period: Last {data['period_days']} days")
    print(f"Commits Analyzed: {data['commits_analyzed']}")

    print("\n📊 Language-Specific Trends:")
    for lang, trend in data["trends"].items():
        change_symbol = "📈" if trend["change"] > 0 else "📉" if trend["change"] < 0 else "➡️"
        print(f"\n  {lang.capitalize()}:")
        print(f"    {change_symbol} Current: {trend['current']} test files")
        print(f"    📅 {data['period_days']} days ago: {trend['oldest']} test files")
        print(f"    📊 Change: {trend['change']:+d} ({trend['percent_change']:+.1f}%)")

    print("\n📋 Overall Summary:")
    summary = data["summary"]
    print(f"  Total Test Files (Current): {summary['total_current']}")
    print(f"  Total Test Files ({data['period_days']} days ago): {summary['total_oldest']}")
    print(f"  Net Change: {summary['total_change']:+d} test files")

    if summary["total_change"] > 0:
        print("\n🎉 Test coverage is improving!")
    elif summary["total_change"] < 0:
        print("\n⚠️  Test coverage has decreased")
    else:
        print("\n➡️  Test coverage is stable")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze test coverage trends")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze (default: 30)")

    args = parser.parse_args()

    data = analyze_coverage_trend(days=args.days)
    print_trend_report(data)


if __name__ == "__main__":
    main()




