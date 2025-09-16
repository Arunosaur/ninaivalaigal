# RBAC Context Sensitivity Policy → Code Mapping

This document maps **sensitivity tiers** into **enforceable code constructs**:  
- Redaction rules (what is scrubbed at capture time)  
- Retention policies (how long data lives)  
- Role-based permissions (who can access/export)

---

## 1. Sensitivity Tiers

| Tier | Description | Examples |
|------|-------------|----------|
| **Tier 0 – Public** | Non-sensitive, safe to share across orgs | General commands, open-source notes, documentation |
| **Tier 1 – Internal** | Low-risk internal ops data | Dev logs, team discussions without PII |
| **Tier 2 – Confidential** | Business-sensitive, restricted to team/org | Design docs, strategy notes, non-public product info |
| **Tier 3 – Restricted** | Personally Identifiable Information (PII) & regulated data | Customer names, emails, internal HR data |
| **Tier 4 – Secrets** | High-risk credentials & tokens, must never be stored in raw form | API keys, JWTs, DB passwords |

---

## 2. Redaction Rules

| Tier | Redaction Applied? | Rule Set |
|------|-------------------|----------|
| Tier 0 | ❌ No | Stored as-is |
| Tier 1 | ❌ Minimal | Basic profanity/PII scan |
| Tier 2 | ✅ Contextual | Regex + entropy for sensitive strings, redact emails/phone numbers |
| Tier 3 | ✅ Strong | Regex + entropy + entity detection (names, IDs), replace with placeholders |
| Tier 4 | ✅ Mandatory | Secrets never persisted; replaced with `<REDACTED_SECRET>` |

---

## 3. Retention Policies

| Tier | Default Retention | Override Allowed? |
|------|------------------|-------------------|
| Tier 0 | Permanent | Yes |
| Tier 1 | 3 years | Yes |
| Tier 2 | 1 year | Yes (shorter only) |
| Tier 3 | 90 days | No (compliance enforced) |
| Tier 4 | 0 (discard at capture) | ❌ Never |

---

## 4. Role Access Matrix

| Role        | Tier 0 | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|-------------|--------|--------|--------|--------|--------|
| **Viewer**  | ✅ Read | ✅ Read | ❌ Deny | ❌ Deny | ❌ Deny |
| **Member**  | ✅ R/W  | ✅ R/W  | ✅ Read | ❌ Deny | ❌ Deny |
| **Maintainer** | ✅ R/W  | ✅ R/W  | ✅ R/W  | ✅ Read (audit only) | ❌ Deny |
| **Admin**   | ✅ R/W  | ✅ R/W  | ✅ R/W  | ✅ R/W (with audit log) | ❌ Deny |
| **Owner**   | ✅ R/W  | ✅ R/W  | ✅ R/W  | ✅ R/W (with audit log) | ❌ Deny |

Legend:  
- ✅ R/W = Read & Write allowed  
- ✅ Read = Read-only access  
- ❌ Deny = No access

---

## 5. Code Enforcement Mapping

| Policy Element | Code Implementation |
|----------------|---------------------|
| **Redaction** | `redaction/` package with detectors → applied in FastAPI middleware, CLI hooks, IDE plugins |
| **Retention** | Database `retention_policy` column; nightly job purges expired rows; enforced in `data-lifecycle` service |
| **Access Control** | `permissions.py` with `@require_permission` decorator; RBAC matrix tests in `tests/test_rbac.py` |
| **Audit Trail** | `audit_events` table with redaction log + access attempts; surfaced in Admin Dashboard |
| **Export Controls** | `export_service` enforces sensitivity checks; Tier ≥3 requires Admin/Owner approval |

---

## 6. Example: Endpoint Enforcement

```python
from rbac.permissions import require_permission, Resource, Action
from redaction.pipeline import redact_payload
from retention.policies import enforce_retention

@app.post("/remember")
@require_permission(Resource.MEMORY, Action.CREATE)
async def remember_entry(entry: MemoryIn, ctx: SubjectContext):
    # Apply redaction
    clean = redact_payload(entry.content, sensitivity=entry.sensitivity_tier)
    
    # Store with retention tag
    record_id = db.insert("memories", {
        "content": clean,
        "sensitivity_tier": entry.sensitivity_tier,
        "retention_policy": enforce_retention(entry.sensitivity_tier),
        "user_id": ctx.user_id,
        "org_id": ctx.org_id,
    })
    
    return {"id": record_id, "status": "stored"}
```

---

## 7. Admin Override Rules
- **Admins/Owners** can grant temporary access to **Tier 3** (Restricted) contexts — all actions logged to audit.  
- **Tier 4 (Secrets)** are never retrievable — even Admins only see `<REDACTED_SECRET>` placeholders.  
- **Permission inheritance**: Team → Org → Owner; highest-precedence role applies.  

---

✅ This creates a **direct line** from:  
- **Docs (sensitivity tiers)** →  
- **Code (redaction + RBAC + retention)** →  
- **Audit/compliance (logs, exports, dashboards)**  

So you can prove: “we don’t just document policies, we enforce them in code.”
