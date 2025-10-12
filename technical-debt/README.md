# Technical Debt Log

**Last Updated**: October 11, 2025
**Tracking**: Code quality issues and planned refactoring

---

## 🔴 **High Priority**

### TD-001: Flake8 Violations in Codebase
**Status**: Documented
**Impact**: Pre-commit hooks require `--no-verify` bypass
**Discovered**: During SPDX header implementation (commit 17daaf00)

**Affected Files** (30 violations across 19 files):
- `alembic/env_new.py` (2 violations: D103 missing docstrings)
- `alembic/versions/0112_staff_management.py` (2 violations: D103)
- `ninaivalaigal_ci_rbac_pack/rbac/permissions.py` (5 violations: D103)
- `tests/auth/test_rate_limiting.py` (2 violations: B007 unused loop vars)
- `tests/auth_aware/test_fixtures.py` (2 violations: B007)
- `tests/auth_aware/test_multi_user_scenarios.py` (2 violations: B007)
- `tests/auth_aware/test_rbac_validation.py` (1 violation: B007)
- `tests/e2e/test_complete_auth_flow.py` (1 violation: B007)
- `tests/e2e/test_foundation_matrix.py` (1 violation: B007)
- `tests/foundation/spec_058/test_documentation_links.py` (1 violation: F841 unused var)
- `tests/foundation/spec_063/test_agentic_core.py` (1 violation: F841)
- `tests/integration/spec_040_062_unified/test_memory_graph_unified.py` (1 violation: B007)
- `tests/integration/test_multipart_monitoring.py` (1 violation: B007)
- `tests/smoke/test_db.py` (1 violation: B007)
- `tests/test_agentic_execution.py` (1 violation: F841)
- `tests/test_memory_endpoints.py` (1 violation: F841)
- `tests/test_security_middleware.py` (1 violation: B007)
- `tests/test_team_workflows_e2e.py` (1 violation: F841)
- `tests/unit/test_auth_enhanced.py` (1 violation: F841)

**Violation Types**:
- **D103**: Missing docstrings in public functions (9 violations)
- **B007**: Loop control variable not used (should start with `_`) (13 violations)
- **F841**: Local variable assigned but never used (8 violations)

**Why Deferred**:
- Non-functional changes (style/quality only)
- No runtime impact
- Large surface area (19 files)
- Would complicate SPDX header commit

**Remediation Plan**:
1. Add docstrings to alembic functions
2. Rename unused loop variables (`i` → `_i`, `user` → `_user`, etc.)
3. Remove or use unused local variables (or prefix with `_`)
4. Re-run flake8 to confirm clean
5. Commit: "fix: Resolve all flake8 violations (TD-001)"

**Container Rebuild Required**: Yes (but minimal - only alembic/ is in container)

**Estimated Effort**: 1-2 hours
**Target Resolution**: Sprint 2025-Q4
**Owner**: TBD

---

## 🟡 **Medium Priority**

### TD-002: GPL v3 Contamination
**Status**: Investigating
**Impact**: Open-source licensing risk
**Discovered**: Dependency audit 2025-Q4

**Affected Packages**:
- PyQt5 (5.15.10) - GPL v3
- PyQtWebEngine (5.15.6) - GPL v3

**Next Steps**:
1. `grep -r "PyQt" server/ frontend-* packages/`
2. Determine if used in MIT/Apache code (CRITICAL) or proprietary server/ (OK)
3. Replace with PySide6 (LGPL) if in public code
4. Document exception if only in proprietary code

**Target Resolution**: Sprint 2025-Q4
**Owner**: TBD

---

## 🟢 **Low Priority**

### TD-003: UNLICENSED JavaScript Packages
**Status**: Documented
**Impact**: License compliance gap
**Discovered**: JavaScript dependency audit 2025-Q4

**Affected Packages**:
- 2 npm packages showing as "UNLICENSED"

**Next Steps**:
1. Identify exact package names
2. Check package.json for missing license field
3. Verify actual license from source repository
4. Update or replace packages

**Target Resolution**: Sprint 2025-Q4
**Owner**: TBD

---

## 📋 **Process Improvements Needed**

### PI-001: Pre-commit Hook Enforcement
**Issue**: Developers can bypass hooks with `--no-verify`
**Solution**: Add commit message validation that rejects commits with `--no-verify` in message

### PI-002: Automated Flake8 in CI
**Issue**: Violations can be committed if pre-commit is bypassed
**Solution**: Add GitHub Actions workflow that fails on any flake8 violations

### PI-003: Quarterly Compliance Audits
**Issue**: No scheduled compliance reviews
**Solution**: Add cron job to run dependency audits quarterly

---

## 📊 **Technical Debt Metrics**

| Category | Count | Priority | Estimated Hours |
|----------|-------|----------|-----------------|
| Flake8 Violations | 30 | High | 1-2 |
| GPL Contamination | 2 pkgs | High | 2-4 |
| Unlicensed Packages | 2 pkgs | Medium | 1 |
| **Total** | **34 items** | **Mixed** | **4-7 hours** |

**Target**: Resolve all High priority items by end of Q4 2025

---

## 🔄 **Review Schedule**

- **Weekly**: New technical debt items added to this log
- **Monthly**: Review and prioritize technical debt backlog
- **Quarterly**: Major cleanup sprint for accumulated debt

---

**Maintained by**: Engineering Team
**Last Review**: October 11, 2025
**Next Review**: November 11, 2025
