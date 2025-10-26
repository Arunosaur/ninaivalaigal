# SPEC-002 Deprecation Notice

**Date**: October 25, 2025
**Status**: 🔴 **DEPRECATED**
**Superseded By**: [SPEC-006: User Management, Authentication & Signup](../../006-user-signup-system/spec.md)

---

## Summary

SPEC-002 (User Management & Authentication) has been **deprecated and archived**. All functionality described in this SPEC has been superseded by the more comprehensive SPEC-006.

---

## Deprecation Rationale

### Original SPEC-002 Scope
- Basic user management
- JWT authentication
- Simple signup/login flows
- 85% implemented (incomplete)

### Why Superseded by SPEC-006

**SPEC-006** provides a **complete, production-ready** implementation that includes:

1. **Extended Authentication**:
   - JWT token generation with extended claims
   - RBAC role integration
   - Team membership tracking
   - Organization context

2. **Comprehensive Signup Flows**:
   - Individual user signup
   - Organization signup with admin creation
   - Email verification
   - Password reset workflows

3. **Production Features**:
   - Token refresh mechanism
   - Session management (SPEC-017)
   - Security middleware (SPEC-008)
   - Health monitoring integration

4. **Enterprise Capabilities**:
   - Multi-org support
   - Team invitations (SPEC-016)
   - RBAC policy enforcement (SPEC-009)
   - Audit trails

---

## Migration Path

**From SPEC-002 → SPEC-006**

### Authentication (Fully Migrated ✅)
- JWT generation: Enhanced with RBAC claims
- Login flow: Extended with team/org context
- Token usage: Backward compatible

### User Management (Fully Migrated ✅)
- User creation: Now supports org/team context
- Password hashing: bcrypt maintained
- Role assignment: Integrated with RBAC

### New Features in SPEC-006
- Email verification
- Password reset
- Organization registration
- Token refresh endpoints

---

## Current Status

### SPEC-002
- **Status**: Deprecated (archived)
- **Implementation**: 85% (incomplete)
- **Location**: `.archive/002a-user-management-basic-DEPRECATED/`
- **Use**: Historical reference only

### SPEC-006
- **Status**: ✅ Complete (Authoritative)
- **Implementation**: 100% production-ready
- **Location**: `006-user-signup-system/`
- **Use**: Current specification for all auth/user operations

---

## References

### Authoritative SPEC
- **[SPEC-006: User Management, Authentication & Signup](../../006-user-signup-system/spec.md)**

### Related SPECs
- **SPEC-009**: RBAC Policy Enforcement
- **SPEC-014**: Authentication and Authorization
- **SPEC-016**: Team Invitations
- **SPEC-017**: Session Management
- **SPEC-008**: Security Middleware

### Implementation
- Core API: `http://localhost:13390/auth/*`
- Endpoints: `/auth/signup/*`, `/auth/login`, `/auth/refresh`

---

## For SPEC Analysis

**Recommendation**: **Skip SPEC-002** and proceed directly to **SPEC-003: Core API Architecture**

**Active SPECs in Sequence**:
1. ✅ SPEC-000: Vision & Scope (Validated)
2. ✅ SPEC-001: Core Memory System (Validated and Sealed)
3. 🔴 SPEC-002: **DEPRECATED** → See SPEC-006
4. ⏭️ SPEC-003: Core API Architecture (Next for analysis)
5. SPEC-004: Team Collaboration
6. SPEC-005: Admin Dashboard
7. SPEC-006: User Management, Authentication & Signup (Supersedes SPEC-002)

---

**Note**: This deprecation is part of SPEC consolidation efforts (October 2025) to eliminate redundant specifications and establish clear ownership.

**Archive Date**: October 13, 2025
**Last Active**: Pre-October 2025
**Replacement**: SPEC-006 (Complete)
