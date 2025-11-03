# SPEC-050 Deprecation Notice

**⚠️ DEPRECATION NOTICE**: This SPEC has been **deprecated** as of **November 1, 2025**.

**Reason**: Superseded by [SPEC-127: Context Bridge & Memory Federation System](../127-context-bridge-system/README.md)

**Redirect**: All cross-organization memory sharing work is now tracked under **SPEC-127**.

**Action Required**:
- ✅ Use [SPEC-127](../127-context-bridge-system/README.md) as the authoritative specification
- ✅ Reference SPEC-127 in all future documentation and Taiga stories
- ✅ Do not implement features from this SPEC - use SPEC-127 instead

---

## What SPEC-127 Provides

SPEC-127 consolidates and extends SPEC-050 with:

### From SPEC-050 (Preserved):
- ✅ Org-to-org token bridge
- ✅ Visibility scopes (EXTERNAL-READ, EXTERNAL-REFERENCE, EXTERNAL-EMBED)
- ✅ Shared link tokens with domain+token verification
- ✅ Sharing policy framework (org-level allow/deny filters)
- ✅ Audit ledger (timestamped and signed)
- ✅ Sandbox mode (view-only rendering)
- ✅ Compliance tags
- ✅ Verification headers

### Enhanced in SPEC-127:
- ✨ **Reference vs Clone modes** (live link vs isolated copy)
- ✨ **Security & trust scoring system** (0-100 dynamic scoring)
- ✨ **Detailed GraphOps integration** architecture
- ✨ **Unified API surface** (single entry point)
- ✨ **Cross-context graph linking** (federated queries)
- ✨ **User/team collaboration** (consolidates SPEC-049)

---

## Migration Path

If you have work in progress based on SPEC-050:

1. **Review SPEC-127** to understand the unified architecture
2. **Map your features** to SPEC-127 capabilities
3. **Update references** from SPEC-050 to SPEC-127
4. **Use SPEC-127 APIs** instead of SPEC-050 designs

---

## Historical Context

**Original SPEC-050 Scope**:
- Enable controlled sharing of memory tokens across organizational boundaries
- Preserve isolation, compliance, and ownership integrity
- Support partner orgs, educators, cross-pod AI context sharing

**Why Deprecated**:
- SPEC-127 provides all SPEC-050 functionality with enhanced capabilities
- SPEC-127 also consolidates SPEC-049 (Memory Collaboration) and SPEC-101 (Federation)
- Maintaining multiple specs creates confusion and duplication
- Single unified spec is easier to maintain and implement

---

**Deprecated**: November 1, 2025
**Superseded By**: SPEC-127
**Archived To**: `specs/.archive/deprecated/050-cross-org-memory-sharing-DEPRECATED/`
