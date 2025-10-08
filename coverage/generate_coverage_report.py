#!/usr/bin/env python3
"""Generate comprehensive coverage report with dashboard."""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_coverage():
    """Run coverage analysis and generate reports."""
    print("🧪 Running comprehensive test suite with coverage...")

    # Run tests with coverage
    result = subprocess.run(
        [
            "python",
            "-m",
            "pytest",
            "--cov=server",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            "tests/",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("❌ Tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False

    print("✅ Tests completed successfully")
    print(result.stdout)
    return True


def generate_badge_data():
    """Generate coverage badge data."""
    try:
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)

        total_coverage = coverage_data["totals"]["percent_covered"]

        # Determine badge color
        if total_coverage >= 80:
            color = "brightgreen"
        elif total_coverage >= 60:
            color = "yellow"
        else:
            color = "red"

        badge_data = {
            "schemaVersion": 1,
            "label": "coverage",
            "message": f"{total_coverage:.1f}%",
            "color": color,
        }

        with open("coverage/badge.json", "w") as f:
            json.dump(badge_data, f, indent=2)

        print(f"📊 Coverage badge generated: {total_coverage:.1f}% ({color})")
        return total_coverage

    except FileNotFoundError:
        print("❌ Coverage JSON file not found")
        return 0


def generate_summary_report():
    """Generate summary coverage report."""
    try:
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)

        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_coverage": coverage_data["totals"]["percent_covered"],
            "total_lines": coverage_data["totals"]["num_statements"],
            "covered_lines": coverage_data["totals"]["covered_lines"],
            "missing_lines": coverage_data["totals"]["missing_lines"],
            "modules": {},
        }

        # Module breakdown
        for file_path, file_data in coverage_data["files"].items():
            if file_path.startswith("server/"):
                module_name = file_path.replace("server/", "").replace(".py", "")
                summary["modules"][module_name] = {
                    "coverage": file_data["summary"]["percent_covered"],
                    "lines": file_data["summary"]["num_statements"],
                    "covered": file_data["summary"]["covered_lines"],
                    "missing": file_data["summary"]["missing_lines"],
                }

        with open("coverage/summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        print("📋 Coverage summary generated")
        return summary

    except FileNotFoundError:
        print("❌ Coverage JSON file not found")
        return None


def generate_html_dashboard(summary):
    """Generate HTML dashboard."""
    if not summary:
        return

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Ninaivalaigal Code Coverage Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 5px; }}
        .coverage-high {{ background: #d4edda; }}
        .coverage-medium {{ background: #fff3cd; }}
        .coverage-low {{ background: #f8d7da; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; }}
        .progress {{ width: 100px; height: 20px; background: #e9ecef; border-radius: 10px; }}
        .progress-bar {{ height: 100%; border-radius: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Ninaivalaigal Code Coverage Dashboard</h1>
        <p>Generated: {summary['timestamp']}</p>
        <div class="metric coverage-{'high' if summary['total_coverage'] >= 80 else 'medium' if summary['total_coverage'] >= 60 else 'low'}">
            <strong>Total Coverage: {summary['total_coverage']:.1f}%</strong>
        </div>
        <div class="metric">
            <strong>Total Lines: {summary['total_lines']}</strong>
        </div>
        <div class="metric">
            <strong>Covered Lines: {summary['covered_lines']}</strong>
        </div>
        <div class="metric">
            <strong>Missing Lines: {summary['missing_lines']}</strong>
        </div>
    </div>

    <h2>📊 Module Coverage Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Module</th>
                <th>Coverage</th>
                <th>Lines</th>
                <th>Covered</th>
                <th>Missing</th>
                <th>Progress</th>
            </tr>
        </thead>
        <tbody>
"""

    # Sort modules by coverage percentage
    sorted_modules = sorted(summary["modules"].items(), key=lambda x: x[1]["coverage"], reverse=True)

    for module_name, module_data in sorted_modules:
        coverage_pct = module_data["coverage"]
        color = "#28a745" if coverage_pct >= 80 else "#ffc107" if coverage_pct >= 60 else "#dc3545"

        html_template += f"""
            <tr>
                <td><strong>{module_name}</strong></td>
                <td>{coverage_pct:.1f}%</td>
                <td>{module_data['lines']}</td>
                <td>{module_data['covered']}</td>
                <td>{module_data['missing']}</td>
                <td>
                    <div class="progress">
                        <div class="progress-bar" style="width: {coverage_pct}%; background-color: {color};"></div>
                    </div>
                </td>
            </tr>
        """

    html_template += (
        """
        </tbody>
    </table>

    <h2>🎯 Coverage Goals</h2>
    <ul>
        <li><strong>Target:</strong> 80% overall coverage</li>
        <li><strong>Critical modules:</strong> auth/, security/, memory/ should reach 100%</li>
        <li><strong>Current status:</strong> """
        + f"{summary['total_coverage']:.1f}% ({'✅ Target reached!' if summary['total_coverage'] >= 80 else '🔄 In progress'})"
        + """</li>
    </ul>

    <h2>📈 Next Steps</h2>
    <ul>
        <li>Fix circular import issues in server modules</li>
        <li>Add functional tests with running server</li>
        <li>Focus on critical modules for 100% coverage</li>
        <li>Add integration tests with test database</li>
        <li>Add performance benchmarks</li>
    </ul>

    <p><em>For detailed coverage report, see <a href="htmlcov/index.html">HTML Coverage Report</a></em></p>
</body>
</html>
"""
    )

    with open("coverage/dashboard.html", "w") as f:
        f.write(html_template)

    print("🌐 HTML dashboard generated: coverage/dashboard.html")


def main():
    """Main function."""
    print("🚀 Starting comprehensive coverage analysis...")

    # Create coverage directory
    os.makedirs("coverage", exist_ok=True)

    # Run coverage
    if not run_coverage():
        sys.exit(1)

    # Generate reports
    total_coverage = generate_badge_data()
    summary = generate_summary_report()
    generate_html_dashboard(summary)

    print(f"\n🎉 Coverage analysis complete!")
    print(f"📊 Total Coverage: {total_coverage:.1f}%")
    print(f"🌐 Dashboard: coverage/dashboard.html")
    print(f"📋 Summary: coverage/summary.json")
    print(f"🏷️  Badge: coverage/badge.json")

    # Check if target is met
    if total_coverage >= 80:
        print("✅ Coverage target (80%) achieved!")
        sys.exit(0)
    else:
        print(f"🔄 Coverage target not met. Need {80 - total_coverage:.1f}% more.")
        sys.exit(0)  # Don't fail CI, just inform


if __name__ == "__main__":
    main()
