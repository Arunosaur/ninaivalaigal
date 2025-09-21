#!/usr/bin/env python3
"""
Simple Code Review Runner for mem0
Direct execution of code analysis without MCP server
"""

import json
import os
import sys
from pathlib import Path

# Add the server directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

try:
    from mcp_code_reviewer import CodeAnalyzer
except ImportError as e:
    print(f"Error importing CodeAnalyzer: {e}")
    print("Make sure mcp_code_reviewer.py is in the server directory")
    sys.exit(1)

def main():
    """Run code review on mem0 project"""
    project_root = Path(__file__).parent
    analyzer = CodeAnalyzer(str(project_root))

    print("🔍 Starting Comprehensive Code Review of mem0 Project")
    print("=" * 60)

    # Files to analyze
    files_to_analyze = [
        "server/main.py",
        "server/database.py",
        "server/auth.py",
        "server/mcp_server.py",
        "server/ai_integrations.py",
        "server/performance_monitor.py",
        "client/mem0",
        "client/mem0-universal.sh",
        "manage.sh"
    ]

    all_results = []

    for file_path in files_to_analyze:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"\n📁 Analyzing: {file_path}")
            try:
                result = analyzer.analyze_file(str(full_path))
                all_results.append(result)

                # Print summary for this file
                issues = result.issues
                if issues:
                    print(f"   ⚠️  Found {len(issues)} issues:")
                    severity_count = {}
                    for issue in issues:
                        severity_count[issue.severity] = severity_count.get(issue.severity, 0) + 1

                    for severity, count in severity_count.items():
                        print(f"      {severity.upper()}: {count}")
                else:
                    print("   ✅ No issues found")

            except Exception as e:
                print(f"   ❌ Error analyzing {file_path}: {e}")
                all_results.append({
                    "file_path": str(full_path),
                    "error": str(e)
                })
        else:
            print(f"   ⚠️  File not found: {file_path}")

    # Generate summary report
    print("\n" + "=" * 60)
    print("📊 CODE REVIEW SUMMARY REPORT")
    print("=" * 60)

    total_files = len(all_results)
    total_issues = 0
    severity_breakdown = {"high": 0, "medium": 0, "low": 0, "info": 0}
    category_breakdown = {}

    for result in all_results:
        if isinstance(result, dict) and "error" in result:
            continue

        issues = result.issues
        total_issues += len(issues)

        for issue in issues:
            severity_breakdown[issue.severity] += 1
            category_breakdown[issue.category] = category_breakdown.get(issue.category, 0) + 1

    print(f"📁 Total Files Analyzed: {total_files}")
    print(f"🔍 Total Issues Found: {total_issues}")
    print(f"🚨 High Severity: {severity_breakdown['high']}")
    print(f"⚠️  Medium Severity: {severity_breakdown['medium']}")
    print(f"ℹ️  Low Severity: {severity_breakdown['low']}")
    print(f"💡 Info: {severity_breakdown['info']}")

    print("\n📂 Category Breakdown:")
    for category, count in sorted(category_breakdown.items(), key=lambda x: x[1], reverse=True):
        print(f"   {category}: {count}")

    # Save detailed report
    report_file = project_root / "code_review_report.json"
    with open(report_file, 'w') as f:
        json.dump([result.__dict__ if hasattr(result, '__dict__') else result for result in all_results], f, indent=2, default=str)

    print(f"\n💾 Detailed report saved to: {report_file}")

    # Show top issues
    if total_issues > 0:
        print(f"\n🔥 TOP {min(10, total_issues)} ISSUES:")
        all_issues = []
        for result in all_results:
            if hasattr(result, 'issues'):
                all_issues.extend(result.issues)

        # Sort by severity (high first) and confidence
        severity_order = {"high": 4, "medium": 3, "low": 2, "info": 1}
        all_issues.sort(key=lambda x: (severity_order.get(x.severity, 0), x.confidence), reverse=True)

        for i, issue in enumerate(all_issues[:10], 1):
            print(f"{i:2d}. [{issue.severity.upper()}] {issue.title}")
            print(f"    📄 {issue.file_path}:{issue.line_number}")
            print(f"    💡 {issue.suggestion}")
            print()

    print("✅ Code review completed!")

if __name__ == "__main__":
    main()
