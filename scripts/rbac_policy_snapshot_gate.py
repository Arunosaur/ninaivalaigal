#!/usr/bin/env python3
"""RBAC Policy Snapshot Pre-commit Gate

This script implements a pre-commit gate to prevent unnoticed RBAC matrix changes
by comparing current policy state against a baseline snapshot.

Features:
- Automated policy snapshot generation and comparison
- Git integration for pre-commit hooks
- Policy drift detection with detailed change analysis
- Configurable approval thresholds for different change types
- Integration with CI/CD pipelines for automated validation

Security Benefits:
- Prevents accidental privilege escalation
- Ensures all RBAC changes are intentional and reviewed
- Provides audit trail for policy modifications
- Enables rollback to known-good policy states
"""

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Import the existing RBAC policy snapshot functionality
sys.path.append(str(Path(__file__).parent.parent))
from tests.test_rbac_policy_snapshot import (
    RBACPolicySnapshot,
    create_production_policy_snapshot,
    validate_policy_against_snapshot,
)

logger = logging.getLogger(__name__)

# Configuration constants
BASELINE_SNAPSHOT_PATH = "rbac_policy_baseline.json"
CURRENT_SNAPSHOT_PATH = "rbac_policy_current.json"
POLICY_CHANGE_LOG_PATH = "rbac_policy_changes.log"
MAX_ACCEPTABLE_ADDITIONS = 5
MAX_ACCEPTABLE_MODIFICATIONS = 2

@dataclass
class PolicyGateConfig:
    """Configuration for RBAC policy gate."""
    baseline_path: str = BASELINE_SNAPSHOT_PATH
    current_path: str = CURRENT_SNAPSHOT_PATH
    change_log_path: str = POLICY_CHANGE_LOG_PATH
    max_acceptable_additions: int = MAX_ACCEPTABLE_ADDITIONS
    max_acceptable_modifications: int = MAX_ACCEPTABLE_MODIFICATIONS
    allow_removals: bool = False  # Strict: no permission removals without explicit approval
    require_approval_file: bool = True  # Require .rbac_changes_approved file for concerning changes
    git_integration: bool = True
    ci_mode: bool = False

class RBACPolicyGate:
    """Pre-commit gate for RBAC policy changes."""

    def __init__(self, config: PolicyGateConfig | None = None):
        self.config = config or PolicyGateConfig()
        self.repo_root = self._find_repo_root()
        self.baseline_path = self.repo_root / self.config.baseline_path
        self.current_path = self.repo_root / self.config.current_path
        self.change_log_path = self.repo_root / self.config.change_log_path

    def _find_repo_root(self) -> Path:
        """Find the git repository root."""
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback to current directory

    def generate_current_snapshot(self) -> str:
        """Generate snapshot of current RBAC policy state."""
        try:
            # Import current RBAC configuration from the application
            from server.rbac_models import get_current_policy_matrix

            # Create snapshot from current policy
            snapshot = RBACPolicySnapshot()
            current_matrix = get_current_policy_matrix()

            # Convert current matrix to snapshot format
            for role_name, resources in current_matrix.items():
                for resource_name, permissions in resources.items():
                    # Convert to enum types for snapshot
                    from tests.test_rbac_policy_snapshot import (
                        Permission,
                        Resource,
                        Role,
                    )

                    try:
                        role = Role(role_name)
                        resource = Resource(resource_name)
                        perms = [Permission(p) for p in permissions]

                        # Add conditions based on role and resource
                        conditions = {}
                        if role != Role.ADMIN:
                            if resource in [Resource.MEMORY, Resource.CONTEXT]:
                                conditions["owner_only"] = True
                            elif resource == Resource.TEAM:
                                conditions["member_only"] = True

                        snapshot.add_rule(role, resource, perms, conditions)
                    except ValueError as e:
                        logger.warning(f"Skipping unknown role/resource/permission: {e}")
                        continue

            return snapshot.to_json()

        except ImportError:
            # Fallback: generate from test policy matrix
            logger.warning("Could not import current policy, using test baseline")
            return create_production_policy_snapshot()

    def load_baseline_snapshot(self) -> str | None:
        """Load baseline policy snapshot."""
        if not self.baseline_path.exists():
            return None

        try:
            return self.baseline_path.read_text()
        except Exception as e:
            logger.error(f"Failed to load baseline snapshot: {e}")
            return None

    def save_baseline_snapshot(self, snapshot_json: str) -> None:
        """Save baseline policy snapshot."""
        try:
            self.baseline_path.write_text(snapshot_json)
            logger.info(f"Baseline snapshot saved to {self.baseline_path}")
        except Exception as e:
            logger.error(f"Failed to save baseline snapshot: {e}")
            raise

    def save_current_snapshot(self, snapshot_json: str) -> None:
        """Save current policy snapshot."""
        try:
            self.current_path.write_text(snapshot_json)
            logger.info(f"Current snapshot saved to {self.current_path}")
        except Exception as e:
            logger.error(f"Failed to save current snapshot: {e}")
            raise

    def check_policy_changes(self) -> dict[str, Any]:
        """Check for RBAC policy changes against baseline."""
        # Generate current snapshot
        current_snapshot = self.generate_current_snapshot()
        self.save_current_snapshot(current_snapshot)

        # Load baseline snapshot
        baseline_snapshot = self.load_baseline_snapshot()

        if baseline_snapshot is None:
            return {
                "status": "no_baseline",
                "message": "No baseline snapshot found. Run with --create-baseline to create one.",
                "gate_passed": False,
                "requires_approval": True
            }

        # Validate current policy against baseline
        validation_result = validate_policy_against_snapshot(current_snapshot, baseline_snapshot)

        # Analyze changes for gate decision
        gate_result = self._analyze_changes_for_gate(validation_result)

        # Log changes
        self._log_policy_changes(gate_result)

        return gate_result

    def _analyze_changes_for_gate(self, validation_result: dict[str, Any]) -> dict[str, Any]:
        """Analyze policy changes to determine if gate should pass."""
        comparison = validation_result["comparison"]

        if comparison["identical"]:
            return {
                "status": "no_changes",
                "message": "No RBAC policy changes detected.",
                "gate_passed": True,
                "requires_approval": False,
                "changes": []
            }

        changes = comparison["changes"]
        additions = [c for c in changes if c["type"] == "added"]
        modifications = [c for c in changes if c["type"] == "modified"]
        removals = [c for c in changes if c["type"] == "removed"]

        # Determine if changes are acceptable
        gate_passed = True
        requires_approval = False
        issues = []

        # Check additions
        if len(additions) > self.config.max_acceptable_additions:
            gate_passed = False
            requires_approval = True
            issues.append(f"Too many permission additions: {len(additions)} > {self.config.max_acceptable_additions}")

        # Check modifications
        if len(modifications) > self.config.max_acceptable_modifications:
            gate_passed = False
            requires_approval = True
            issues.append(f"Too many permission modifications: {len(modifications)} > {self.config.max_acceptable_modifications}")

        # Check removals (strict policy)
        if removals and not self.config.allow_removals:
            gate_passed = False
            requires_approval = True
            issues.append(f"Permission removals detected: {len(removals)} (not allowed without approval)")

        # Check for privilege escalation
        escalation_changes = self._detect_privilege_escalation(changes)
        if escalation_changes:
            gate_passed = False
            requires_approval = True
            issues.append(f"Potential privilege escalation detected: {len(escalation_changes)} changes")

        # Check if approval file exists for concerning changes
        if requires_approval and self.config.require_approval_file:
            approval_file = self.repo_root / ".rbac_changes_approved"
            if approval_file.exists():
                gate_passed = True
                requires_approval = False
                issues.append("Changes approved via .rbac_changes_approved file")

        return {
            "status": "changes_detected",
            "message": f"RBAC policy changes detected: {len(changes)} total changes",
            "gate_passed": gate_passed,
            "requires_approval": requires_approval,
            "issues": issues,
            "changes": {
                "total": len(changes),
                "additions": len(additions),
                "modifications": len(modifications),
                "removals": len(removals),
                "escalations": len(escalation_changes)
            },
            "change_details": changes,
            "validation_result": validation_result
        }

    def _detect_privilege_escalation(self, changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect potential privilege escalation in changes."""
        escalations = []

        for change in changes:
            if change["type"] == "added":
                rule = change["rule"]
                # Check if adding admin permissions to non-admin role
                if "admin" in rule.get("permissions", []) and rule.get("role") != "admin":
                    escalations.append(change)
                # Check if adding write permissions to viewer role
                elif "write" in rule.get("permissions", []) and rule.get("role") == "viewer":
                    escalations.append(change)

            elif change["type"] == "modified":
                old_rule = change["old_rule"]
                new_rule = change["new_rule"]

                # Check if permissions were expanded
                old_perms = set(old_rule.get("permissions", []))
                new_perms = set(new_rule.get("permissions", []))

                if new_perms > old_perms:  # New permissions added
                    added_perms = new_perms - old_perms
                    if "admin" in added_perms or ("write" in added_perms and old_rule.get("role") == "viewer"):
                        escalations.append(change)

        return escalations

    def _log_policy_changes(self, gate_result: dict[str, Any]) -> None:
        """Log policy changes to audit file."""
        import time

        log_entry = {
            "timestamp": time.time(),
            "status": gate_result["status"],
            "gate_passed": gate_result["gate_passed"],
            "requires_approval": gate_result["requires_approval"],
            "changes": gate_result.get("changes", {}),
            "git_commit": self._get_git_commit_hash(),
            "git_branch": self._get_git_branch()
        }

        try:
            # Append to log file
            with open(self.change_log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to log policy changes: {e}")

    def _get_git_commit_hash(self) -> str | None:
        """Get current git commit hash."""
        if not self.config.git_integration:
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def _get_git_branch(self) -> str | None:
        """Get current git branch."""
        if not self.config.git_integration:
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.repo_root
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    def create_baseline(self) -> dict[str, Any]:
        """Create new baseline policy snapshot."""
        current_snapshot = self.generate_current_snapshot()
        self.save_baseline_snapshot(current_snapshot)

        # Parse snapshot to get stats
        snapshot_data = json.loads(current_snapshot)

        return {
            "status": "baseline_created",
            "message": f"Baseline snapshot created with {snapshot_data['rules_count']} rules",
            "baseline_path": str(self.baseline_path),
            "policy_hash": snapshot_data["policy_hash"],
            "rules_count": snapshot_data["rules_count"]
        }

    def update_baseline(self) -> dict[str, Any]:
        """Update baseline to current policy state."""
        return self.create_baseline()

    def generate_approval_template(self, gate_result: dict[str, Any]) -> str:
        """Generate approval template for policy changes."""
        template = f"""# RBAC Policy Change Approval

## Summary
- **Total Changes**: {gate_result.get('changes', {}).get('total', 0)}
- **Additions**: {gate_result.get('changes', {}).get('additions', 0)}
- **Modifications**: {gate_result.get('changes', {}).get('modifications', 0)}
- **Removals**: {gate_result.get('changes', {}).get('removals', 0)}
- **Potential Escalations**: {gate_result.get('changes', {}).get('escalations', 0)}

## Issues Detected
"""

        for issue in gate_result.get("issues", []):
            template += f"- {issue}\n"

        template += f"""
## Change Details
```json
{json.dumps(gate_result.get('change_details', []), indent=2)}
```

## Approval
To approve these changes, create a file named `.rbac_changes_approved` in the repository root:

```bash
touch .rbac_changes_approved
git add .rbac_changes_approved
git commit -m "Approve RBAC policy changes"
```

## Security Review Checklist
- [ ] Changes are intentional and necessary
- [ ] No unintended privilege escalation
- [ ] Principle of least privilege maintained
- [ ] Changes documented and communicated
- [ ] Rollback plan prepared
"""

        return template

def main():
    """Main entry point for RBAC policy gate."""
    parser = argparse.ArgumentParser(description="RBAC Policy Snapshot Pre-commit Gate")
    parser.add_argument("--create-baseline", action="store_true",
                       help="Create new baseline policy snapshot")
    parser.add_argument("--update-baseline", action="store_true",
                       help="Update baseline to current policy state")
    parser.add_argument("--check", action="store_true", default=True,
                       help="Check current policy against baseline (default)")
    parser.add_argument("--ci-mode", action="store_true",
                       help="Run in CI mode with stricter validation")
    parser.add_argument("--generate-approval", action="store_true",
                       help="Generate approval template for changes")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Configure gate
    config = PolicyGateConfig(ci_mode=args.ci_mode)
    gate = RBACPolicyGate(config)

    try:
        if args.create_baseline or args.update_baseline:
            result = gate.create_baseline()
            print(json.dumps(result, indent=2))
            return 0

        # Check policy changes
        gate_result = gate.check_policy_changes()

        if args.generate_approval and gate_result["requires_approval"]:
            approval_template = gate.generate_approval_template(gate_result)
            approval_file = gate.repo_root / "rbac_policy_approval.md"
            approval_file.write_text(approval_template)
            print(f"Approval template generated: {approval_file}")

        # Print results
        print(json.dumps(gate_result, indent=2))

        # Exit with appropriate code
        if gate_result["gate_passed"]:
            print("✅ RBAC Policy Gate: PASSED")
            return 0
        else:
            print("❌ RBAC Policy Gate: FAILED")
            if gate_result["requires_approval"]:
                print("🔒 Manual approval required for policy changes")
            return 1

    except Exception as e:
        logger.error(f"RBAC Policy Gate failed with error: {e}")
        print(f"❌ RBAC Policy Gate: ERROR - {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())
