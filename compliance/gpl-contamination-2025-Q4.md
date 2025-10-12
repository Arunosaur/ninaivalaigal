# GPL Contamination Analysis - 2025 Q4

**Date**: October 11, 2025
**Status**: 🚨 CRITICAL - GPL v3 packages detected

## High-Severity Issues (GPL v3)

### 1. PyQt5 (GPL v3)
- **Version**: 5.15.10
- **License**: GPL v3 (viral copyleft)
- **Risk**: HIGH - Could contaminate MIT/Apache code
- **Usage**: Unknown - needs investigation
- **Action**: REMOVE or isolate to proprietary server/ only

### 2. PyQtWebEngine (GPL v3)
- **Version**: 5.15.6
- **License**: GPL v3 (viral copyleft)
- **Risk**: HIGH - Could contaminate MIT/Apache code
- **Usage**: Unknown - needs investigation
- **Action**: REMOVE or isolate to proprietary server/ only

## Medium-Severity Issues (LGPL)

LGPL packages are generally safe for dynamic linking but require documentation:

### PyGithub (LGPL)
- **Status**: ⚠️ OK - Used in development/tooling
- **Usage**: GitHub API integration

### psycopg2-binary (LGPL)
- **Status**: ⚠️ OK - Database driver (dynamic linking)
- **Usage**: PostgreSQL connection

### chardet, docutils, frozendict, gmpy2, pycurl, pytoolconfig, rope (LGPL)
- **Status**: ⚠️ OK - Development/build tools
- **Usage**: Various utilities and tooling

## Recommendations

### Immediate Actions Required:

1. **Investigate PyQt5/PyQtWebEngine**:
   ```bash
   grep -r "PyQt" server/ frontend-* packages/
   ```
   - If in server/ (proprietary): OK, can use GPL internally
   - If in MIT/Apache code: MUST REMOVE immediately

2. **Document LGPL Usage**:
   - Add to compliance/exceptions.md
   - Confirm dynamic linking (not static)
   - Include in NOTICE file

3. **Create Clean Environment**:
   - Consider separate venv for development vs production
   - Only install GPL packages in isolated environments

### Long-Term Solutions:

1. **Separate Dependencies**:
   - dev-requirements.txt (can include GPL)
   - prod-requirements.txt (no GPL)

2. **Alternative Packages**:
   - PyQt5 → PySide6 (LGPL) or tkinter (built-in)
   - PyQtWebEngine → Alternatives TBD

## Next Steps:

- [ ] Investigate where PyQt5 is used
- [ ] Determine if it's in MIT/Apache components
- [ ] Remove or relocate to proprietary code
- [ ] Update requirements.txt with split dependencies
- [ ] Re-run audit after cleanup

---

**Audited by**: Compliance Bot
**Approved by**: [Pending]
**Next Review**: 2026-Q1
