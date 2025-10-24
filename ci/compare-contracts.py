#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Compare live OpenAPI contracts with stored contract specifications.
Identifies drift and generates detailed comparison report.

Usage:
    python ci/compare-contracts.py --output contract-comparison.md
"""

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import yaml


class ContractComparator:
    """Compares live and stored OpenAPI contracts."""

    def __init__(self):
        self.contracts_dir = Path("shared/contracts")
        self.live_dir = Path("shared/contracts-live")
        self.findings = []

    def load_yaml(self, file_path: Path) -> dict:
        """Load and parse YAML file."""
        try:
            with open(file_path) as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return {}

    def compare_paths(self, stored: dict, live: dict, service: str) -> List[str]:
        """Compare API paths between stored and live specs."""
        findings = []

        stored_paths = set(stored.get("paths", {}).keys())
        live_paths = set(live.get("paths", {}).keys())

        # New paths in live service
        new_paths = live_paths - stored_paths
        if new_paths:
            findings.append(f"### 📍 New Endpoints in Live Service")
            findings.append(f"These endpoints exist in the running service but not in the contract:")
            for path in sorted(new_paths):
                methods = [
                    m.upper() for m in live["paths"][path].keys() if m in ["get", "post", "put", "delete", "patch"]
                ]
                findings.append(f"- `{path}` ({', '.join(methods)})")
            findings.append("")

        # Missing paths in live service
        missing_paths = stored_paths - live_paths
        if missing_paths:
            findings.append(f"### ⚠️  Endpoints in Contract but NOT in Live Service")
            findings.append(f"These endpoints are documented but don't exist:")
            for path in sorted(missing_paths):
                findings.append(f"- `{path}`")
            findings.append("")

        # Method differences on common paths
        common_paths = stored_paths & live_paths
        for path in sorted(common_paths):
            stored_methods = set(
                m for m in stored["paths"][path].keys() if m in ["get", "post", "put", "delete", "patch"]
            )
            live_methods = set(m for m in live["paths"][path].keys() if m in ["get", "post", "put", "delete", "patch"])

            new_methods = live_methods - stored_methods
            removed_methods = stored_methods - live_methods

            if new_methods or removed_methods:
                findings.append(f"### 🔄 Method Changes on `{path}`")
                if new_methods:
                    findings.append(f"- **New methods:** {', '.join(m.upper() for m in new_methods)}")
                if removed_methods:
                    findings.append(f"- **Removed methods:** {', '.join(m.upper() for m in removed_methods)}")
                findings.append("")

        return findings

    def compare_schemas(self, stored: dict, live: dict, service: str) -> List[str]:
        """Compare schemas between stored and live specs."""
        findings = []

        stored_schemas = set(stored.get("components", {}).get("schemas", {}).keys())
        live_schemas = set(live.get("components", {}).get("schemas", {}).keys())

        new_schemas = live_schemas - stored_schemas
        if new_schemas:
            findings.append(f"### 📦 New Schemas in Live Service")
            for schema in sorted(new_schemas):
                findings.append(f"- `{schema}`")
            findings.append("")

        missing_schemas = stored_schemas - live_schemas
        if missing_schemas:
            findings.append(f"### ⚠️  Schemas in Contract but NOT in Live Service")
            for schema in sorted(missing_schemas):
                findings.append(f"- `{schema}`")
            findings.append("")

        return findings

    def compare_service(self, service_name: str, stored_path: Path, live_path: Path) -> Dict:
        """Compare contracts for a single service."""
        print(f"🔍 Comparing {service_name}...")

        stored_spec = self.load_yaml(stored_path)
        live_spec = self.load_yaml(live_path)

        if not stored_spec:
            return {"status": "error", "message": "Stored spec not found or invalid"}

        if not live_spec:
            return {"status": "error", "message": "Live spec not found or invalid"}

        findings = []
        findings.append(f"## 🔄 {service_name}")
        findings.append(f"**Stored Contract:** `{stored_path}`")
        findings.append(f"**Live Service:** `{live_path}`")
        findings.append("")

        # Compare paths
        path_findings = self.compare_paths(stored_spec, live_spec, service_name)
        findings.extend(path_findings)

        # Compare schemas
        schema_findings = self.compare_schemas(stored_spec, live_spec, service_name)
        findings.extend(schema_findings)

        if not path_findings and not schema_findings:
            findings.append("✅ **No drift detected** - Contract matches live service")
            findings.append("")

        return {"status": "ok", "findings": findings}

    def generate_report(self) -> str:
        """Generate full comparison report."""
        report = ["# 📊 Contract vs Live Service Comparison Report"]
        report.append("")
        report.append("**Generated:** $(date)")
        report.append("")
        report.append("This report compares stored API contracts with live running services.")
        report.append("")
        report.append("---")
        report.append("")

        # Service mappings
        services = [
            ("Core API", self.contracts_dir / "core-api/v1/openapi.yaml", self.live_dir / "core-api-live.yaml"),
            (
                "Business Service",
                self.contracts_dir / "business-service/v1/openapi.yaml",
                self.live_dir / "business-service-live.yaml",
            ),
            (
                "Admin/Vendor Service",
                self.contracts_dir / "admin-vendor-service/v1/openapi.yaml",
                self.live_dir / "admin-vendor-live.yaml",
            ),
            (
                "Graph/AI Service",
                self.contracts_dir / "graph-ai-service/v1/openapi.yaml",
                self.live_dir / "graph-service-live.yaml",
            ),
        ]

        all_ok = True

        for service_name, stored_path, live_path in services:
            if not live_path.exists():
                report.append(f"## ⏭️  {service_name}")
                report.append(f"**Status:** Live service not available or no OpenAPI endpoint")
                report.append("")
                continue

            result = self.compare_service(service_name, stored_path, live_path)

            if result["status"] == "error":
                report.append(f"## ❌ {service_name}")
                report.append(f"**Error:** {result['message']}")
                report.append("")
                all_ok = False
            else:
                report.extend(result["findings"])
                if any("New Endpoints" in f or "NOT in Live" in f for f in result["findings"]):
                    all_ok = False

        # Summary
        report.append("---")
        report.append("")
        report.append("## 📝 Summary")
        report.append("")

        if all_ok:
            report.append("✅ **All contracts match live services** - No action needed")
        else:
            report.append("⚠️  **Contract drift detected** - Review findings above and update contracts")
            report.append("")
            report.append("**Recommended Actions:**")
            report.append("1. For new endpoints: Add to stored contracts")
            report.append("2. For missing endpoints: Remove from contracts or implement in services")
            report.append("3. Re-extract contracts after updates: `./scripts/extract-live-contracts.sh`")

        return "\n".join(report)

    def run(self, output_file: str):
        """Run comparison and save report."""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📊 Comparing Contracts vs Live Services")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")

        report = self.generate_report()

        Path(output_file).write_text(report)
        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"✅ Comparison report saved to: {output_file}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def main():
    parser = argparse.ArgumentParser(description="Compare stored and live API contracts")
    parser.add_argument("--output", default="contract-comparison.md", help="Output file path")

    args = parser.parse_args()

    comparator = ContractComparator()
    comparator.run(args.output)


if __name__ == "__main__":
    main()
