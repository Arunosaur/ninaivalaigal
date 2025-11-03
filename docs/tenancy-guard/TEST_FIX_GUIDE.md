# TenancyGuard Integration Test Fix Guide

**Date**: November 2, 2025
**Status**: ✅ Migration applied, test updates needed

---

## ✅ FIXED: Team `origin` Column

**Migration Applied**: `0131_add_origin_to_teams`

The `origin` column has been added to the `teams` table. This issue is resolved.

---

## 🔧 REMAINING: Context Foreign Key Issue

### Problem

The `Context` model has a foreign key constraint to `organizations` table. Tests fail when trying to create contexts without organizations.

### Solution

Update integration tests to create organizations before creating contexts.

### Example Test Fix

**Before** (fails):
```python
def test_context_operations():
    # This fails because no organization exists
    context = Context(name="test_context", user_id=user_id)
    db.add(context)
    db.commit()  # ❌ Foreign key constraint violation
```

**After** (works):
```python
def test_context_operations():
    # 1. Create organization first
    org = Organization(
        name="Test Org",
        owner_id=user_id
    )
    db.add(org)
    db.commit()

    # 2. Now create context with organization
    context = Context(
        name="test_context",
        user_id=user_id,
        organization_id=org.id  # ✅ Foreign key satisfied
    )
    db.add(context)
    db.commit()  # ✅ Works!
```

---

## Test Update Checklist

For each test that creates `Context` objects:

- [ ] Check if test creates an `Organization` first
- [ ] If not, add organization creation before context creation
- [ ] Set `context.organization_id = org.id`
- [ ] Commit organization before creating context

---

## Alternative: Make organization_id Nullable

If contexts don't always need organizations, you can make the foreign key nullable:

### Option 1: Alembic Migration

```python
# Create new migration
alembic revision -m "make_context_organization_nullable"

# In the migration file:
def upgrade():
    op.alter_column('contexts', 'organization_id',
                   existing_type=sa.UUID(),
                   nullable=True)

def downgrade():
    op.alter_column('contexts', 'organization_id',
                   existing_type=sa.UUID(),
                   nullable=False)
```

### Option 2: Update Model

```python
class Context(Base):
    __tablename__ = "contexts"

    organization_id = Column(UUID(as_uuid=True),
                            ForeignKey("organizations.id"),
                            nullable=True)  # ✅ Make optional
```

---

## Recommended Approach

**For TenancyGuard tests**: Update tests to create organizations first (more realistic)

**For production**: Decide if contexts always need organizations:
- If YES: Keep current schema, update tests
- If NO: Make `organization_id` nullable via migration

---

## Summary

✅ **Team `origin` column**: FIXED (migration applied)
🔧 **Context organizations**: Update tests to create orgs first

**Next Steps**:
1. Update integration tests to create organizations before contexts
2. Run tests again
3. All TenancyGuard tests should pass

---

**Questions?** Contact the team or check:
- `/alembic/versions/0131_add_origin_to_teams.py` - Applied migration
- TenancyGuard integration test files
