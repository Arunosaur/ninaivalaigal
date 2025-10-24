# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

#!/usr/bin/env python3
"""
API Contract Validation Script
Ensures gRPC and REST API contracts remain compatible across versions
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import yaml


class ContractValidator:
    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_protobuf_syntax(self) -> bool:
        """Validate all .proto files compile successfully"""
        proto_files = list(self.contracts_dir.rglob("*.proto"))

        if not proto_files:
            self.errors.append("No .proto files found")
            return False

        # Try to find protoc in common locations
        protoc_paths = [
            "protoc",  # Try PATH first
            "/opt/homebrew/anaconda3/bin/protoc",  # Conda on Apple Silicon
            "/usr/local/bin/protoc",  # Homebrew on Intel
        ]

        protoc_cmd = None
        for path in protoc_paths:
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                protoc_cmd = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        if not protoc_cmd:
            self.errors.append("❌ protoc compiler not found. Install with: brew install protobuf")
            return False

        for proto_file in proto_files:
            try:
                # Use contracts root directory as proto_path for imports to work
                relative_path = proto_file.relative_to(self.contracts_dir)

                result = subprocess.run(
                    [
                        protoc_cmd,
                        f"--proto_path={self.contracts_dir}",
                        "--descriptor_set_out=/dev/null",
                        str(relative_path),
                    ],
                    cwd=self.contracts_dir,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"✅ {proto_file.name} compiles successfully")
            except subprocess.CalledProcessError as e:
                self.errors.append(f"❌ {proto_file.name} compilation failed: {e.stderr}")
                return False

        return True

    def check_breaking_changes(self) -> bool:
        """Check for breaking changes in proto schemas"""
        # Breaking change detection is now handled by ci/check-breaking-changes.py
        # which is called separately in the CI workflow.
        # This provides better separation of concerns and more detailed reporting.
        #
        # For local validation, run: python ci/check-breaking-changes.py --base origin/main --head HEAD
        return True

    def validate_naming_conventions(self) -> bool:
        """Ensure proto files follow naming conventions"""
        proto_files = list(self.contracts_dir.rglob("*.proto"))

        for proto_file in proto_files:
            content = proto_file.read_text()

            # Check package naming (should be service.v1 format)
            if "package" in content:
                package_line = [l for l in content.split("\n") if "package" in l][0]
                if ".v1" not in package_line:
                    self.warnings.append(f"⚠️  {proto_file.name} should use versioned package (e.g., graphops.v1)")

        return True

    def validate_openapi_schemas(self) -> bool:
        """Validate all OpenAPI YAML files"""
        openapi_files = list(self.contracts_dir.rglob("**/openapi.yaml"))

        if not openapi_files:
            print("ℹ️  No OpenAPI schemas found (optional)")
            return True

        for openapi_file in openapi_files:
            try:
                # Validate YAML syntax
                with open(openapi_file, "r") as f:
                    spec = yaml.safe_load(f)

                # Basic OpenAPI 3.0 validation
                if "openapi" not in spec:
                    self.errors.append(f"❌ {openapi_file.name} missing 'openapi' field")
                    return False

                if not spec["openapi"].startswith("3.0"):
                    self.warnings.append(f"⚠️  {openapi_file.name} should use OpenAPI 3.0")

                # Required fields
                required_fields = ["info", "paths"]
                for field in required_fields:
                    if field not in spec:
                        self.errors.append(f"❌ {openapi_file.name} missing required field: {field}")
                        return False

                # Check info section
                if "info" in spec:
                    info_required = ["title", "version"]
                    for field in info_required:
                        if field not in spec["info"]:
                            self.errors.append(f"❌ {openapi_file.name} info section missing: {field}")
                            return False

                # Check for health endpoint
                if "paths" in spec and "/health" not in spec["paths"]:
                    self.warnings.append(f"⚠️  {openapi_file.name} should include /health endpoint")

                service_name = openapi_file.parent.parent.name
                print(f"✅ {service_name}/openapi.yaml is valid")

            except yaml.YAMLError as e:
                self.errors.append(f"❌ {openapi_file.name} invalid YAML: {e}")
                return False
            except Exception as e:
                self.errors.append(f"❌ {openapi_file.name} validation error: {e}")
                return False

        return True

    def generate_report(self) -> Dict:
        """Generate validation report"""
        return {"passed": len(self.errors) == 0, "errors": self.errors, "warnings": self.warnings}


def main():
    contracts_dir = Path(__file__).parent.parent / "shared" / "contracts"

    validator = ContractValidator(contracts_dir)

    print("🔍 Validating API Contracts...\n")

    # Run validations
    print("📝 Validating Protocol Buffers...")
    syntax_ok = validator.validate_protobuf_syntax()
    breaking_ok = validator.check_breaking_changes()
    naming_ok = validator.validate_naming_conventions()

    print("\n📝 Validating OpenAPI Schemas...")
    openapi_ok = validator.validate_openapi_schemas()

    # Generate report
    report = validator.generate_report()

    print("\n" + "=" * 50)
    if report["passed"]:
        print("✅ API Contract Validation PASSED")
    else:
        print("❌ API Contract Validation FAILED")
    print("=" * 50)

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  {error}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  {warning}")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
