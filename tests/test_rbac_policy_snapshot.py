"""
RBAC Policy Snapshot Test

Creates RBAC policy snapshot with JSON serialization for policy drift detection
and compliance validation as requested in external code review.
"""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Role(Enum):
    """User roles in the system."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class Permission(Enum):
    """Permissions in the system."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class Resource(Enum):
    """Resources in the system."""

    MEMORY = "memory"
    CONTEXT = "context"
    USER = "user"
    ORGANIZATION = "organization"
    TEAM = "team"


@dataclass
class PolicyRule:
    """Individual RBAC policy rule."""

    role: Role
    resource: Resource
    permissions: list[Permission]
    conditions: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "role": self.role.value,
            "resource": self.resource.value,
            "permissions": [p.value for p in self.permissions],
            "conditions": self.conditions or {},
        }


class RBACPolicySnapshot:
    """RBAC policy snapshot for drift detection."""

    def __init__(self):
        self.rules: list[PolicyRule] = []
        self.version = "1.0.0"
        self.created_at = None
        self.policy_hash = None

    def add_rule(
        self,
        role: Role,
        resource: Resource,
        permissions: list[Permission],
        conditions: dict[str, Any] = None,
    ):
        """Add policy rule to snapshot."""
        rule = PolicyRule(role, resource, permissions, conditions)
        self.rules.append(rule)

    def generate_policy_matrix(self) -> dict[str, Any]:
        """Generate complete RBAC policy matrix."""

        # Define the complete policy matrix
        policy_matrix = {
            Role.ADMIN: {
                Resource.MEMORY: [
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.ADMIN,
                ],
                Resource.CONTEXT: [
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.ADMIN,
                ],
                Resource.USER: [
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.ADMIN,
                ],
                Resource.ORGANIZATION: [
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.ADMIN,
                ],
                Resource.TEAM: [
                    Permission.READ,
                    Permission.WRITE,
                    Permission.DELETE,
                    Permission.ADMIN,
                ],
            },
            Role.USER: {
                Resource.MEMORY: [Permission.READ, Permission.WRITE],
                Resource.CONTEXT: [Permission.READ, Permission.WRITE],
                Resource.USER: [Permission.READ],
                Resource.ORGANIZATION: [Permission.READ],
                Resource.TEAM: [Permission.READ, Permission.WRITE],
            },
            Role.VIEWER: {
                Resource.MEMORY: [Permission.READ],
                Resource.CONTEXT: [Permission.READ],
                Resource.USER: [Permission.READ],
                Resource.ORGANIZATION: [Permission.READ],
                Resource.TEAM: [Permission.READ],
            },
        }

        # Clear existing rules and rebuild from matrix
        self.rules.clear()

        for role, resources in policy_matrix.items():
            for resource, permissions in resources.items():
                # Add ownership conditions for non-admin roles
                conditions = {}
                if role != Role.ADMIN:
                    if resource in [Resource.MEMORY, Resource.CONTEXT]:
                        conditions["owner_only"] = True
                    elif resource == Resource.TEAM:
                        conditions["member_only"] = True

                self.add_rule(role, resource, permissions, conditions)

        return policy_matrix

    def to_json(self) -> str:
        """Serialize policy snapshot to JSON."""
        import time

        self.created_at = time.time()

        # Calculate policy hash for drift detection
        policy_content = json.dumps(
            [rule.to_dict() for rule in self.rules], sort_keys=True
        )
        self.policy_hash = hashlib.sha256(policy_content.encode()).hexdigest()

        snapshot_data = {
            "version": self.version,
            "created_at": self.created_at,
            "policy_hash": self.policy_hash,
            "rules_count": len(self.rules),
            "rules": [rule.to_dict() for rule in self.rules],
            "metadata": {
                "roles": [role.value for role in Role],
                "resources": [resource.value for resource in Resource],
                "permissions": [permission.value for permission in Permission],
            },
        }

        return json.dumps(snapshot_data, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, json_str: str) -> "RBACPolicySnapshot":
        """Deserialize policy snapshot from JSON."""
        data = json.loads(json_str)

        snapshot = cls()
        snapshot.version = data["version"]
        snapshot.created_at = data["created_at"]
        snapshot.policy_hash = data["policy_hash"]

        for rule_data in data["rules"]:
            role = Role(rule_data["role"])
            resource = Resource(rule_data["resource"])
            permissions = [Permission(p) for p in rule_data["permissions"]]
            conditions = rule_data.get("conditions")

            snapshot.add_rule(role, resource, permissions, conditions)

        return snapshot

    def compare_with(self, other: "RBACPolicySnapshot") -> dict[str, Any]:
        """Compare with another policy snapshot for drift detection."""

        # Quick hash comparison
        if self.policy_hash == other.policy_hash:
            return {"identical": True, "changes": []}

        # Detailed comparison
        changes = []

        # Convert rules to comparable format
        self_rules = {self._rule_key(rule): rule for rule in self.rules}
        other_rules = {self._rule_key(rule): rule for rule in other.rules}

        # Find added rules
        for key in other_rules:
            if key not in self_rules:
                changes.append({"type": "added", "rule": other_rules[key].to_dict()})

        # Find removed rules
        for key in self_rules:
            if key not in other_rules:
                changes.append({"type": "removed", "rule": self_rules[key].to_dict()})

        # Find modified rules
        for key in self_rules:
            if key in other_rules:
                if self_rules[key].to_dict() != other_rules[key].to_dict():
                    changes.append(
                        {
                            "type": "modified",
                            "old_rule": self_rules[key].to_dict(),
                            "new_rule": other_rules[key].to_dict(),
                        }
                    )

        return {
            "identical": False,
            "changes_count": len(changes),
            "changes": changes,
            "old_hash": self.policy_hash,
            "new_hash": other.policy_hash,
        }

    def _rule_key(self, rule: PolicyRule) -> str:
        """Generate unique key for rule comparison."""
        return f"{rule.role.value}:{rule.resource.value}"

    def validate_completeness(self) -> dict[str, Any]:
        """Validate that policy matrix is complete."""
        expected_combinations = len(Role) * len(Resource)
        actual_combinations = len(self.rules)

        missing_combinations = []
        existing_keys = {self._rule_key(rule) for rule in self.rules}

        for role in Role:
            for resource in Resource:
                key = f"{role.value}:{resource.value}"
                if key not in existing_keys:
                    missing_combinations.append(
                        {"role": role.value, "resource": resource.value}
                    )

        return {
            "complete": len(missing_combinations) == 0,
            "expected_combinations": expected_combinations,
            "actual_combinations": actual_combinations,
            "missing_combinations": missing_combinations,
            "coverage_percentage": (actual_combinations / expected_combinations) * 100,
        }


def test_rbac_policy_snapshot():
    """Test RBAC policy snapshot functionality."""

    # Create baseline policy snapshot
    baseline = RBACPolicySnapshot()
    baseline.generate_policy_matrix()

    # Serialize to JSON
    baseline_json = baseline.to_json()

    # Deserialize from JSON
    restored = RBACPolicySnapshot.from_json(baseline_json)

    # Compare baseline with itself (should be identical)
    comparison = baseline.compare_with(restored)

    # Validate completeness
    completeness = baseline.validate_completeness()

    # Create modified policy for drift testing
    modified = RBACPolicySnapshot()
    modified.generate_policy_matrix()

    # Add a new rule to simulate policy drift
    modified.add_rule(
        Role.USER,
        Resource.ORGANIZATION,
        [Permission.READ, Permission.WRITE],  # Added WRITE permission
        {"drift_test": True},
    )

    # Compare baseline with modified
    drift_comparison = baseline.compare_with(modified)

    return {
        "baseline_rules_count": len(baseline.rules),
        "baseline_hash": baseline.policy_hash,
        "serialization_test": comparison["identical"],
        "completeness": completeness,
        "drift_detected": not drift_comparison["identical"],
        "drift_changes": drift_comparison["changes_count"],
        "test_passed": (
            comparison["identical"]
            and completeness["complete"]
            and drift_comparison["changes_count"] > 0
        ),
    }


def create_production_policy_snapshot() -> str:
    """Create production RBAC policy snapshot."""
    snapshot = RBACPolicySnapshot()
    snapshot.generate_policy_matrix()
    return snapshot.to_json()


def validate_policy_against_snapshot(
    current_policy_json: str, baseline_json: str
) -> dict[str, Any]:
    """Validate current policy against baseline snapshot."""

    current = RBACPolicySnapshot.from_json(current_policy_json)
    baseline = RBACPolicySnapshot.from_json(baseline_json)

    comparison = baseline.compare_with(current)
    completeness = current.validate_completeness()

    # Determine if changes are acceptable
    acceptable_changes = []
    concerning_changes = []

    for change in comparison.get("changes", []):
        if change["type"] == "added":
            # New permissions might be acceptable
            acceptable_changes.append(change)
        elif change["type"] == "removed":
            # Removed permissions are concerning
            concerning_changes.append(change)
        elif change["type"] == "modified":
            # Modified permissions need review
            concerning_changes.append(change)

    return {
        "policy_valid": len(concerning_changes) == 0,
        "completeness": completeness,
        "comparison": comparison,
        "acceptable_changes": len(acceptable_changes),
        "concerning_changes": len(concerning_changes),
        "recommendation": "APPROVE"
        if len(concerning_changes) == 0
        else "REVIEW_REQUIRED",
    }


if __name__ == "__main__":
    # Run policy snapshot test
    test_results = test_rbac_policy_snapshot()
    print("RBAC Policy Snapshot Test Results:")
    print(json.dumps(test_results, indent=2))

    # Create production snapshot
    production_snapshot = create_production_policy_snapshot()
    print("\nProduction Policy Snapshot:")
    print(production_snapshot)
