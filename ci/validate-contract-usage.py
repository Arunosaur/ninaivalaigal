#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Validate that services are using shared contracts instead of duplicate models.
Detects duplicate model definitions and reports contract compliance.

Usage:
    python ci/validate-contract-usage.py
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set


class ContractUsageValidator:
    """Validates contract usage across services."""

    def __init__(self):
        self.services_dir = Path("services")
        self.contracts_dir = Path("shared/contracts")
        self.duplicates = []
        self.missing_imports = []
        self.violations = []

    def get_contract_models(self) -> Dict[str, Set[str]]:
        """Extract all model names from shared contracts."""
        models_by_module = {}

        for model_file in self.contracts_dir.rglob("models.py"):
            module_path = str(model_file.relative_to(self.contracts_dir))
            models = self.extract_model_names(model_file)
            models_by_module[module_path] = models

        return models_by_module

    def extract_model_names(self, file_path: Path) -> Set[str]:
        """Extract Pydantic model class names from a Python file."""
        try:
            with open(file_path) as f:
                tree = ast.parse(f.read())

            models = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a Pydantic model (inherits from BaseModel)
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "BaseModel":
                            models.add(node.name)
                            break

            return models
        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return set()

    def check_service_models(self, service_path: Path, contract_models: Dict[str, Set[str]]):
        """Check a service for duplicate model definitions."""
        for py_file in service_path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            service_models = self.extract_model_names(py_file)

            # Check for duplicates
            for module_path, contract_model_set in contract_models.items():
                duplicates = service_models & contract_model_set
                if duplicates:
                    for model in duplicates:
                        self.duplicates.append(
                            {
                                "service": service_path.name,
                                "file": str(py_file.relative_to(service_path)),
                                "model": model,
                                "contract_module": module_path,
                            }
                        )

    def check_imports(self, service_path: Path):
        """Check if service imports from shared contracts."""
        has_contract_imports = False

        for py_file in service_path.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                with open(py_file) as f:
                    content = f.read()

                # Check for contract imports (both old and new patterns)
                if (
                    "from contracts." in content
                    or "import contracts." in content
                    or "from auth.v1.models" in content
                    or "from common.v1" in content
                    or "from business.v1" in content
                    or "from graph.v1" in content
                    or "from memory.v1" in content
                ):
                    has_contract_imports = True
                    break
            except Exception:
                pass

        if not has_contract_imports:
            self.missing_imports.append(service_path.name)

    def run(self):
        """Run validation checks."""
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔍 Validating Contract Usage Across Services")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")

        # Get all contract models
        print("📦 Extracting contract models...")
        contract_models = self.get_contract_models()
        total_contract_models = sum(len(models) for models in contract_models.values())
        print(f"   Found {total_contract_models} models in shared contracts")
        print("")

        # Check each service
        if not self.services_dir.exists():
            print("❌ Services directory not found")
            return False

        services = [d for d in self.services_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

        for service in services:
            print(f"🔍 Checking {service.name}...")
            self.check_service_models(service, contract_models)
            self.check_imports(service)

        print("")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📊 Validation Results")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")

        # Report duplicates
        if self.duplicates:
            print("⚠️  DUPLICATE MODELS DETECTED:")
            print("")
            for dup in self.duplicates:
                print(f"  Service: {dup['service']}")
                print(f"  File:    {dup['file']}")
                print(f"  Model:   {dup['model']}")
                print(f"  Contract: {dup['contract_module']}")
                print(f"  Action:  Remove local definition, import from contracts")
                print("")
        else:
            print("✅ No duplicate models found")
            print("")

        # Report missing imports
        if self.missing_imports:
            print("⚠️  SERVICES NOT USING SHARED CONTRACTS:")
            print("")
            for service in self.missing_imports:
                if service == "memory-service":
                    print(f"  - {service} (Rust service in rust-services/memory-service - uses serde, not Pydantic)")
                elif service == "graph-ai-service":
                    print(f"  - {service} (Placeholder directory - no implementation)")
                else:
                    print(f"  - {service}")
            print("  Note: Rust services use their own type system and do not need Python contracts.")
            print("")
            print("  Action: Update services to import from contracts.*")
            print("")
        else:
            print("✅ All services import from shared contracts")
            print("")

        # Summary
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📝 Summary")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("")
        print(f"  Shared Contract Models: {total_contract_models}")
        print(f"  Services Checked: {len(services)}")
        print(f"  Duplicate Models: {len(self.duplicates)}")
        print(f"  Services Missing Imports: {len(self.missing_imports)}")
        print("")

        # Check if there are actionable issues (exclude Rust and placeholder services)
        actionable_issues = [s for s in self.missing_imports if s not in ["memory-service", "graph-ai-service"]]

        if self.duplicates or actionable_issues:
            print("❌ CONTRACT COMPLIANCE: FAILED")
            print("")
            print("Next Steps:")
            print("1. Remove duplicate models from services")
            print("2. Import models from shared contracts")
            print("3. Update Dockerfiles to include shared/contracts")
            print("4. Re-run validation")
        elif not self.duplicates and not actionable_issues:
            print("✅ CONTRACT COMPLIANCE: PASSED")
            print("")
            print("All Python services are using shared contracts!")
            if self.missing_imports:
                print("Note: Rust and placeholder services excluded from validation.")
            print("")
            return False
        else:
            print("✅ CONTRACT COMPLIANCE: PASSED")
            print("")
            return True


def main():
    validator = ContractUsageValidator()
    success = validator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
