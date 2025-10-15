# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

#!/usr/bin/env python3
"""
wrk Load Test Results Parser
SPEC-099 Phase 1: Throughput Metrics Extraction

Parses wrk output and extracts key metrics for CI validation.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Optional


class WrkResultsParser:
    def __init__(self):
        self.metrics = {
            "duration_ms": 0,
            "requests": 0,
            "throughput_rps": 0.0,
            "latency": {"avg_ms": 0.0, "p50_ms": 0.0, "p95_ms": 0.0, "p99_ms": 0.0, "max_ms": 0.0},
            "errors": {"total": 0, "percent": 0.0},
        }

    def parse_output(self, output: str) -> Dict:
        """Parse wrk text output"""
        lines = output.strip().split("\n")

        for line in lines:
            # Duration
            if "Duration:" in line:
                match = re.search(r"Duration:\s+(\d+)\s+ms", line)
                if match:
                    self.metrics["duration_ms"] = int(match.group(1))

            # Requests
            if "Requests:" in line:
                match = re.search(r"Requests:\s+(\d+)", line)
                if match:
                    self.metrics["requests"] = int(match.group(1))

            # Throughput
            if "Throughput:" in line:
                match = re.search(r"Throughput:\s+([\d.]+)\s+req/s", line)
                if match:
                    self.metrics["throughput_rps"] = float(match.group(1))

            # Average Latency
            if "Avg Latency:" in line:
                match = re.search(r"Avg Latency:\s+([\d.]+)\s+ms", line)
                if match:
                    self.metrics["latency"]["avg_ms"] = float(match.group(1))

            # P50 Latency
            if "P50 Latency:" in line:
                match = re.search(r"P50 Latency:\s+([\d.]+)\s+ms", line)
                if match:
                    self.metrics["latency"]["p50_ms"] = float(match.group(1))

            # P95 Latency
            if "P95 Latency:" in line:
                match = re.search(r"P95 Latency:\s+([\d.]+)\s+ms", line)
                if match:
                    self.metrics["latency"]["p95_ms"] = float(match.group(1))

            # P99 Latency
            if "P99 Latency:" in line:
                match = re.search(r"P99 Latency:\s+([\d.]+)\s+ms", line)
                if match:
                    self.metrics["latency"]["p99_ms"] = float(match.group(1))

            # Max Latency
            if "Max Latency:" in line:
                match = re.search(r"Max Latency:\s+([\d.]+)\s+ms", line)
                if match:
                    self.metrics["latency"]["max_ms"] = float(match.group(1))

            # Errors
            if "Errors:" in line:
                match = re.search(r"Errors:\s+(\d+)\s+\(([\d.]+)%\)", line)
                if match:
                    self.metrics["errors"]["total"] = int(match.group(1))
                    self.metrics["errors"]["percent"] = float(match.group(2))

        return self.metrics

    def validate_slas(self, slas: Dict) -> Dict:
        """Check if metrics meet SLA requirements"""
        results = {"passed": True, "checks": []}

        checks = [
            {
                "name": "Throughput SLA",
                "target": f">= {slas.get('min_throughput_rps', 500)} req/s",
                "actual": f"{self.metrics['throughput_rps']:.2f} req/s",
                "passed": self.metrics["throughput_rps"] >= slas.get("min_throughput_rps", 500),
            },
            {
                "name": "P95 Latency SLA",
                "target": f"<= {slas.get('max_p95_latency_ms', 10)} ms",
                "actual": f"{self.metrics['latency']['p95_ms']:.2f} ms",
                "passed": self.metrics["latency"]["p95_ms"] <= slas.get("max_p95_latency_ms", 10),
            },
            {
                "name": "Error Rate SLA",
                "target": f"< {slas.get('max_error_percent', 0.1)}%",
                "actual": f"{self.metrics['errors']['percent']:.2f}%",
                "passed": self.metrics["errors"]["percent"] < slas.get("max_error_percent", 0.1),
            },
        ]

        for check in checks:
            results["checks"].append(check)
            if not check["passed"]:
                results["passed"] = False

        return results

    def generate_report(self, validation: Optional[Dict] = None) -> str:
        """Generate human-readable report"""
        report = []
        report.append("=" * 60)
        report.append("  wrk Load Test Results")
        report.append("=" * 60)
        report.append("")
        report.append(f"Duration:        {self.metrics['duration_ms']} ms")
        report.append(f"Total Requests:  {self.metrics['requests']}")
        report.append(f"Throughput:      {self.metrics['throughput_rps']:.2f} req/s")
        report.append("")
        report.append("Latency:")
        report.append(f"  Average:       {self.metrics['latency']['avg_ms']:.2f} ms")
        report.append(f"  P50:           {self.metrics['latency']['p50_ms']:.2f} ms")
        report.append(f"  P95:           {self.metrics['latency']['p95_ms']:.2f} ms")
        report.append(f"  P99:           {self.metrics['latency']['p99_ms']:.2f} ms")
        report.append(f"  Max:           {self.metrics['latency']['max_ms']:.2f} ms")
        report.append("")
        report.append(f"Errors:          {self.metrics['errors']['total']} ({self.metrics['errors']['percent']:.2f}%)")

        if validation:
            report.append("")
            report.append("=" * 60)
            report.append("  SLA Validation")
            report.append("=" * 60)
            for check in validation["checks"]:
                status = "✅ PASS" if check["passed"] else "❌ FAIL"
                report.append(f"{status} {check['name']}")
                report.append(f"      Target: {check['target']}")
                report.append(f"      Actual: {check['actual']}")

        report.append("")
        report.append("=" * 60)
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description="Parse wrk load test results and validate SLAs")
    parser.add_argument("input", type=Path, help="Path to wrk output file")
    parser.add_argument(
        "--sla-min-throughput", type=float, default=500.0, help="Minimum throughput req/s (default: 500)"
    )
    parser.add_argument(
        "--sla-max-p95-latency", type=float, default=10.0, help="Maximum P95 latency in ms (default: 10)"
    )
    parser.add_argument(
        "--sla-max-error-percent", type=float, default=0.1, help="Maximum error percentage (default: 0.1)"
    )
    parser.add_argument("--output", type=Path, help="Optional: Write JSON results to file")
    parser.add_argument("--validate", action="store_true", help="Validate against SLAs and exit with error if failed")

    args = parser.parse_args()

    # Read wrk output
    if args.input == Path("-"):
        output = sys.stdin.read()
    else:
        if not args.input.exists():
            print(f"❌ Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "r") as f:
            output = f.read()

    # Parse results
    parser = WrkResultsParser()
    metrics = parser.parse_output(output)

    # Validate SLAs if requested
    validation = None
    if args.validate:
        slas = {
            "min_throughput_rps": args.sla_min_throughput,
            "max_p95_latency_ms": args.sla_max_p95_latency,
            "max_error_percent": args.sla_max_error_percent,
        }
        validation = parser.validate_slas(slas)

    # Generate report
    report = parser.generate_report(validation)
    print(report)

    # Output JSON if requested
    if args.output:
        output_data = {"metrics": metrics, "validation": validation}
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"\n📄 Results saved to: {args.output}")

    # Exit with appropriate code
    if validation and not validation["passed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
