# SPEC-084: Memory Sharing & Transfer Architecture

**Status:** Proposed
**Owner:** Platform Architecture Team
**Effective:** Upon approval
**Related:** SPEC-083 (Product Surface Split), SPEC-026 (Standalone Teams), SPEC-002 (Multi-User Auth)

---

## 1) Purpose

Define comprehensive memory visibility, sharing, and transfer rules across individuals, teams, and organizations with proper permission controls and audit trails.

---

## 2) Core Concepts

### Entity Types
1. **Individual**: Single user account
2. **Team (Standalone)**: Group of individuals without organization
3. **Team (Within Org)**: Team belonging to an organization
4. **Organization**: Formal entity containing individuals and teams

### Memory Scopes
- **Personal Memory**: Associated with individual user, visible only to self
- **Team Memory**: Associated with team context, visible to all team members
- **Organizational Memory**: Associated with org context, visible to all org members
- **Public Memory**: Visible to anyone on platform (knowledge base, tutorials)

---

## 3) Visibility Rules

### Personal Memory
- **Visibility**: Self only
- **Context**: `user_id` only
- **Access**: Owner has full read/write/delete

### Team Memory
- **Visibility**: All team members
- **Context**: `team_id`
- **Access**:
  - Team members: Read/write
  - Team admins: Read/write/delete/share

### Organizational Memory
- **Visibility**: All organization members
- **Context**: `org_id`
- **Access**:
  - Org members: Read/write
  - Org admins: Read/write/delete/share

### Public Memory
- **Visibility**: Anyone on platform
- **Context**: `visibility: public`
- **Access**:
  - Creator: Full control
  - Others: Read-only
- **Classification**:
  - **Public**: Searchable and discoverable
  - **Unlisted**: Accessible via link but not searchable

---

## 4) Sharing & Transfer Permissions

### Individual User
**Can Share/Transfer TO:**
- ✅ Another individual
- ✅ Any team (if member or with invitation)
- ✅ Any organization (if member or with invitation)

**Modes:**
- **Share**: Original owner retains copy (read-only for recipient)
- **Transfer**: Ownership changes (original loses access)
- **Copy**: Duplicate created (both retain independent copies)

### Team Member (Regular)
**Can Share/Transfer:**
- ✅ Own personal memory to team (requires team admin approval)
- ❌ Cannot share team memory externally (admin only)

### Team Admin (Standalone Team)
**Can Share/Transfer:**
- ✅ Team memory to individuals
- ✅ Team memory to other teams
- ✅ Team memory to organizations
- ✅ External sharing allowed (no org restrictions)

### Team Admin (Within Organization)
**Can Share/Transfer:**
- ✅ Team memory within organization
- ❌ Cannot share team memory externally (org admin only)
- ✅ Can promote team memory to org memory (with org admin approval)

### Organization Admin
**Can Share/Transfer:**
- ✅ Org memory to individuals
- ✅ Org memory to teams (internal or external)
- ✅ Org memory to other organizations (M&A scenario)
- ✅ Full external sharing authority

---

## 5) Transfer vs Share Semantics

### Share (Copy with Access)
- Original owner retains full access
- Recipient gets read-only or read-write access (configurable)
- Can be revoked by original owner
- Audit trail maintained

### Transfer (Ownership Change)
- Original owner loses access
- Recipient becomes new owner
- Cannot be revoked (permanent)
- Full audit trail with reason

### Copy (Duplicate)
- Both parties retain independent copies
- No ongoing relationship between copies
- Each can modify their copy independently

---

## 6) Multi-Team & Multi-Org Membership

### User in Multiple Teams
- Can see memory from all teams they belong to
- **Cannot** transfer memory between teams without admin approval
- Cross-team isolation enforced (prevents leaks)

### Team Upgrade: Standalone → Organization
- Existing team memory becomes org memory (configurable)
- Memories shared externally before upgrade remain shared
- External sharing permissions change (now requires org admin)

---

## 7) Approval Workflows

### Personal → Team
- **Auto-approved** if user is team member
- Team admin can accept/reject contribution

### Team → External Entity
- **Requires team admin approval**
- If team within org: **Requires org admin approval**

### Org → External Org
- **Requires org admin approval**
- Recipient org admin must accept
- Compliance check (some orgs may block external sharing)

### Transfer (Any)
- **Requires recipient acceptance**
- Recipient can reject transfer
- Audit log records acceptance/rejection

---

## 8) Revocation & Access Control

### Memory Shared to Team
- If member leaves team: **Access revoked automatically**
- If team disbanded: Shared memory remains with recipient teams/orgs

### Memory Transferred
- **Cannot be revoked** (ownership changed)
- Original owner has no access after transfer

### Org Memory Shared Externally
- Org admin can revoke at any time
- Revocation is immediate
- Recipient notified of revocation

---

## 9) Rate Limits & Abuse Prevention

### Sharing Rate Limits
- **Free Tier**: 10 shares/transfers per day
- **Paid Tier**: 100 shares/transfers per day
- **Enterprise**: Unlimited

### Transfer Rate Limits
- **All Tiers**: 5 transfers per day (prevents abuse)
- **Cooldown**: 24 hours between transfers of same memory

### Monitoring & Alerts
- Platform staff alerted if user exceeds limits
- Suspicious patterns flagged (mass sharing to external orgs)
- Automatic temporary suspension for abuse

---

## 10) Audit Trail Requirements

### Every Share/Transfer Must Log:
```json
{
  "action": "share|transfer|copy",
  "memory_id": "mem_123",
  "from_entity": {"type": "user|team|org", "id": "..."},
  "to_entity": {"type": "user|team|org", "id": "..."},
  "performed_by": "user_456",
  "timestamp": "2024-10-03T14:30:00Z",
  "reason": "Project handoff",
  "permission": "read|read-write",
  "revoked_at": null,
  "revoked_by": null
}
```

### Audit Access
- **Users**: Can see their own share/transfer history
- **Team Admins**: Can see team's share/transfer history
- **Org Admins**: Can see org's share/transfer history
- **Platform Staff**: Can see all audit trails (compliance)

---

## 11) Data Retention After Account Deletion

### User Account Deleted
- **Personal Memory**: Deleted (with 30-day grace period)
- **Shared Memory**: Copied to recipients (they retain access)
- **Transferred Memory**: Recipient retains (ownership already changed)

### Team Disbanded
- **Team Memory**: Deleted (with 30-day grace period)
- **Shared Memory**: Recipients retain copies
- **Members' Personal Memory**: Unaffected

### Organization Dissolved
- **Org Memory**: Deleted (with 90-day grace period for enterprise)
- **Shared Memory**: Recipients retain copies
- **Teams within Org**: Can be converted to standalone teams

---

## 12) M&A Scenario (Organization → Organization)

### Use Case
- Company A acquires Company B
- Need to transfer all of Company B's memory to Company A

### Process
1. Company B org admin initiates transfer
2. Company A org admin accepts transfer
3. All org memory transferred (ownership changes)
4. All teams within Company B become teams within Company A
5. Company B org marked as "acquired" (not deleted)
6. Audit trail maintained for compliance

---

## 13) Implementation Requirements

### Database Schema
- `memory_visibility` table: Tracks who can see what
- `memory_shares` table: Active shares with permissions
- `memory_transfers` table: Transfer history (immutable)
- `sharing_audit_log` table: Complete audit trail

### API Endpoints
- `POST /memory/{id}/share` - Share memory
- `POST /memory/{id}/transfer` - Transfer ownership
- `POST /memory/{id}/copy` - Create copy
- `DELETE /memory/shares/{share_id}` - Revoke share
- `GET /memory/audit` - Get audit trail

### UI Components
- Share dialog with entity selector
- Transfer confirmation modal
- Audit trail viewer
- Revocation management

---

## 14) Security Considerations

### Prevent Data Leaks
- Cross-team isolation enforced
- External sharing requires explicit admin approval
- Rate limits prevent mass exfiltration

### Compliance
- GDPR: Right to be forgotten (delete with grace period)
- SOC 2: Complete audit trails
- HIPAA: Encryption at rest and in transit

### Access Control
- Role-based permissions enforced at API level
- Database-level row security policies
- Regular permission audits

---

## 15) Success Metrics

- ✅ Users can share personal memory with teams
- ✅ Teams can collaborate with shared memory
- ✅ Organizations can manage org-wide knowledge
- ✅ M&A scenarios supported with full transfer
- ✅ Audit trails complete and accessible
- ✅ Rate limits prevent abuse
- ✅ Zero unauthorized access incidents

---

## 16) Open Questions

1. **Public Memory Moderation**: Who can mark memory as public? Approval process?
2. **Memory Versioning**: Should shared memory track versions?
3. **Collaborative Editing**: Can multiple users edit shared memory simultaneously?
4. **Memory Expiration**: Should shares have expiration dates?
5. **Bulk Operations**: Should admins be able to bulk share/transfer?

---

**Next Steps:**
1. Review and approve SPEC-084
2. Design database schema for sharing/transfer
3. Implement API endpoints with permission checks
4. Build UI components for sharing workflows
5. Add comprehensive audit logging
6. Test M&A scenario end-to-end
