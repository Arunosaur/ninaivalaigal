# SPEC-049 Deprecation Notice

**⚠️ DEPRECATION NOTICE**: This SPEC has been **deprecated** as of **November 1, 2025**.

**Reason**: Superseded by [SPEC-127: Context Bridge & Memory Federation System](../127-context-bridge-system/README.md)

**Redirect**: All memory sharing and collaboration work is now tracked under **SPEC-127**.

**Action Required**:
- ✅ Use [SPEC-127](../127-context-bridge-system/README.md) as the authoritative specification
- ✅ Reference SPEC-127 in all future documentation and Taiga stories
- ✅ Do not implement features from this SPEC - use SPEC-127 instead

---

## What SPEC-127 Provides

SPEC-127 consolidates and extends SPEC-049 with:

### From SPEC-049 (Preserved):
- ✅ Role-based sharing (Viewer, Editor, Commenter)
- ✅ User & team collaboration
- ✅ Time-limited access
- ✅ Revocation system
- ✅ Audit trails
- ✅ Sharing dashboard
- ✅ Deep links

### Enhanced in SPEC-127:
- ✨ **Reference vs Clone modes** (live link vs isolated copy)
- ✨ **Security & trust scoring system** (0-100 dynamic scoring)
- ✨ **Detailed GraphOps integration** architecture
- ✨ **Unified API surface** (single entry point)
- ✨ **Cross-context graph linking** (federated queries)
- ✨ **Cross-org sharing** (consolidates SPEC-050)

---

## Migration Path

If you have work in progress based on SPEC-049:

1. **Review SPEC-127** to understand the unified architecture
2. **Map your features** to SPEC-127 capabilities
3. **Update references** from SPEC-049 to SPEC-127
4. **Use SPEC-127 APIs** instead of SPEC-049 designs

---

## Historical Context

**Original SPEC-049 Scope**:
- Extend memory access control model (SPEC-043) into collaboration system
- Enable sharing at individual, team, and organizational levels
- Role-based access with time limits and audit trails

**Why Deprecated**:
- SPEC-127 provides all SPEC-049 functionality with enhanced capabilities
- SPEC-127 also consolidates SPEC-050 (Cross-Org Sharing) and SPEC-101 (Federation)
- Maintaining multiple specs creates confusion and duplication
- Single unified spec is easier to maintain and implement

---

**Deprecated**: November 1, 2025
**Superseded By**: SPEC-127
**Archived To**: `specs/.archive/deprecated/049-memory-sharing-collaboration-DEPRECATED/`
