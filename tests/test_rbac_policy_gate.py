"""Tests for RBAC Policy Snapshot Pre-commit Gate."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from scripts.rbac_policy_snapshot_gate import (
    RBACPolicyGate,
    PolicyGateConfig
)


class TestPolicyGateConfig:
    """Test policy gate configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PolicyGateConfig()
        
        assert config.max_acceptable_additions == 5
        assert config.max_acceptable_modifications == 2
        assert config.allow_removals is False
        assert config.require_approval_file is True
        assert config.git_integration is True
        assert config.ci_mode is False
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PolicyGateConfig(
            max_acceptable_additions=10,
            allow_removals=True,
            ci_mode=True
        )
        
        assert config.max_acceptable_additions == 10
        assert config.allow_removals is True
        assert config.ci_mode is True


class TestRBACPolicyGate:
    """Test RBAC policy gate functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = PolicyGateConfig(
            baseline_path=str(self.temp_dir / "baseline.json"),
            current_path=str(self.temp_dir / "current.json"),
            change_log_path=str(self.temp_dir / "changes.log"),
            git_integration=False  # Disable git for tests
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    @patch('scripts.rbac_policy_snapshot_gate.Path.cwd')
    def test_gate_initialization(self, mock_cwd):
        """Test gate initializes properly."""
        mock_cwd.return_value = self.temp_dir
        
        gate = RBACPolicyGate(self.config)
        
        assert gate.config == self.config
        assert gate.repo_root == self.temp_dir
    
    def test_create_baseline(self):
        """Test baseline creation."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Mock snapshot generation
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_snapshot = '{"test": "snapshot", "rules_count": 5, "policy_hash": "test_hash"}'
                mock_gen.return_value = mock_snapshot
                
                result = gate.create_baseline()
                
                assert result["status"] == "baseline_created"
                assert result["rules_count"] == 5
                assert gate.baseline_path.exists()
                assert gate.baseline_path.read_text() == mock_snapshot
    
    def test_no_baseline_scenario(self):
        """Test behavior when no baseline exists."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_gen.return_value = '{"test": "current"}'
                
                result = gate.check_policy_changes()
                
                assert result["status"] == "no_baseline"
                assert result["gate_passed"] is False
                assert result["requires_approval"] is True
    
    def test_no_changes_scenario(self):
        """Test behavior when no policy changes exist."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Create baseline
            baseline_snapshot = '{"rules": [], "policy_hash": "test_hash"}'
            gate.baseline_path.write_text(baseline_snapshot)
            
            # Mock current snapshot to be identical
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_gen.return_value = baseline_snapshot
                
                with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                    mock_validate.return_value = {
                        "comparison": {"identical": True, "changes": []},
                        "completeness": {"complete": True}
                    }
                    
                    result = gate.check_policy_changes()
                    
                    assert result["status"] == "no_changes"
                    assert result["gate_passed"] is True
                    assert result["requires_approval"] is False
    
    def test_acceptable_changes_scenario(self):
        """Test behavior with acceptable policy changes."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Create baseline
            baseline_snapshot = '{"rules": [], "policy_hash": "baseline_hash"}'
            gate.baseline_path.write_text(baseline_snapshot)
            
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_gen.return_value = '{"rules": [], "policy_hash": "current_hash"}'
                
                # Mock small number of acceptable changes
                mock_changes = [
                    {"type": "added", "rule": {"role": "user", "resource": "memory", "permissions": ["read"]}}
                ]
                
                with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                    mock_validate.return_value = {
                        "comparison": {"identical": False, "changes": mock_changes},
                        "completeness": {"complete": True}
                    }
                    
                    result = gate.check_policy_changes()
                    
                    assert result["status"] == "changes_detected"
                    assert result["gate_passed"] is True  # Should pass with small changes
                    assert result["changes"]["additions"] == 1
    
    def test_concerning_changes_scenario(self):
        """Test behavior with concerning policy changes."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Create baseline
            baseline_snapshot = '{"rules": [], "policy_hash": "baseline_hash"}'
            gate.baseline_path.write_text(baseline_snapshot)
            
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_gen.return_value = '{"rules": [], "policy_hash": "current_hash"}'
                
                # Mock concerning changes (too many additions)
                mock_changes = [
                    {"type": "added", "rule": {"role": "user", "resource": f"resource_{i}", "permissions": ["read"]}}
                    for i in range(10)  # Exceeds max_acceptable_additions (5)
                ]
                
                with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                    mock_validate.return_value = {
                        "comparison": {"identical": False, "changes": mock_changes},
                        "completeness": {"complete": True}
                    }
                    
                    result = gate.check_policy_changes()
                    
                    assert result["status"] == "changes_detected"
                    assert result["gate_passed"] is False
                    assert result["requires_approval"] is True
                    assert result["changes"]["additions"] == 10
                    assert any("Too many permission additions" in issue for issue in result["issues"])
    
    def test_privilege_escalation_detection(self):
        """Test detection of privilege escalation."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Test escalation detection
            changes = [
                {
                    "type": "added",
                    "rule": {"role": "user", "resource": "memory", "permissions": ["admin"]}
                },
                {
                    "type": "modified",
                    "old_rule": {"role": "viewer", "resource": "memory", "permissions": ["read"]},
                    "new_rule": {"role": "viewer", "resource": "memory", "permissions": ["read", "write"]}
                }
            ]
            
            escalations = gate._detect_privilege_escalation(changes)
            
            assert len(escalations) == 2
            assert escalations[0]["rule"]["permissions"] == ["admin"]
            assert "write" in escalations[1]["new_rule"]["permissions"]
    
    def test_approval_file_bypass(self):
        """Test that approval file allows concerning changes."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            # Create approval file
            approval_file = self.temp_dir / ".rbac_changes_approved"
            approval_file.touch()
            
            # Create baseline
            baseline_snapshot = '{"rules": [], "policy_hash": "baseline_hash"}'
            gate.baseline_path.write_text(baseline_snapshot)
            
            with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                mock_gen.return_value = '{"rules": [], "policy_hash": "current_hash"}'
                
                # Mock concerning changes
                mock_changes = [
                    {"type": "removed", "rule": {"role": "user", "resource": "memory", "permissions": ["write"]}}
                ]
                
                with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                    mock_validate.return_value = {
                        "comparison": {"identical": False, "changes": mock_changes},
                        "completeness": {"complete": True}
                    }
                    
                    result = gate.check_policy_changes()
                    
                    assert result["gate_passed"] is True  # Should pass with approval file
                    assert result["requires_approval"] is False
                    assert any("approved via" in issue for issue in result["issues"])
    
    def test_generate_approval_template(self):
        """Test approval template generation."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            gate_result = {
                "changes": {"total": 5, "additions": 3, "modifications": 1, "removals": 1, "escalations": 0},
                "issues": ["Too many additions", "Removals not allowed"],
                "change_details": [{"type": "added", "rule": {"role": "user"}}]
            }
            
            template = gate.generate_approval_template(gate_result)
            
            assert "Total Changes**: 5" in template
            assert "Additions**: 3" in template
            assert "Too many additions" in template
            assert ".rbac_changes_approved" in template
            assert "Security Review Checklist" in template
    
    def test_change_logging(self):
        """Test policy change logging."""
        with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=self.temp_dir):
            gate = RBACPolicyGate(self.config)
            
            gate_result = {
                "status": "changes_detected",
                "gate_passed": False,
                "requires_approval": True,
                "changes": {"total": 1}
            }
            
            with patch.object(gate, '_get_git_commit_hash', return_value="abc123"):
                with patch.object(gate, '_get_git_branch', return_value="feature/test"):
                    gate._log_policy_changes(gate_result)
            
            # Check log file was created and contains entry
            assert gate.change_log_path.exists()
            log_content = gate.change_log_path.read_text()
            log_entry = json.loads(log_content.strip())
            
            assert log_entry["status"] == "changes_detected"
            assert log_entry["gate_passed"] is False
            assert log_entry["git_commit"] == "abc123"
            assert log_entry["git_branch"] == "feature/test"


class TestIntegration:
    """Test integration scenarios."""
    
    def test_full_workflow_with_baseline_creation(self):
        """Test complete workflow from baseline creation to change detection."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            config = PolicyGateConfig(
                baseline_path=str(temp_dir / "baseline.json"),
                current_path=str(temp_dir / "current.json"),
                change_log_path=str(temp_dir / "changes.log"),
                git_integration=False
            )
            
            with patch('scripts.rbac_policy_snapshot_gate.Path.cwd', return_value=temp_dir):
                gate = RBACPolicyGate(config)
                
                # Step 1: Create baseline
                with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                    mock_gen.return_value = '{"rules": [], "policy_hash": "baseline", "rules_count": 0}'
                    
                    baseline_result = gate.create_baseline()
                    assert baseline_result["status"] == "baseline_created"
                
                # Step 2: Check with no changes
                with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                    mock_gen.return_value = '{"rules": [], "policy_hash": "baseline", "rules_count": 0}'
                    
                    with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                        mock_validate.return_value = {
                            "comparison": {"identical": True, "changes": []},
                            "completeness": {"complete": True}
                        }
                        
                        check_result = gate.check_policy_changes()
                        assert check_result["status"] == "no_changes"
                        assert check_result["gate_passed"] is True
                
                # Step 3: Check with changes
                with patch.object(gate, 'generate_current_snapshot') as mock_gen:
                    mock_gen.return_value = '{"rules": [], "policy_hash": "changed", "rules_count": 1}'
                    
                    mock_changes = [{"type": "added", "rule": {"role": "user"}}]
                    with patch('scripts.rbac_policy_snapshot_gate.validate_policy_against_snapshot') as mock_validate:
                        mock_validate.return_value = {
                            "comparison": {"identical": False, "changes": mock_changes},
                            "completeness": {"complete": True}
                        }
                        
                        check_result = gate.check_policy_changes()
                        assert check_result["status"] == "changes_detected"
                        assert check_result["changes"]["total"] == 1
        
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
