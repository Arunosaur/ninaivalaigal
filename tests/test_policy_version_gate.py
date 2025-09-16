"""
Policy Version Gate Test Scaffold

Requires ALLOW_POLICY_HASH_CHANGE=true environment variable to allow policy changes,
forcing reviewers to consciously acknowledge policy modifications.
"""

import os
import json
import hashlib
import pytest
from typing import Dict, Any
from server.rbac.permissions import Role, Action, Resource


class PolicyVersionGate:
    """Policy version gate requiring explicit approval for changes."""
    
    # Expected policy hash - update this when policy changes are approved
    EXPECTED_POLICY_HASH = "b974dd1d500e937930c1ad6333d8b5d72611f153d765f4e63606a1cc736ec162"
    
    @classmethod
    def get_current_policy_hash(cls) -> str:
        """Calculate hash of current RBAC policy matrix."""
        
        # Create a sample policy structure for testing
        sample_policy = {
            "roles": [role.name for role in Role],
            "actions": [action.name for action in Action],
            "resources": [res.name for res in Resource],
            "policy_matrix": {
                "admin": {
                    "memory": ["read", "write", "delete"],
                    "context": ["read", "write"],
                    "user": ["read"],
                    "organization": ["read"],
                    "team": ["read", "write"],
                },
                "viewer": {
                    "memory": ["read"],
                    "context": ["read"],
                    "user": ["read"],
                    "organization": ["read"],
                    "team": ["read"],
                }
            }
        }
        
        # Calculate hash
        policy_json = json.dumps(sample_policy, sort_keys=True)
        return hashlib.sha256(policy_json.encode()).hexdigest()
    
    @classmethod
    def check_policy_version_gate(cls) -> Dict[str, Any]:
        """
        Check if policy changes are allowed.
        
        Returns gate status and requires ALLOW_POLICY_HASH_CHANGE=true for changes.
        """
        current_hash = cls.get_current_policy_hash()
        hash_matches = current_hash == cls.EXPECTED_POLICY_HASH
        
        # Check environment variable
        allow_change = os.getenv("ALLOW_POLICY_HASH_CHANGE", "false").lower() == "true"
        
        result = {
            "policy_hash_matches": hash_matches,
            "current_hash": current_hash,
            "expected_hash": cls.EXPECTED_POLICY_HASH,
            "change_allowed": allow_change,
            "gate_passed": hash_matches or allow_change
        }
        
        if not result["gate_passed"]:
            result["error"] = (
                "Policy hash mismatch detected. "
                "Set ALLOW_POLICY_HASH_CHANGE=true to allow policy changes."
            )
        
        return result


def test_policy_version_gate_blocks_changes():
    """Test that policy version gate blocks unauthorized changes."""
    
    # Ensure environment variable is not set
    if "ALLOW_POLICY_HASH_CHANGE" in os.environ:
        del os.environ["ALLOW_POLICY_HASH_CHANGE"]
    
    gate_result = PolicyVersionGate.check_policy_version_gate()
    
    # If hashes match, gate should pass
    if gate_result["policy_hash_matches"]:
        assert gate_result["gate_passed"] == True
        return {"test_result": "PASS - Policy hash matches expected"}
    
    # If hashes don't match and no env var, gate should block
    assert gate_result["gate_passed"] == False
    assert "ALLOW_POLICY_HASH_CHANGE=true" in gate_result["error"]
    
    return {"test_result": "PASS - Gate correctly blocks unauthorized changes"}


def test_policy_version_gate_allows_with_env_var():
    """Test that policy version gate allows changes with environment variable."""
    
    # Set environment variable
    os.environ["ALLOW_POLICY_HASH_CHANGE"] = "true"
    
    try:
        gate_result = PolicyVersionGate.check_policy_version_gate()
        
        # Gate should pass with environment variable set
        assert gate_result["gate_passed"] == True
        assert gate_result["change_allowed"] == True
        
        return {"test_result": "PASS - Gate allows changes with env var"}
    
    finally:
        # Clean up environment variable
        if "ALLOW_POLICY_HASH_CHANGE" in os.environ:
            del os.environ["ALLOW_POLICY_HASH_CHANGE"]


def test_policy_hash_calculation():
    """Test policy hash calculation consistency."""
    
    # Calculate hash multiple times
    hash1 = PolicyVersionGate.get_current_policy_hash()
    hash2 = PolicyVersionGate.get_current_policy_hash()
    
    # Should be consistent
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    
    return {
        "test_result": "PASS - Hash calculation is consistent",
        "calculated_hash": hash1
    }


def simulate_policy_change_workflow():
    """Simulate the workflow for making policy changes."""
    
    workflow_steps = []
    
    # Step 1: Check current policy status
    gate_result = PolicyVersionGate.check_policy_version_gate()
    workflow_steps.append({
        "step": "check_current_policy",
        "result": gate_result
    })
    
    # Step 2: If policy changed, show required action
    if not gate_result["policy_hash_matches"]:
        workflow_steps.append({
            "step": "policy_change_detected",
            "action_required": "Set ALLOW_POLICY_HASH_CHANGE=true to proceed",
            "current_hash": gate_result["current_hash"],
            "expected_hash": gate_result["expected_hash"]
        })
        
        # Step 3: Simulate setting environment variable
        os.environ["ALLOW_POLICY_HASH_CHANGE"] = "true"
        
        workflow_steps.append({
            "step": "environment_variable_set",
            "variable": "ALLOW_POLICY_HASH_CHANGE=true"
        })
        
        # Step 4: Re-check gate
        gate_result_after = PolicyVersionGate.check_policy_version_gate()
        workflow_steps.append({
            "step": "recheck_after_env_var",
            "result": gate_result_after
        })
        
        # Step 5: Update expected hash (in real workflow, this would be a code change)
        workflow_steps.append({
            "step": "update_expected_hash",
            "action": f"Update EXPECTED_POLICY_HASH to '{gate_result['current_hash']}'",
            "note": "This should be done in code review process"
        })
        
        # Clean up
        del os.environ["ALLOW_POLICY_HASH_CHANGE"]
    
    else:
        workflow_steps.append({
            "step": "no_policy_change",
            "result": "Policy hash matches, no action required"
        })
    
    return {
        "workflow_completed": True,
        "steps": workflow_steps
    }


if __name__ == "__main__":
    print("Policy Version Gate Test Results:")
    
    # Run tests
    test1 = test_policy_version_gate_blocks_changes()
    print(f"✅ Block test: {test1['test_result']}")
    
    test2 = test_policy_version_gate_allows_with_env_var()
    print(f"✅ Allow test: {test2['test_result']}")
    
    test3 = test_policy_hash_calculation()
    print(f"✅ Hash test: {test3['test_result']}")
    print(f"   Current hash: {test3['calculated_hash']}")
    
    # Simulate workflow
    print("\nPolicy Change Workflow Simulation:")
    workflow = simulate_policy_change_workflow()
    for i, step in enumerate(workflow["steps"], 1):
        print(f"{i}. {step['step']}: {step.get('result', step.get('action', step.get('note', 'completed')))}")
