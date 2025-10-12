# License Compliance Guide

**Version 1.0 | Last Updated: October 2025**

This document provides guidelines for maintaining license compliance in the Ninaivalaigal project.

## Overview

Ninaivalaigal uses a **multi-license open-core model**. Compliance requires:
1. ✅ Ensuring all dependencies are compatible with our licenses
2. ✅ Maintaining SPDX headers in all source files
3. ✅ Regular audits of dependency licenses
4. ✅ Proper attribution in NOTICE files

---

## Dependency License Compatibility

### Our Licenses and What They Allow

| Our License | Can Depend On | Cannot Depend On | Notes |
|-------------|---------------|------------------|-------|
| **MIT** | MIT, BSD, Apache 2.0, ISC | GPL, AGPL, LGPL (v3) | Most permissive |
| **Apache 2.0** | MIT, BSD, Apache 2.0, ISC | GPL, AGPL | Includes patent grant |
| **Elastic 2.0** | MIT, BSD, Apache 2.0, ISC | GPL, AGPL | Source-available |
| **Proprietary** | Any | None (we can use anything) | Full control |

### GPL Compatibility Issues

**⚠️ WARNING**: GPL and AGPL licenses are **viral** (copyleft):
- If you use GPL code in MIT/Apache code, the **entire project** becomes GPL
- This would **destroy** our open-core business model
- **Never** use GPL dependencies in `frontend-*`, `packages/*`, or `scripts/`

**Acceptable GPL use**:
- ✅ In `server/` (proprietary) - we can use GPL internally
- ✅ Build-time tools (linters, formatters) - not distributed
- ❌ Runtime dependencies - must avoid

---

## Automated Dependency Audits

### Python Dependencies

Run this monthly or before each release:

```bash
# Install license checker
pip install pip-licenses

# Generate full report
pip-licenses --format=markdown --with-urls --with-description > compliance/dep-licenses-python.md

# Check for GPL contamination
pip-licenses | grep -iE "GPL|LGPL"

# If any GPL found, investigate:
pip show [package-name]
```

**Action if GPL found**:
1. Check if it's a build-time tool (safe) or runtime dep (unsafe)
2. If runtime, find alternative or seek exception
3. Document decision in `compliance/exceptions.md`

### JavaScript Dependencies

Run this monthly or before each release:

```bash
# Install license checker
npm install -g license-checker

# Generate full report for each frontend
cd frontend-nextjs-customer
npx license-checker --json --out ../../compliance/dep-licenses-customer.json
npx license-checker --summary > ../../compliance/dep-summary-customer.txt

cd ../frontend-nextjs-admin
npx license-checker --json --out ../../compliance/dep-licenses-admin.json

cd ../frontend-shared
npx license-checker --json --out ../../compliance/dep-licenses-shared.json

# Check for GPL
cd ../..
grep -r "GPL" compliance/dep-*.json
```

**Common problematic licenses**:
- `GPL-2.0`, `GPL-3.0` - Viral copyleft ❌
- `AGPL-3.0` - Viral copyleft + network clause ❌
- `LGPL-3.0` - Conditional copyleft ⚠️ (linking ok, modification not)
- `UNLICENSED` or `UNKNOWN` - Requires manual review ⚠️

### Container Image Dependencies

Check base images and system packages:

```bash
# Scan Docker/Apple Container CLI images
container run --rm nina-api:arm64 dpkg -l > compliance/container-packages.txt

# For official images, check:
# - PostgreSQL: https://github.com/docker-library/postgres/blob/master/LICENSE
# - Redis: https://redis.io/docs/about/license/
```

---

## SPDX Header Compliance

### Automated Header Insertion

Use the provided script to add SPDX headers:

```bash
# Dry run (see what would change)
python3 SPDX-header-inserter.py --dry-run

# Add headers to all files
python3 SPDX-header-inserter.py

# Check compliance (for CI)
python3 SPDX-header-inserter.py --check
```

### Manual Header Format

If adding headers manually, use this template:

**Python files**:
```python
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
```

**TypeScript files**:
```typescript
// SPDX-License-Identifier: MIT
// Copyright (c) 2025 Medhasys LLC
```

**Shell scripts**:
```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
```

**For proprietary files**:
```python
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
```

---

## NOTICE File Maintenance

The `NOTICE` file must include attributions for all dependencies.

### Updating NOTICE

```bash
# Generate automatic attribution list
python3 scripts/generate-notice.py > NOTICE

# Or manually add entries in this format:
```

**NOTICE file template**:
```
Ninaivalaigal
Copyright (c) 2025 Medhasys LLC

This product includes software developed by:
- FastAPI (https://fastapi.tiangolo.com) - MIT License
- React (https://reactjs.org) - MIT License
- PostgreSQL (https://www.postgresql.org) - PostgreSQL License
- Redis (https://redis.io) - BSD 3-Clause License

[Full attributions in compliance/THIRD_PARTY_LICENSES.md]
```

---

## CI/CD Integration

Add these checks to your CI pipeline:

### GitHub Actions Workflow

```yaml
name: License Compliance

on: [push, pull_request]

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Check SPDX Headers
        run: python3 SPDX-header-inserter.py --check

      - name: Audit Python Dependencies
        run: |
          pip install pip-licenses
          pip-licenses | grep -iE "GPL|AGPL" && exit 1 || exit 0

      - name: Audit JavaScript Dependencies
        run: |
          cd frontend-nextjs-customer
          npx license-checker --summary | grep -iE "GPL|AGPL" && exit 1 || exit 0
```

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: spdx-headers
        name: Check SPDX Headers
        entry: python3 SPDX-header-inserter.py --check
        language: system
        always_run: true
```

---

## Exception Process

Sometimes you **must** use a GPL library (e.g., no alternative exists).

### Requesting an Exception

1. **Document the need**: Create `compliance/exceptions/[package-name].md`
2. **Include**:
   - Why this dependency is critical
   - Alternatives considered
   - License compatibility analysis
   - Isolation strategy (if applicable)
3. **Get approval**: Legal review required
4. **Track**: Add to `compliance/exceptions.md`

### Exception Template

```markdown
# Exception Request: [Package Name]

**Date**: YYYY-MM-DD
**Requestor**: [Your Name]
**Package**: [package-name]
**License**: GPL-3.0
**Component**: server/module_x

## Justification
[Why we need this package]

## Alternatives Considered
1. [Alternative 1] - rejected because [reason]
2. [Alternative 2] - rejected because [reason]

## Impact Analysis
- **Code affected**: [which files]
- **License implications**: [what changes]
- **Isolation strategy**: [how we contain GPL]

## Approval
- [ ] Technical Lead
- [ ] Legal Review
- [ ] Final Decision: APPROVED / REJECTED
```

---

## Quarterly Compliance Checklist

Run this checklist every 3 months:

### Q1 (January), Q2 (April), Q3 (July), Q4 (October)

**Pre-check**:
- [ ] Review all new dependencies added since last audit
- [ ] Update SPDX-header-inserter.py if new file types added
- [ ] Check for dependency security vulnerabilities (separate from licensing)

**Dependency Audit**:
- [ ] Run `pip-licenses` and review output
- [ ] Run `npx license-checker` for all frontends
- [ ] Check container base image licenses
- [ ] Scan for GPL/AGPL contamination
- [ ] Update `compliance/dep-licenses-*.md` snapshots

**Source Code Audit**:
- [ ] Run SPDX header checker: `python3 SPDX-header-inserter.py --check`
- [ ] Fix any missing headers
- [ ] Verify proprietary markers in `server/`
- [ ] Check that new files have correct license identifiers

**Attribution Update**:
- [ ] Update NOTICE file with new dependencies
- [ ] Regenerate THIRD_PARTY_LICENSES.md
- [ ] Check for trademark usage in dependencies

**Documentation**:
- [ ] Update LICENSE-MATRIX.md if new components added
- [ ] Review and update exception requests
- [ ] Archive compliance reports in `compliance/audits/YYYY-QX/`

**Legal Review**:
- [ ] Submit quarterly compliance report to legal team
- [ ] Address any flagged issues
- [ ] Update compliance procedures if needed

---

## Compliance Directory Structure

Maintain this structure for audit trails:

```
compliance/
├── README.md                          # This file
├── dep-licenses-python.md             # Python dependency licenses
├── dep-licenses-customer.json         # Customer app dependencies
├── dep-licenses-admin.json            # Admin app dependencies
├── dep-licenses-shared.json           # Shared packages
├── container-packages.txt             # Container image packages
├── THIRD_PARTY_LICENSES.md            # Full text of all dependency licenses
├── exceptions.md                      # Approved license exceptions
├── exceptions/                        # Individual exception requests
│   └── [package-name].md
└── audits/                            # Quarterly audit reports
    ├── 2025-Q4/
    │   ├── audit-report.md
    │   ├── issues-found.md
    │   └── issues-resolved.md
    └── 2025-Q1/
```

---

## Red Flags to Watch For

**Immediate Action Required**:
- 🚨 GPL/AGPL in runtime dependencies of MIT/Apache components
- 🚨 Missing LICENSE file in a dependency
- 🚨 "All Rights Reserved" in dependency
- 🚨 Custom license requiring manual review

**Review Needed**:
- ⚠️ LGPL dependencies (linking ok, but document)
- ⚠️ Creative Commons licenses in code (usually for docs only)
- ⚠️ Unlicensed or UNKNOWN packages
- ⚠️ Dual-licensed packages (pick compatible option)

**Acceptable**:
- ✅ MIT, BSD, ISC, Apache 2.0
- ✅ PostgreSQL License, Python Software Foundation License
- ✅ CC-BY-4.0 for documentation

---

## Resources

### Tools
- **Python**: `pip-licenses` - https://pypi.org/project/pip-licenses/
- **JavaScript**: `license-checker` - https://www.npmjs.com/package/license-checker
- **SPDX**: https://spdx.dev/

### Reference
- **SPDX License List**: https://spdx.org/licenses/
- **Choose a License**: https://choosealicense.com/
- **tl;drLegal**: https://www.tldrlegal.com/

### Legal
- **Questions**: legal@medhasys.com
- **Exception requests**: legal@medhasys.com
- **Urgent issues**: Call +1-XXX-XXX-XXXX

---

**Maintained by**: Medhasys LLC Legal & Engineering Teams
**Last Updated**: October 2025
**Version**: 1.0

---

**SPDX-License-Identifier**: CC-BY-4.0 (this document only)
