# Deprecated SPECs Summary

**Last Updated**: November 1, 2025
**Total Deprecated**: 3 SPECs

---

## Overview

This directory contains deprecated specifications that have been superseded by newer, more comprehensive SPECs. These are archived for historical reference but should not be used for new development.

---

## Deprecated SPECs

### SPEC-002: User Management & Authentication
**Deprecated**: Early 2024
**Superseded By**: [SPEC-006: User Management, Authentication & Signup](../../specs/006-user-signup-system/README.md)
**Reason**: SPEC-006 provides a more comprehensive and modern approach to user management with signup flows, email verification, and better security practices.

**Location**: Not moved to archive (deprecated in place)
**Status in Index**: 🔴 DEPRECATED - See SPEC-006

---

### SPEC-049: Memory Sharing & Collaboration
**Deprecated**: November 1, 2025
**Superseded By**: [SPEC-127: Context Bridge & Memory Federation System](../../specs/127-context-bridge-system/README.md)
**Reason**: SPEC-127 provides a more comprehensive federation system that includes all memory sharing capabilities plus cross-organizational context bridging.

**Location**: `.archive/deprecated/049-memory-sharing-collaboration/`
**Status in Index**: 🔴 DEPRECATED - See SPEC-127

**Key Features Migrated to SPEC-127**:
- ✅ Role-based sharing (Viewer, Editor, Commenter)
- ✅ User & team collaboration
- ✅ Time-limited access with expiry
- ✅ Revocation system
- ✅ Audit trails
- ✅ Sharing dashboard
- ✅ Deep links with scoped access

**Additional Features in SPEC-127**:
- 🆕 Cross-organizational memory federation
- 🆕 Context bridge for multi-tenant scenarios
- 🆕 Advanced trust models
- 🆕 Federation search capabilities

---

### SPEC-050: Cross-Organization Memory Sharing
**Deprecated**: November 1, 2025
**Superseded By**: [SPEC-127: Context Bridge & Memory Federation System](../../specs/127-context-bridge-system/README.md)
**Reason**: SPEC-127 consolidates cross-org sharing with internal sharing into a unified federation system.

**Location**: `.archive/deprecated/050-cross-org-memory-sharing/`
**Status in Index**: 🔴 DEPRECATED - See SPEC-127

**Key Features Migrated to SPEC-127**:
- ✅ Org-to-org token bridge
- ✅ Visibility scopes (EXTERNAL-READ, EXTERNAL-REFERENCE, EXTERNAL-EMBED)
- ✅ Shared link tokens with verification
- ✅ Sharing policy framework
- ✅ Audit ledger with signed logs
- ✅ Sandbox mode for sensitive tokens
- ✅ Compliance tags

**Additional Features in SPEC-127**:
- 🆕 Unified internal + external sharing model
- 🆕 Enhanced security with modern cryptography
- 🆕 Better performance with caching
- 🆕 Improved developer experience

---

## Deprecation Process

When a SPEC is deprecated:

1. **Add Deprecation Notice**: Update the SPEC's README with a prominent deprecation notice at the top
2. **Update SPEC Index**: Mark the SPEC as deprecated in `specs/SPEC_INDEX.md`
3. **Move to Archive**: Move the SPEC directory to `.archive/deprecated/`
4. **Update Cross-References**: Update all references in other SPECs to point to the new SPEC
5. **Update Taiga Stories**: Mark related Taiga stories as deprecated or migrate to new SPEC
6. **Document Reason**: Clearly document why the SPEC was deprecated and what replaces it

---

## Using Deprecated SPECs

**⚠️ DO NOT**:
- Implement features from deprecated SPECs
- Create new Taiga stories referencing deprecated SPECs
- Reference deprecated SPECs in new documentation

**✅ DO**:
- Use the superseding SPEC for all new work
- Migrate existing work to the new SPEC
- Keep deprecated SPECs for historical reference only
- Update any existing references to point to the new SPEC

---

## Migration Guide

### From SPEC-049/050 to SPEC-127

If you have existing work based on SPEC-049 or SPEC-050:

1. **Review SPEC-127**: Read the [SPEC-127 README](../../specs/127-context-bridge-system/README.md) to understand the new architecture
2. **Map Features**: Identify which SPEC-127 features correspond to your SPEC-049/050 work
3. **Update Stories**: Migrate Taiga stories to reference SPEC-127
4. **Refactor Code**: Update any existing code to use SPEC-127 patterns
5. **Update Tests**: Ensure tests align with SPEC-127 requirements
6. **Update Docs**: Change all documentation references to SPEC-127

**Key Differences**:
- SPEC-127 uses a unified federation model instead of separate internal/external sharing
- SPEC-127 has enhanced security with modern cryptographic primitives
- SPEC-127 includes caching and performance optimizations
- SPEC-127 has a more comprehensive API design

---

## Questions?

For questions about deprecated SPECs or migration:
1. Review the superseding SPEC's README
2. Check the governance reports in `governance/reports/`
3. Consult the SPEC_INDEX.md for current status
4. Contact the architecture team

---

## Archive Structure

```
.archive/
└── deprecated/
    ├── DEPRECATION_SUMMARY.md (this file)
    ├── 049-memory-sharing-collaboration/
    │   └── README.md (with deprecation notice)
    └── 050-cross-org-memory-sharing/
        └── README.md (with deprecation notice)
```

---

**Maintained By**: Architecture Team
**Last Review**: November 1, 2025
**Next Review**: Quarterly (February 2026)
