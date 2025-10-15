# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

#!/usr/bin/env python3
"""
Performance Regression Checker
SPEC-099 Phase 1: CI Performance Validation

Compares current benchmark results against baseline and fails if regression exceeds threshold.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional


class RegressionChecker:
    def __init__(self, threshold_percent: float = 10.0):
        self.threshold = threshold_percent / 100.0  # Convert to decimal
        self.regressions = []
        self.improvements = []

    def load_criterion_estimates(self, path: Path) -> Dict:
        """Load Criterion benchmark estimates JSON"""
        if not path.exists():
            raise FileNotFoundError(f"Estimates file not found: {path}")

        with open(path, "r") as f:
            return json.load(f)

    def compare_benchmarks(self, current: Dict, baseline: Dict) -> Dict:
        """Compare current vs baseline performance"""
        results = {"passed": True, "threshold_percent": self.threshold * 100, "comparisons": []}

        # Extract mean execution time from Criterion format
        current_mean = current.get("mean", {}).get("point_estimate", 0)
        baseline_mean = baseline.get("mean", {}).get("point_estimate", 0)

        if baseline_mean == 0:
            print("⚠️  Warning: Baseline mean is 0, skipping comparison")
            return results

        # Calculate change
        change = (current_mean - baseline_mean) / baseline_mean
        change_percent = change * 100

        comparison = {
            "current_ms": current_mean * 1000,  # Convert to ms
            "baseline_ms": baseline_mean * 1000,
            "change_percent": change_percent,
            "is_regression": change > self.threshold,
        }

        results["comparisons"].append(comparison)

        if comparison["is_regression"]:
            self.regressions.append(comparison)
            results["passed"] = False
            print(f"❌ REGRESSION: {change_percent:+.2f}% slower (threshold: {self.threshold * 100}%)")
        elif change < -0.05:  # >5% improvement
            self.improvements.append(comparison)
            print(f"✅ IMPROVEMENT: {change_percent:+.2f}% faster")
        else:
            print(f"✓  No significant change: {change_percent:+.2f}%")

        return results

    def generate_report(self) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 60)
        report.append("  Performance Regression Check Results")
        report.append("=" * 60)
        report.append("")

        if not self.regressions:
            report.append("✅ NO REGRESSIONS DETECTED")
        else:
            report.append(f"❌ {len(self.regressions)} REGRESSION(S) FOUND")
            report.append("")
            report.append("Regressions:")
            for reg in self.regressions:
                report.append(f"  - {reg['change_percent']:+.2f}% slower")
                report.append(f"    Current:  {reg['current_ms']:.2f} ms")
                report.append(f"    Baseline: {reg['baseline_ms']:.2f} ms")

        if self.improvements:
            report.append("")
            report.append(f"✅ {len(self.improvements)} Improvement(s):")
            for imp in self.improvements:
                report.append(f"  - {imp['change_percent']:+.2f}% faster")

        report.append("")
        report.append("=" * 60)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Check for performance regressions in benchmark results")
    parser.add_argument("--current", type=Path, required=True, help="Path to current benchmark estimates.json")
    parser.add_argument("--baseline", type=Path, required=True, help="Path to baseline benchmark estimates.json")
    parser.add_argument("--threshold", type=float, default=10.0, help="Regression threshold percentage (default: 10%%)")
    parser.add_argument("--output", type=Path, help="Optional: Write results to JSON file")

    args = parser.parse_args()

    print("🔍 Checking for performance regressions...\n")

    checker = RegressionChecker(threshold_percent=args.threshold)

    try:
        # Load benchmark data
        current = checker.load_criterion_estimates(args.current)
        baseline = checker.load_criterion_estimates(args.baseline)

        # Compare
        results = checker.compare_benchmarks(current, baseline)

        # Generate report
        report = checker.generate_report()
        print(report)

        # Save results if requested
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")

        # Exit with appropriate code
        sys.exit(0 if results["passed"] else 1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
