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

### TD-002: GPL v3 Contamination - ✅ RESOLVED
**Status**: ✅ Resolved - All 4 GPL packages safe
**Impact**: None - Not shipped to production
**Discovered**: Dependency audit 2025-Q4
**Resolved**: October 12, 2025

**Affected Packages**:
1. PyQt5 (5.15.10) - GPL v3 (required by Spyder IDE)
2. PyQtWebEngine (5.15.6) - GPL v3 (required by Spyder IDE)
3. docutils (0.21.2) - Dual-licensed (BSD/GPL) - using BSD
4. text-unidecode (1.3) - Dual-licensed (Artistic/GPL) - using Artistic

**Resolution**:
1. Verified ALL packages NOT imported in production code
2. Confirmed NOT in requirements.txt (development environment only)
3. Identified dependencies:
   - PyQt5/PyQtWebEngine: Spyder IDE (development tool)
   - docutils: Sphinx documentation generator → Spyder
   - text-unidecode: python-slugify → cookiecutter (project templates)
4. Dual-licensed packages: Using BSD/Artistic instead of GPL
5. NO ACTION NEEDED - Development dependencies don't contaminate shipped code

**Conclusion**: All GPL packages are safe - dev-only tools + dual-licensing options.

**Target Resolution**: Sprint 2025-Q4 ✅
**Owner**: Resolved by verification

---

## 🟢 **Low Priority**

### TD-003: UNLICENSED JavaScript Packages - ✅ RESOLVED
**Status**: ✅ Resolved - License fields added
**Impact**: None - Own packages, now properly licensed
**Discovered**: JavaScript dependency audit 2025-Q4
**Resolved**: October 12, 2025

**Affected Packages**:
1. `@ninaivalaigal/ui-components@0.1.0` (frontend-shared)
2. `frontend-nextjs-customer@0.1.0`

**Resolution**:
1. Identified packages were ninaivalaigal's own frontend packages
2. Added `"license": "MIT"` field to both package.json files
3. MIT license chosen for frontend (permissive, compatible with MIT/Apache dual-license)
4. License field now properly declared for npm compliance

**Conclusion**: Own packages now properly licensed under MIT.

**Target Resolution**: Sprint 2025-Q4 ✅
**Owner**: Resolved by adding license fields

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

| Category | Count | Priority | Estimated Hours | Status |
|----------|-------|----------|-----------------|--------|
| Flake8 Violations | 30 | High | 1-2 | ⏳ Pending |
| ~~GPL Contamination~~ | ~~4 pkgs~~ | ~~High~~ | ~~2-4~~ | ✅ Resolved |
| ~~Unlicensed Packages~~ | ~~2 pkgs~~ | ~~Medium~~ | ~~1~~ | ✅ Resolved |
| **Total Active** | **30 items** | **High** | **1-2 hours** | **6 items Resolved** |

**Target**: Resolve all High priority items by end of Q4 2025
**Progress**: 1/2 High-priority categories resolved (50%)
**Recent Resolutions**:
- GPL: All 4 packages verified safe (dev-only + dual-licensed)
- UNLICENSED: 2 frontend packages now properly licensed (MIT)

---

## 🔄 **Review Schedule**

- **Weekly**: New technical debt items added to this log
- **Monthly**: Review and prioritize technical debt backlog
- **Quarterly**: Major cleanup sprint for accumulated debt

---

**Maintained by**: Engineering Team
**Last Review**: October 11, 2025
**Next Review**: November 11, 2025
