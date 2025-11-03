# ⚠️ SPEC-049: DEPRECATED - SEE SPEC-127

**❌ DEPRECATION NOTICE**: This SPEC has been **deprecated** as of **November 1, 2025**.

**Reason**: Superseded by [SPEC-127: Context Bridge & Memory Federation System](../127-context-bridge-system/README.md)

**Redirect**: All memory sharing and collaboration work is now tracked under **SPEC-127**.

**Action Required**:
- ✅ Use [SPEC-127](../127-context-bridge-system/README.md) as the authoritative specification
- ✅ Reference SPEC-127 in all future documentation and Taiga stories
- ✅ Do not implement features from this SPEC - use SPEC-127 instead

---

# ~~SPEC-049: Memory Sharing & Collaboration~~ (DEPRECATED)

**Status**: ❌ **DEPRECATED** (Was: ✅ DRAFT COMPLETE)
**Superseded By**: SPEC-127
**Date Deprecated**: November 1, 2025

---

## Objective:
Extend the memory access control model (SPEC-043) into a full-fledged collaboration system that enables users to share, delegate, and collaborate on memory tokens at individual, team, and organizational levels.

## Key Features:
- 🔐 **Role-Based Sharing**: Share individual memories or collections with specific roles (Viewer, Editor, Commenter)
- 👥 **User & Team Collaboration**: Invite users or groups, assign roles
- 📆 **Time-Limited Access**: Share with expiry dates or usage limits
- 🔁 **Revocation System**: Instantly revoke shared access tokens
- 📜 **Audit Trails**: Record who shared what, with whom, and when
- 📊 **Sharing Dashboard**: UI to manage all shared memories
- 📎 **Deep Links**: Generate links with scoped access

## Implementation Plan:
- Extend ACL table with `shared_by`, `shared_with`, `expires_at`, `audit_log`
- Create share/unshare/invite/revoke APIs
- Build share-dashboard interface (CLI + future GUI)
- Add context-aware invite tokens (optional login auto-link)
- Integrate with SPEC-045 for session-bound collaboration context

## Future Expansion:
- 📌 Memory pinning across collaborators
- 💬 Comment threads on memory tokens
- 🔁 Re-share chains with auditing
