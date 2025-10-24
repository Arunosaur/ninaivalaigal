# Breaking Change Policy

**Purpose:** When and how breaking changes are allowed
**Audience:** All developers

---

## Definition

A **breaking change** is any modification that:
- Causes existing client code to fail
- Changes expected behavior
- Removes functionality
- Makes previously valid data invalid

---

## When Breaking Changes Are Allowed

### ✅ Allowed (with new version)
- Major functionality changes
- Architectural improvements
- Security fixes requiring incompatible changes
- Performance optimizations requiring API changes

### ❌ Never Allowed (in same version)
- Removing fields from v1
- Renaming fields in v1
- Changing types in v1
- Making fields more restrictive in v1

---

## Process for Breaking Changes

### Step 1: Justify
Document why breaking change is necessary:
- Security vulnerability?
- Performance bottleneck?
- Design flaw?
- Business requirement?

### Step 2: Create New Version
```bash
mkdir shared/contracts/my-service/v2
cp -r shared/contracts/my-service/v1/* shared/contracts/my-service/v2/
# Make breaking changes in v2 only
```

### Step 3: Write Migration Guide
```markdown
# Migration: v1 → v2

## Breaking Changes
1. `user_name` renamed to `full_name`
2. `age` now required (was optional)

## Migration Steps
[Step-by-step instructions]

## Timeline
- v2 released: Oct 22
- v1 deprecated: Nov 22 (30 days)
- v1 removed: Dec 22 (60 days)
```

### Step 4: Get Approval
- Architecture review required
- Tech lead sign-off
- Product team notification

### Step 5: Deploy Both Versions
```python
app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")
```

### Step 6: Communicate
- Slack announcement
- Email to stakeholders
- Update documentation
- Add deprecation warnings

### Step 7: Monitor Migration
- Track v1 vs v2 usage
- Contact teams still on v1
- Provide support

### Step 8: Remove Old Version
- After 30-90 days
- Only when v1 usage is zero
- Keep archived for reference

---

## Review Checklist

Before approving breaking change PR:

- [ ] New version created (v2, v3, etc.)
- [ ] Migration guide written
- [ ] Timeline defined (min 30 days)
- [ ] All stakeholders notified
- [ ] Both versions deployed
- [ ] Tests cover both versions
- [ ] Documentation updated
- [ ] Architecture review approved

---

## Examples

### ✅ Good Breaking Change
```
Problem: Security vulnerability in auth flow
Solution: Create v2 with secure flow
Timeline: 90 days migration period
Impact: All clients must upgrade
Justification: Security critical
```

### ❌ Bad Breaking Change
```
Problem: Developer preference for field name
Solution: Rename in v1
Impact: All clients break immediately
Justification: Cosmetic change
→ REJECTED: Use v2 or keep v1 unchanged
```

---

## References
- [VERSIONING.md](./VERSIONING.md)
- [DEPRECATION.md](./DEPRECATION.md)
- [COMPATIBILITY.md](./COMPATIBILITY.md)
