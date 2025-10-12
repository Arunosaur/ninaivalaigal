# License Compliance Exceptions

**Version**: 1.0
**Last Updated**: October 11, 2025
**Review Schedule**: Quarterly

This document tracks all approved exceptions to our standard license compliance policies.

---

## Exception Process

Before adding an exception:

1. ✅ Complete exception request template (see below)
2. ✅ Technical review by engineering lead
3. ✅ Legal review by counsel
4. ✅ Final approval by CTO/Legal
5. ✅ Document in this file
6. ✅ Add to quarterly audit tracking

**Unapproved use of non-compliant licenses is a policy violation.**

---

## Active Exceptions

### EX-001: PyQt5 / PyQtWebEngine (GPL v3)
**Status**: 🚨 **UNDER REVIEW** (Not Yet Approved)
**Package**: PyQt5 (5.15.10), PyQtWebEngine (5.15.6)
**License**: GPL v3 (viral copyleft)
**Requested**: October 11, 2025
**Requestor**: Compliance Audit

**Justification**:
- To be determined (investigation in progress)
- May be development-only dependency
- May be isolated to proprietary `server/` code

**Alternatives Considered**:
- PySide6 (LGPL) - preferred if PyQt5 can be replaced
- tkinter (built-in Python) - for simple GUI needs
- Complete removal - if not actually used

**Impact Analysis**:
- **If in MIT/Apache code**: Critical violation, must remove immediately
- **If only in proprietary server/**: Acceptable (we can use GPL internally)
- **If in containers/infrastructure**: Moderate risk, document exception

**Isolation Strategy**:
- Determine exact usage with: `grep -r "PyQt" server/ frontend-* packages/`
- If found in public code: Create migration plan to PySide6
- If found only in proprietary code: Document as approved exception

**Approval Status**: ⏳ Pending Investigation
**Next Review**: November 1, 2025
**Responsible**: Engineering Team

**Decision Authority**: CTO + Legal Counsel
**Approved**: ❌ Not yet approved
**Approval Date**: N/A

---

### EX-002: LGPL Libraries (Dynamic Linking)
**Status**: ✅ **APPROVED**
**Packages**: 11 LGPL packages (see NOTICE.md)
**License**: LGPL v2.1, LGPL v3
**Approved**: October 11, 2025
**Approver**: Engineering Lead

**Justification**:
- All LGPL packages used via **dynamic linking only**
- No static linking or source code modifications
- LGPL allows dynamic linking in proprietary software
- Standard industry practice (e.g., PostgreSQL drivers)

**Packages Covered**:
1. PyGithub (LGPL) - GitHub API client
2. psycopg2-binary (LGPL) - PostgreSQL driver
3. chardet (LGPLv2+) - Character encoding detection
4. docutils (LGPL/BSD/GPL/Public Domain) - Documentation utilities
5. frozendict (LGPLv3) - Immutable dict implementation
6. gmpy2 (LGPLv3+) - Multiple-precision arithmetic
7. pycurl (LGPL/MIT) - libcurl bindings
8. pytoolconfig (LGPL-3.0-or-later) - Tool configuration
9. rope (LGPLv3+) - Python refactoring library
10. text-unidecode (Artistic/GPL/GPLv2+) - ASCII transliteration
11. docstring-to-markdown (LGPLv2+) - Docstring converter

**Compliance Requirements**:
1. ✅ Document in NOTICE.md (done)
2. ✅ Confirm dynamic linking only (verified)
3. ✅ Include LGPL license texts in distributions (pending)
4. ✅ Allow users to replace LGPL libraries (inherent via dynamic linking)

**Impact**: Low - Standard use of LGPL in proprietary software
**Next Review**: January 1, 2026 (quarterly)
**Responsible**: Compliance Team

---

### EX-003: @img/sharp-libvips-darwin-arm64 (LGPL-3.0 JavaScript)
**Status**: ✅ **APPROVED**
**Package**: @img/sharp-libvips-darwin-arm64 (1.2.3)
**License**: LGPL-3.0-or-later
**Approved**: October 11, 2025
**Approver**: Engineering Lead

**Justification**:
- Native library bindings for image processing (libvips)
- Used via dynamic linking (Node.js native module)
- Industry-standard image optimization library
- No source modifications

**Usage**:
- Server-side image resizing and optimization
- Not distributed to end users (server-side only)
- Sharp package itself is Apache 2.0 (compatible)

**Compliance Requirements**:
1. ✅ Document in NOTICE.md (done)
2. ✅ Include LGPL-3.0 license text in distributions
3. ✅ Confirm dynamic linking (verified - native module)

**Impact**: Low - Standard server-side dependency
**Next Review**: January 1, 2026
**Responsible**: Frontend Team

---

## Denied Exceptions

_(None yet)_

---

## Exception Request Template

Use this template to request a new exception:

```markdown
### EX-XXX: [Package Name] ([License])
**Status**: 🔄 **PENDING REVIEW**
**Package**: [name] ([version])
**License**: [license type]
**Requested**: [YYYY-MM-DD]
**Requestor**: [Your Name]

**Justification**:
[Why do we need this package?]

**Alternatives Considered**:
1. [Alternative 1] - rejected because [reason]
2. [Alternative 2] - rejected because [reason]

**Impact Analysis**:
- **Code affected**: [which files/modules]
- **License implications**: [what changes to our licensing]
- **User impact**: [how does this affect end users]

**Isolation Strategy**:
[How will we isolate this dependency to minimize risk?]

**Approval Status**: ⏳ Pending Review
**Next Review**: [YYYY-MM-DD]
**Responsible**: [Team/Person]

**Decision Authority**: [Who must approve]
**Approved**: ❌ Not yet approved
**Approval Date**: N/A
```

---

## Exception Review Schedule

| Exception | Review Frequency | Next Review | Responsible |
|-----------|------------------|-------------|-------------|
| EX-001 (PyQt) | Ad-hoc (investigation) | Nov 1, 2025 | Engineering |
| EX-002 (LGPL) | Quarterly | Jan 1, 2026 | Compliance |
| EX-003 (sharp-libvips) | Quarterly | Jan 1, 2026 | Frontend |

---

## Exception Metrics

**Total Exceptions**: 3
**Approved**: 2 (67%)
**Under Review**: 1 (33%)
**Denied**: 0 (0%)

**By Risk Level**:
- 🚨 High Risk: 1 (PyQt GPL v3)
- ⚠️ Medium Risk: 0
- ✅ Low Risk: 2 (LGPL dynamic linking)

**By License Type**:
- GPL v3: 1 (under review)
- LGPL: 2 (approved)

---

## Escalation Procedures

### For New Exception Requests:
1. Engineering Lead reviews technical justification
2. Legal reviews license implications
3. CTO/Legal makes final decision
4. Compliance updates this document

### For Denied Exceptions:
1. Requestor must propose alternative solution
2. If no alternative exists, feature may be blocked
3. Escalate to executive leadership if business-critical

### For Expired Exceptions:
1. Compliance team notifies owner 30 days before expiry
2. Owner must justify renewal or plan removal
3. Expired exceptions become violations if not renewed

---

## Contact Information

**Exception Requests**: compliance@medhasys.com
**Legal Review**: legal@medhasys.com
**Emergency Violations**: security@medhasys.com

---

**Maintained by**: Compliance Team
**Review Authority**: CTO + Legal Counsel
**Version Control**: Tracked in Git with audit trail

---

**SPDX-License-Identifier**: CC-BY-4.0 (this document only)
