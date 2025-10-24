#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Generate a human-readable diff report for API contract changes.

Usage:
    python generate-contract-diff.py --base origin/main --head HEAD --output contract-diff.md
"""

import argparse
import subprocess
from pathlib import Path
from typing import Dict, List

import yaml


class ContractDiffGenerator:
    """Generates markdown diff reports for OpenAPI contract changes."""

    def __init__(self, base_ref: str, head_ref: str):
        self.base_ref = base_ref
        self.head_ref = head_ref
        self.contracts_dir = Path("shared/contracts")

    def get_contract_files(self, ref: str) -> Dict[str, str]:
        """Get all OpenAPI contract files at a given git ref."""
        try:
            result = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", ref, str(self.contracts_dir)],
                capture_output=True,
                text=True,
                check=True,
            )
            files = [f for f in result.stdout.strip().split("\n") if f.endswith("openapi.yaml")]

            contracts = {}
            for file_path in files:
                try:
                    content = subprocess.run(
                        ["git", "show", f"{ref}:{file_path}"], capture_output=True, text=True, check=True
                    ).stdout
                    contracts[file_path] = content
                except subprocess.CalledProcessError:
                    pass

            return contracts
        except subprocess.CalledProcessError:
            return {}

    def parse_openapi(self, content: str) -> dict:
        """Parse OpenAPI YAML content."""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError:
            return {}

    def generate_diff(self, base_spec: dict, head_spec: dict, service: str) -> List[str]:
        """Generate diff lines for a service."""
        lines = []

        # Path changes
        base_paths = set(base_spec.get("paths", {}).keys())
        head_paths = set(head_spec.get("paths", {}).keys())

        new_paths = head_paths - base_paths
        removed_paths = base_paths - head_paths

        if new_paths:
            lines.append(f"### ✨ New Endpoints")
            for path in sorted(new_paths):
                methods = [
                    m.upper() for m in head_spec["paths"][path].keys() if m in ["get", "post", "put", "delete", "patch"]
                ]
                lines.append(f"- `{path}` ({', '.join(methods)})")

        if removed_paths:
            lines.append(f"### 🚨 Removed Endpoints")
            for path in sorted(removed_paths):
                lines.append(f"- `{path}`")

        # Schema changes
        base_schemas = set(base_spec.get("components", {}).get("schemas", {}).keys())
        head_schemas = set(head_spec.get("components", {}).get("schemas", {}).keys())

        new_schemas = head_schemas - base_schemas
        removed_schemas = base_schemas - head_schemas

        if new_schemas:
            lines.append(f"### ✨ New Schemas")
            for schema in sorted(new_schemas):
                lines.append(f"- `{schema}`")

        if removed_schemas:
            lines.append(f"### 🚨 Removed Schemas")
            for schema in sorted(removed_schemas):
                lines.append(f"- `{schema}`")

        return lines

    def generate_report(self) -> str:
        """Generate full markdown report."""
        base_contracts = self.get_contract_files(self.base_ref)
        head_contracts = self.get_contract_files(self.head_ref)

        report = ["# 📋 API Contract Changes\n"]
        report.append(f"**Base:** `{self.base_ref}`")
        report.append(f"**Head:** `{self.head_ref}`\n")

        has_changes = False

        for file_path in sorted(set(base_contracts.keys()) | set(head_contracts.keys())):
            service = file_path.split("/")[2]

            if file_path not in head_contracts:
                report.append(f"## 🚨 {service} (REMOVED)")
                report.append(f"Contract file removed: `{file_path}`\n")
                has_changes = True
                continue

            if file_path not in base_contracts:
                report.append(f"## ✨ {service} (NEW)")
                report.append(f"New contract added: `{file_path}`\n")
                has_changes = True
                continue

            base_spec = self.parse_openapi(base_contracts[file_path])
            head_spec = self.parse_openapi(head_contracts[file_path])

            diff_lines = self.generate_diff(base_spec, head_spec, service)

            if diff_lines:
                report.append(f"## 🔄 {service}")
                report.extend(diff_lines)
                report.append("")
                has_changes = True

        if not has_changes:
            report.append("✅ No contract changes detected.")

        return "\n".join(report)

    def save_report(self, output_path: str):
        """Generate and save report to file."""
        report = self.generate_report()
        Path(output_path).write_text(report)
        print(f"📊 Contract diff report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate contract diff report")
    parser.add_argument("--base", required=True, help="Base git ref")
    parser.add_argument("--head", required=True, help="Head git ref")
    parser.add_argument("--output", default="contract-diff.md", help="Output file path")

    args = parser.parse_args()

    generator = ContractDiffGenerator(args.base, args.head)
    generator.save_report(args.output)


if __name__ == "__main__":
    main()
