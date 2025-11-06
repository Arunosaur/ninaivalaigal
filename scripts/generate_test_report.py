#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Test Report Generator

Generates comprehensive test reports including:
- Test coverage by module
- Test execution statistics
- Coverage trends
- Missing test files

Usage:
    python scripts/generate_test_report.py [--html] [--json] [--coverage]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))


def get_test_coverage() -> Dict[str, any]:
    """Get test coverage statistics"""
    root = Path(__file__).parent.parent

    try:
        # Run pytest with coverage
        result = subprocess.run(
            ["python", "-m", "pytest", "--cov=server", "--cov=services", "--cov-report=json", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
        )

        # Parse coverage JSON
        coverage_file = root / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, "r") as f:
                coverage_data = json.load(f)
            return coverage_data
    except Exception as e:
        print(f"⚠️  Could not generate coverage: {e}")

    return {}


def get_test_statistics() -> Dict[str, any]:
    """Get test execution statistics"""
    root = Path(__file__).parent.parent

    try:
        # Run pytest with JSON output
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd=root,
            capture_output=True,
            text=True,
        )

        # Count tests
        test_count = result.stdout.count("test_")
        file_count = result.stdout.count(".py::")

        return {
            "total_tests": test_count,
            "test_files": file_count,
        }
    except Exception as e:
        print(f"⚠️  Could not get test statistics: {e}")

    return {"total_tests": 0, "test_files": 0}


def find_missing_tests() -> List[str]:
    """Find source files without corresponding test files"""
    root = Path(__file__).parent.parent

    try:
        # Import the test coverage checker
        from check_test_coverage import find_test_file

        missing = []
        for source_file in root.rglob("*.py"):
            # Skip test files and scripts
            if "test" in str(source_file) or "scripts" in str(source_file):
                continue

            # Skip if in server/ or services/
            if "server/" in str(source_file) or "services/" in str(source_file):
                test_file = find_test_file(source_file, root)
                if not test_file:
                    missing.append(str(source_file.relative_to(root)))

        return missing
    except Exception as e:
        print(f"⚠️  Could not find missing tests: {e}")
        return []


def generate_html_report(data: Dict[str, any], output_file: Path):
    """Generate HTML test report"""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .stat {{ display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .missing {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>🧪 Test Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

    <div class="summary">
        <h2>Summary</h2>
        <div class="stat">
            <div>Total Tests</div>
            <div class="stat-value">{data.get('statistics', {}).get('total_tests', 0)}</div>
        </div>
        <div class="stat">
            <div>Test Files</div>
            <div class="stat-value">{data.get('statistics', {}).get('test_files', 0)}</div>
        </div>
    </div>

    <h2>Missing Test Files</h2>
    <div class="missing">
        <p>Files without corresponding tests: {len(data.get('missing_tests', []))}</p>
        <ul>
"""
    for missing in data.get("missing_tests", [])[:20]:  # Show first 20
        html += f"            <li>{missing}</li>\n"

    html += """
        </ul>
    </div>
</body>
</html>
"""

    with open(output_file, "w") as f:
        f.write(html)

    print(f"✅ HTML report generated: {output_file}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Generate comprehensive test report")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    parser.add_argument("--json", action="store_true", help="Generate JSON report")
    parser.add_argument("--coverage", action="store_true", help="Include coverage data")

    args = parser.parse_args()

    print("📊 Generating Test Report...")
    print("=" * 80)

    # Collect data
    data = {
        "timestamp": datetime.now().isoformat(),
        "statistics": get_test_statistics(),
        "missing_tests": find_missing_tests(),
    }

    if args.coverage:
        data["coverage"] = get_test_coverage()

    # Generate reports
    root = Path(__file__).parent.parent

    if args.json:
        json_file = root / "test_report.json"
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ JSON report generated: {json_file}")

    if args.html:
        html_file = root / "test_report.html"
        generate_html_report(data, html_file)

    # Print summary
    print("\n📊 Report Summary:")
    print(f"  Total Tests: {data['statistics']['total_tests']}")
    print(f"  Test Files: {data['statistics']['test_files']}")
    print(f"  Missing Tests: {len(data['missing_tests'])}")


if __name__ == "__main__":
    main()
