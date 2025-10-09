# Security Policy: Bandit Configuration

## Overview
This document explains our Bandit security scanning configuration and the rationale for exclusions.

## Current Security Posture

```
✅ HIGH Severity Issues: 0
⚠️  MEDIUM Severity Issues: 17 (false positives)
ℹ️  LOW Severity Issues: 246 (informational)
📊 Lines of Code Scanned: 67,833
```

**Status**: ✅ **Excellent** - No exploitable security vulnerabilities detected

---

## Exclusion Rationale

### B104: Binding to All Interfaces

**What it detects**: `app.run(host="0.0.0.0", port=8080)`

**Why we skip**:
- ✅ **Legitimate for development** servers and containerized deployments
- ✅ **Production uses proper host binding** via Docker/K8s configurations
- ✅ **Not a security risk** in our deployment model (containers + ingress gateway)

**Example**:
```python
# Development server - acceptable
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)  # OK: Dev server
```

---

### B608: SQL Injection Warnings

**What it detects**: String-based SQL query construction

**Why we skip**:
- ✅ **All queries use SQLAlchemy ORM** with parameterization
- ✅ **False positives** from `text()` with proper parameter binding
- ✅ **No actual SQL injection vectors** - all inputs are sanitized

**Example of safe pattern Bandit flags**:
```python
# This is SAFE (parameterized) but Bandit flags it
query = text("SELECT * FROM users WHERE id = :id")  # nosec B608
result = session.execute(query, {"id": user_id})
```

**What we DO protect against**:
```python
# This would be UNSAFE - we never do this
query = f"SELECT * FROM users WHERE id = {user_id}"  # ❌ BLOCKED by code review
```

---

## Excluded Directories

```yaml
exclude_dirs:
  - /tests/         # Test code with intentional security bypasses
  - /scripts/       # Development/admin scripts, not production
  - /alembic/       # Database migrations (generated, reviewed separately)
  - /client-tools/  # Client utilities, different trust boundary
  - /external/      # Third-party code, scanned separately
```

---

## Severity Thresholds

### Pre-commit Enforcement
- ❌ **HIGH**: Blocks commit (zero tolerance)
- ⚠️  **MEDIUM**: Warning only (reviewed manually)
- ℹ️  **LOW**: Informational (not shown)

### CI/CD Pipeline
- ❌ **HIGH**: Fails build
- ⚠️  **MEDIUM**: Warning (tracked, doesn't block)
- ℹ️  **LOW**: Reported for awareness

---

## When to Use `# nosec`

Add inline suppression **only** for verified safe code:

```python
# ✅ Good: Specific, documented suppression
query = text("SELECT * FROM users WHERE id = :id")  # nosec B608 - parameterized query

# ❌ Bad: Blanket suppression
# nosec  # Don't do this - too broad
```

**Review process**:
1. Verify the code is actually safe
2. Add specific test ID: `# nosec B608`
3. Add brief explanation in comment
4. Get security review for HIGH/MEDIUM suppressions

---

## Security Review Cadence

| Activity | Frequency | Owner |
|----------|-----------|-------|
| Pre-commit scan | Every commit | Automated |
| Full repository scan | Weekly | Security team |
| Dependency audit | Monthly | DevOps |
| Security policy review | Quarterly | Security + Eng leads |

---

## Reporting Security Issues

If you identify a **genuine security vulnerability** (not a false positive):

1. **DO NOT** open a public GitHub issue
2. **DO** report to: security@[company].com
3. **DO** follow responsible disclosure practices
4. **DO** expect acknowledgment within 24 hours

---

## References

- [Bandit Documentation](https://bandit.readthedocs.io/)
- [SQLAlchemy Security Best Practices](https://docs.sqlalchemy.org/en/14/core/connections.html#using-textual-sql)
- [OWASP SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)

---

**Last Updated**: 2025-10-09
**Policy Version**: 1.0
**Status**: ✅ Active
