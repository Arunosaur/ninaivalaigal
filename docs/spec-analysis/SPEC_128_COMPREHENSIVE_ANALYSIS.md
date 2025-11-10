# SPEC-128 Comprehensive Analysis: Memory Sharing & Transfer Architecture

**Date:** January 2025
**Status:** ⚠️ **Partially Implemented** (30% implemented)

---

## 🎯 Executive Summary

**SPEC-128 Identity:** Memory Sharing & Transfer Architecture
**SPEC_INDEX.md Status:** Proposed
**Actual Implementation Status:** ⚠️ **30% - Partially Implemented**
**SPEC README Status:** Proposed (document header says SPEC-084, renumbered to 128)
**Taiga Stories:** US#599 mentioned (needs verification)

**Note:** This SPEC was renumbered from SPEC-084 to SPEC-128. The document header still says "SPEC-084" but the directory is `128-memory-sharing`.

---

## 📊 Implementation Status

### Current State: 30% Implemented

**SPEC-128 defines comprehensive memory visibility, sharing, and transfer rules. Basic sharing infrastructure exists (via SPEC-043 and SPEC-049), but transfer operations, approval workflows, and rate limits are missing.**

### ✅ Partially Implemented (30%)

**Basic Sharing Infrastructure:**
- ✅ **Memory ACL System** (SPEC-043) - Complete
  - POST `/acl/memory/{memory_id}/share` - Share memory with user
  - DELETE `/acl/memory/{memory_id}/share/{user_id}` - Revoke access
  - Visibility levels: PRIVATE, TEAM, ORGANIZATION, PUBLIC
  - Access levels: NONE, READ, WRITE, ADMIN, OWNER
- ✅ **Sharing Contracts** (SPEC-049) - Partially implemented
  - `MemorySharingContractManager` class exists
  - `sharing_contracts.py` with contract management
  - Visibility levels: PRIVATE, SHARED, TEAM, ORG, PUBLIC
  - Share permissions: VIEW, COMMENT, EDIT, SHARE, ADMIN
  - Contract status: PENDING, ACTIVE, EXPIRED, REVOKED, REJECTED
- ✅ **Basic Share Endpoint** - `POST /memory/{memory_id}/share` exists (via ACL)

### ❌ Missing (70%)

**Database Schema:**
- ❌ `memory_visibility` table - **NOT CREATED**
- ❌ `memory_shares` table - **NOT CREATED** (using ACL tables instead)
- ❌ `memory_transfers` table - **NOT CREATED**
- ❌ `sharing_audit_log` table - **NOT CREATED** (basic audit exists, but not comprehensive)

**API Endpoints:**
- ❌ POST `/memory/{id}/transfer` - **NOT IMPLEMENTED**
- ❌ POST `/memory/{id}/copy` - **NOT IMPLEMENTED**
- ❌ GET `/memory/audit` - **NOT IMPLEMENTED** (comprehensive audit trail)

**Core Features:**
- ❌ **Transfer Ownership** - **NOT IMPLEMENTED**
  - Ownership change functionality
  - Transfer history tracking
  - M&A scenario support
  - Bulk transfer operations
- ❌ **Copy Operation** - **NOT IMPLEMENTED**
  - Duplicate memory creation
  - Independent copy management
- ❌ **Approval Workflows** - **NOT IMPLEMENTED**
  - Personal → Team approval
  - Team → External entity approval
  - Org → External org approval
  - Transfer acceptance/rejection
- ❌ **Rate Limits** - **NOT IMPLEMENTED**
  - Sharing rate limits (10/100/unlimited per tier)
  - Transfer rate limits (5 per day)
  - Abuse prevention monitoring
  - Automatic suspension for abuse
- ❌ **Comprehensive Visibility Rules** - **PARTIAL**
  - Personal/Team/Org/Public visibility rules exist (via ACL)
  - But transfer/copy rules, approval workflows missing
- ❌ **M&A Scenario Support** - **NOT IMPLEMENTED**
  - Org-to-org transfer
  - Team migration
  - Bulk transfer operations
  - Organization dissolution handling

---

## 🔗 Related SPECs & Overlaps

### Overlap Analysis

| SPEC | Title | Status | Overlap Assessment |
|------|-------|--------|-------------------|
| **SPEC-043** | Memory ACL System | Complete | ✅ **COMPLEMENTARY** - SPEC-043 provides access control enforcement, SPEC-128 defines sharing/transfer rules |
| **SPEC-049** | Memory Sharing Collaboration | **DEPRECATED** | ⚠️ **PARTIAL OVERLAP** - Some code exists (sharing_contracts.py), but SPEC-049 is deprecated in favor of SPEC-127 |
| **SPEC-127** | Context Bridge System | Not Implemented | ⚠️ **POTENTIAL OVERLAP** - Both deal with sharing, but different scopes:
  - SPEC-127: Cross-context sharing (Team ↔ Team) with Reference/Clone/Hybrid modes
  - SPEC-128: Visibility rules and transfer semantics (Individual, Team, Org, Public)
  - **Assessment**: SPEC-128 is policy layer, SPEC-127 is technical implementation layer |

### Key Distinctions

**SPEC-128 (Policy/Rules Layer):**
- Defines **WHAT** can be shared (visibility rules)
- Defines **WHO** can share/transfer (permissions)
- Defines **HOW** sharing works semantically (Share vs Transfer vs Copy)
- Defines **WHEN** sharing needs approval (approval workflows)
- Defines **WHERE** data goes (retention after deletion)
- Defines **LIMITS** (rate limits, abuse prevention)

**SPEC-127 (Technical Implementation Layer):**
- Implements **HOW** sharing works technically (Reference/Clone/Hybrid modes)
- Implements trust scoring for sharing decisions
- Implements GraphOps integration for relationship tracking
- Cross-context bridge creation and management

**SPEC-043 (Access Control Layer):**
- Enforces **WHO** can access (ACL enforcement)
- Provides token-based access control
- Provides visibility-based access

**Relationship:** They are complementary layers:
- **SPEC-128**: Policy definition (what can be shared, transfer rules)
- **SPEC-043**: Access enforcement (who can access)
- **SPEC-127**: Technical implementation (how sharing works with bridges)

**Conclusion:** They should work together, not compete. SPEC-128 defines the rules, SPEC-043 enforces them, and SPEC-127 implements the technical mechanisms.

---

## 📋 Core Features

### 1. Visibility Rules

| Scope | Visibility | Context | Access | Status |
|-------|------------|---------|--------|--------|
| **Personal** | Self only | `user_id` | Owner: Full control | ✅ Implemented (via ACL) |
| **Team** | All team members | `team_id` | Members: Read/write, Admins: Full control | ✅ Implemented (via ACL) |
| **Org** | All org members | `org_id` | Members: Read/write, Admins: Full control | ✅ Implemented (via ACL) |
| **Public** | Anyone on platform | `visibility: public` | Creator: Full control, Others: Read-only | ✅ Implemented (via ACL) |

### 2. Sharing Operations

| Operation | Description | Status |
|-----------|------------|--------|
| **Share** | Original owner retains copy, recipient gets access | ✅ Implemented (via ACL) |
| **Transfer** | Ownership changes, original loses access | ❌ Not implemented |
| **Copy** | Duplicate created, both retain independent copies | ❌ Not implemented |

### 3. Approval Workflows

| Workflow | Approval Required | Status |
|----------|------------------|--------|
| Personal → Team | Auto-approved if member, admin can accept/reject | ❌ Not implemented |
| Team → External | Team admin approval (org admin if within org) | ❌ Not implemented |
| Org → External Org | Org admin approval + recipient acceptance | ❌ Not implemented |
| Transfer (Any) | Recipient acceptance required | ❌ Not implemented |

### 4. Rate Limits

| Limit Type | Free Tier | Paid Tier | Enterprise | Status |
|------------|-----------|-----------|------------|--------|
| Sharing | 10/day | 100/day | Unlimited | ❌ Not implemented |
| Transfer | 5/day (all tiers) | 5/day | 5/day | ❌ Not implemented |
| Cooldown | 24h between transfers | 24h | 24h | ❌ Not implemented |

---

## 📊 Database Schema Requirements

### Tables Needed:

1. **memory_visibility**
   - memory_id (UUID, FK)
   - visibility_level (enum: personal, team, org, public)
   - context_id (UUID)
   - created_at, updated_at

2. **memory_shares**
   - share_id (UUID, PK)
   - memory_id (UUID, FK)
   - from_entity (JSON: {type, id})
   - to_entity (JSON: {type, id})
   - permission (enum: view, comment, edit, share, admin)
   - status (enum: pending, active, expired, revoked)
   - created_at, expires_at

3. **memory_transfers**
   - transfer_id (UUID, PK)
   - memory_id (UUID, FK)
   - from_entity (JSON: {type, id})
   - to_entity (JSON: {type, id})
   - transferred_at
   - transferred_by (UUID, FK)
   - accepted_at
   - accepted_by (UUID, FK)
   - reason (text)
   - **Immutable** (no updates allowed)

4. **sharing_audit_log**
   - audit_id (UUID, PK)
   - action (enum: share, transfer, copy, revoke)
   - memory_id (UUID, FK)
   - from_entity (JSON)
   - to_entity (JSON)
   - performed_by (UUID, FK)
   - timestamp
   - reason (text)
   - revoked_at, revoked_by (nullable)

**Status:** ❌ None of these tables exist (using ACL tables instead)

---

## 🔒 Security Considerations

### Prevent Data Leaks
- Cross-team isolation enforced - ✅ (via ACL)
- External sharing requires explicit admin approval - ❌ Not implemented
- Rate limits prevent mass exfiltration - ❌ Not implemented

### Compliance
- GDPR: Right to be forgotten (delete with grace period) - ⚠️ Partial (30-day grace period mentioned, not implemented)
- SOC 2: Complete audit trails - ⚠️ Partial (basic audit exists, not comprehensive)
- HIPAA: Encryption at rest and in transit - ✅ (assumed via infrastructure)

### Access Control
- Role-based permissions enforced at API level - ✅ (via ACL)
- Database-level row security policies - ⚠️ Unknown
- Regular permission audits - ❌ Not implemented

---

## 🚨 Issues Found

### 1. Status Mismatch

**SPEC_INDEX.md:** "Proposed"
**SPEC README:** "Proposed"
**Actual Status:** 30% implemented

**Recommendation:** Update SPEC_INDEX.md to reflect "Partially Implemented (30%)"

### 2. Document Header Mismatch

**Issue:** Document header says "SPEC-084" but directory is "128-memory-sharing"

**Recommendation:** Update document header to say "SPEC-128"

### 3. Overlap with SPEC-127

**Issue:** Both SPECs deal with sharing, potential confusion

**Recommendation:**
- Document relationship clearly in both SPECs
- SPEC-128: Policy layer (WHAT can be shared)
- SPEC-127: Technical layer (HOW sharing works)

### 4. Missing Story

**Issue:** US#599 mentioned but not verified

**Recommendation:** Verify US#599 and create/update stories for missing functionality

---

## ✅ Recommendations

### 1. Immediate Actions

1. **Update SPEC_INDEX.md** - Change status from "Proposed" to "Partially Implemented (30%)"
2. **Update SPEC README** - Fix document header (SPEC-084 → SPEC-128)
3. **Clarify SPEC-127 Relationship** - Document how SPEC-128 and SPEC-127 work together
4. **Verify US#599** - Check if story exists and update if needed

### 2. Implementation Priority

**Phase 1: Transfer & Copy (Highest Priority)**
- Implement POST `/memory/{id}/transfer`
- Implement POST `/memory/{id}/copy`
- Create `memory_transfers` table
- Transfer history tracking

**Phase 2: Approval Workflows**
- Approval system for Personal → Team
- Approval system for Team → External
- Approval system for Org → External
- Transfer acceptance/rejection

**Phase 3: Rate Limits & Audit**
- Rate limit enforcement
- Abuse prevention monitoring
- Comprehensive audit trail

**Phase 4: M&A Support**
- Org-to-org transfer
- Bulk transfer operations
- Team migration

### 3. Dependencies

**Blocking:**
- SPEC-043 (ACL) - ✅ Complete (ready)
- SPEC-026 (Standalone Teams) - Needs verification
- SPEC-002 (Multi-User Auth) - Needs verification

**No Blockers:** Core dependencies are complete, ready to start implementation

---

## 📝 Conclusion

**SPEC-128 is a policy/rules layer that defines comprehensive memory visibility, sharing, and transfer rules. Basic sharing infrastructure exists (30%), but transfer operations, approval workflows, and rate limits are missing (70%).**

**Key Findings:**
- ✅ Basic sharing via ACL exists
- ✅ Visibility levels implemented
- ❌ Transfer and copy operations missing
- ❌ Approval workflows missing
- ❌ Rate limits missing
- ⚠️ Overlap with SPEC-127 needs clarification
- ⚠️ Status mismatch in documentation

**Action Required:**
1. Verify/create Taiga stories for missing functionality
2. Update documentation to reflect actual status
3. Clarify relationship with SPEC-127
4. Begin Phase 1 implementation (transfer and copy)
