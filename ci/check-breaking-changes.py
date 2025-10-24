#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Check for breaking changes in API contracts between two git refs.

Usage:
    python check-breaking-changes.py --base origin/main --head HEAD
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

import yaml


class BreakingChangeDetector:
    """Detects breaking changes in OpenAPI specifications."""

    BREAKING_CHANGES = []

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
                    # File doesn't exist at this ref
                    pass

            return contracts
        except subprocess.CalledProcessError as e:
            print(f"Error getting contract files: {e}")
            return {}

    def parse_openapi(self, content: str) -> dict:
        """Parse OpenAPI YAML content."""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"Error parsing OpenAPI: {e}")
            return {}

    def detect_breaking_changes(self, base_spec: dict, head_spec: dict, service: str) -> List[str]:
        """Detect breaking changes between two OpenAPI specs."""
        changes = []

        # Check for removed paths
        base_paths = set(base_spec.get("paths", {}).keys())
        head_paths = set(head_spec.get("paths", {}).keys())
        removed_paths = base_paths - head_paths

        if removed_paths:
            for path in removed_paths:
                changes.append(f"🚨 BREAKING: Removed endpoint: {path}")

        # Check for removed/changed operations
        for path in base_paths & head_paths:
            base_operations = base_spec["paths"][path]
            head_operations = head_spec["paths"][path]

            base_methods = set(base_operations.keys())
            head_methods = set(head_operations.keys())
            removed_methods = base_methods - head_methods

            if removed_methods:
                for method in removed_methods:
                    changes.append(f"🚨 BREAKING: Removed method {method.upper()} on {path}")

            # Check for removed parameters
            for method in base_methods & head_methods:
                if method in ["get", "post", "put", "delete", "patch"]:
                    base_params = base_operations.get(method, {}).get("parameters", [])
                    head_params = head_operations.get(method, {}).get("parameters", [])

                    base_param_names = {p.get("name") for p in base_params if p.get("required", False)}
                    head_param_names = {p.get("name") for p in head_params if p.get("required", False)}

                    # New required parameters are breaking
                    new_required = head_param_names - base_param_names
                    if new_required:
                        for param in new_required:
                            changes.append(f"🚨 BREAKING: New required parameter '{param}' on {method.upper()} {path}")

        # Check for removed components/schemas
        base_schemas = set(base_spec.get("components", {}).get("schemas", {}).keys())
        head_schemas = set(head_spec.get("components", {}).get("schemas", {}).keys())
        removed_schemas = base_schemas - head_schemas

        if removed_schemas:
            for schema in removed_schemas:
                changes.append(f"🚨 BREAKING: Removed schema: {schema}")

        return changes

    def run(self) -> bool:
        """Run breaking change detection."""
        print(f"🔍 Checking for breaking changes between {self.base_ref} and {self.head_ref}")

        base_contracts = self.get_contract_files(self.base_ref)
        head_contracts = self.get_contract_files(self.head_ref)

        all_changes = []

        # Check each contract file
        for file_path in set(base_contracts.keys()) | set(head_contracts.keys()):
            service = file_path.split("/")[2]  # Extract service name

            if file_path not in head_contracts:
                all_changes.append(f"🚨 BREAKING: Removed contract file: {file_path}")
                continue

            if file_path not in base_contracts:
                print(f"✨ New contract added: {file_path}")
                continue

            base_spec = self.parse_openapi(base_contracts[file_path])
            head_spec = self.parse_openapi(head_contracts[file_path])

            changes = self.detect_breaking_changes(base_spec, head_spec, service)
            all_changes.extend(changes)

        if all_changes:
            print("\n❌ BREAKING CHANGES DETECTED:\n")
            for change in all_changes:
                print(f"  {change}")
            print("\n⚠️  Breaking changes require a new API version (v2, v3, etc.)")
            print("   Update the version in the contract path and maintain backward compatibility.")

            # Create marker file for CI
            Path("breaking-changes-detected").touch()
            return False
        else:
            print("\n✅ No breaking changes detected")
            return True


def main():
    parser = argparse.ArgumentParser(description="Check for breaking changes in API contracts")
    parser.add_argument("--base", required=True, help="Base git ref (e.g., origin/main)")
    parser.add_argument("--head", required=True, help="Head git ref (e.g., HEAD)")

    args = parser.parse_args()

    detector = BreakingChangeDetector(args.base, args.head)
    success = detector.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
