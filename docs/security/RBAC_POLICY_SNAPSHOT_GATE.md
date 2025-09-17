# RBAC Policy Snapshot Pre-commit Gate

## Overview

The RBAC Policy Snapshot Pre-commit Gate is a security mechanism that prevents unnoticed changes to the Role-Based Access Control (RBAC) policy matrix by comparing the current policy state against a baseline snapshot before allowing commits.

## Features

- **Automated Policy Drift Detection**: Compares current RBAC policy against baseline snapshot
- **Configurable Thresholds**: Limits on policy additions, modifications, and removals
- **Privilege Escalation Detection**: Identifies concerning permission changes automatically
- **Manual Approval Workflow**: Override mechanism for intentional policy changes
- **Git Integration**: Tracks commits, branches, and maintains change history
- **CI/CD Ready**: Supports both local development and continuous integration environments
- **Comprehensive Logging**: Detailed audit trail with timestamps and git context

## Installation

### 1. Pre-commit Hook Setup

The gate is integrated via pre-commit hooks. Install pre-commit if not already available:

```bash
pip install pre-commit
```

Install the hooks:

```bash
pre-commit install
```

### 2. Create Initial Baseline

Before using the gate, create an initial policy baseline:

```bash
python scripts/rbac_policy_snapshot_gate.py --create-baseline
```

This creates `rbac_policy_baseline.json` containing the current policy state.

## Usage

### Automatic Operation

The gate runs automatically on commits that modify RBAC-related files:
- `server/rbac_*.py`
- `tests/test_rbac_*.py` 
- `scripts/*rbac*.py`
- Any `.sql` files in these patterns

### Manual Operation

Check current policy against baseline:
```bash
python scripts/rbac_policy_snapshot_gate.py --check
```

Update baseline to current state:
```bash
python scripts/rbac_policy_snapshot_gate.py --update-baseline
```

Generate approval template for changes:
```bash
python scripts/rbac_policy_snapshot_gate.py --generate-approval
```

Run in CI mode (stricter validation):
```bash
python scripts/rbac_policy_snapshot_gate.py --check --ci-mode
```

## Configuration

The gate behavior is controlled by `PolicyGateConfig` in `scripts/rbac_policy_snapshot_gate.py`:

```python
@dataclass
class PolicyGateConfig:
    max_acceptable_additions: int = 5      # Max new permissions without approval
    max_acceptable_modifications: int = 2   # Max permission changes without approval
    allow_removals: bool = False           # Whether to allow permission removals
    require_approval_file: bool = True     # Require .rbac_changes_approved file
    git_integration: bool = True           # Enable git commit/branch tracking
    ci_mode: bool = False                 # Stricter validation for CI
```

## Approval Workflow

When the gate detects concerning changes, it requires manual approval:

### 1. Review Changes
The gate will output detailed information about detected policy changes:
```
❌ RBAC Policy Gate: FAILED
🔒 Policy changes detected that require manual approval

Policy Changes Summary:
- Additions: 8 (exceeds limit of 5)
- Modifications: 1
- Removals: 0
- Privilege Escalations: 2

Issues:
- Too many permission additions (8 > 5)
- Privilege escalation detected: admin permissions added
```

### 2. Generate Approval Template
```bash
python scripts/rbac_policy_snapshot_gate.py --generate-approval > rbac_approval.md
```

### 3. Review and Approve
Review the generated template, complete the security checklist, and create the approval file:
```bash
touch .rbac_changes_approved
git add .rbac_changes_approved
git commit -m "Approve RBAC policy changes"
```

### 4. Commit Original Changes
The original commit will now pass the gate check.

## Security Considerations

### Privilege Escalation Detection

The gate automatically detects privilege escalations by identifying:
- Addition of high-privilege permissions (`admin`, `write`, `delete`)
- Expansion of existing role permissions
- New roles with elevated access

### Thresholds and Limits

Default thresholds are conservative to catch most concerning changes:
- **5 additions**: Small incremental changes are acceptable
- **2 modifications**: Limited permission changes without review
- **0 removals**: Permission removals require explicit approval

### CI/CD Integration

In CI mode, the gate applies stricter validation:
- Lower thresholds for acceptable changes
- Mandatory approval file for any privilege escalations
- Enhanced logging and audit trails

## File Structure

```
.
├── .pre-commit-config.yaml              # Pre-commit configuration
├── .pre-commit-hooks/
│   └── rbac-policy-gate                 # Pre-commit hook script
├── scripts/
│   └── rbac_policy_snapshot_gate.py     # Main gate implementation
├── tests/
│   ├── test_rbac_policy_snapshot.py     # RBAC snapshot tests
│   └── test_rbac_policy_gate.py         # Gate functionality tests
├── docs/security/
│   └── RBAC_POLICY_SNAPSHOT_GATE.md     # This documentation
├── rbac_policy_baseline.json            # Policy baseline snapshot
├── rbac_policy_current.json             # Current policy state (temp)
└── rbac_policy_changes.log              # Change audit log
```

## Testing

Run the comprehensive test suite:

```bash
# Test gate functionality
python -m pytest tests/test_rbac_policy_gate.py -v

# Test RBAC snapshot system
python -m pytest tests/test_rbac_policy_snapshot.py -v

# Test all security components
python -m pytest tests/test_multipart_hardening_patch_v2.py tests/test_metrics_label_guard.py tests/test_rbac_policy_gate.py -v
```

## Troubleshooting

### Gate Fails on Clean Policy
If the gate fails unexpectedly on a clean policy:
1. Verify baseline exists: `ls -la rbac_policy_baseline.json`
2. Regenerate baseline: `python scripts/rbac_policy_snapshot_gate.py --create-baseline`
3. Check for import errors in policy modules

### False Positives
If the gate triggers on acceptable changes:
1. Review the specific changes: `python scripts/rbac_policy_snapshot_gate.py --check --verbose`
2. Adjust thresholds in `PolicyGateConfig` if needed
3. Use approval workflow for one-time exceptions

### CI/CD Issues
For CI/CD pipeline failures:
1. Ensure baseline is committed to repository
2. Use `--ci-mode` for stricter validation
3. Pre-approve expected changes in deployment scripts

## Integration Examples

### GitHub Actions
```yaml
- name: RBAC Policy Gate
  run: |
    python scripts/rbac_policy_snapshot_gate.py --check --ci-mode
```

### GitLab CI
```yaml
rbac_policy_gate:
  script:
    - python scripts/rbac_policy_snapshot_gate.py --check --ci-mode
  only:
    changes:
      - server/rbac_*.py
      - tests/test_rbac_*.py
```

### Jenkins Pipeline
```groovy
stage('RBAC Policy Gate') {
    steps {
        sh 'python scripts/rbac_policy_snapshot_gate.py --check --ci-mode'
    }
}
```

## Security Impact

The RBAC Policy Snapshot Gate provides critical security benefits:

1. **Prevents Accidental Privilege Escalation**: Catches unintended permission expansions
2. **Enforces Change Review**: Requires explicit approval for concerning modifications
3. **Maintains Audit Trail**: Comprehensive logging of all policy changes
4. **Supports Compliance**: Provides evidence of access control governance
5. **Reduces Attack Surface**: Prevents policy drift that could create vulnerabilities

## Maintenance

### Regular Tasks
- Review change logs monthly: `cat rbac_policy_changes.log`
- Update baseline after approved policy changes
- Monitor for false positives and adjust thresholds

### Baseline Management
- Baseline should be updated only after thorough security review
- Keep historical baselines for rollback capability
- Document all baseline updates with justification

## Related Documentation

- [Multipart Security Hardening](MULTIPART_HARDENING_PATCH_V2.md)
- [Metrics Label Guard](../observability/METRICS_LABEL_GUARD.md)
- [RBAC Policy Snapshot Tests](../../tests/test_rbac_policy_snapshot.py)

---

**Status**: Production Ready  
**Version**: 1.0  
**Last Updated**: 2025-09-16  
**Security Review**: Required before deployment
