# ⚠️ DEPRECATED: This Frontend is No Longer Active

**Date Deprecated:** November 2025
**Status:** All features migrated to `apps/customer/`

---

## What Happened?

This Next.js frontend (`frontend-nextjs-customer/`) has been **consolidated** into the main Vite app (`apps/customer/`).

**Reason:** Next.js was overkill for our FastAPI-based architecture. We don't need SSR, API routes, or server components—just client-side React.

---

## Migration Status

✅ **All features migrated:**

1. Team Creation (`/team/create`)
2. Team Dashboard (`/team/dashboard`)
3. Team Billing (`/team/billing`)
4. Payment Method (`/team/billing/payment-method`)
5. Invoice List (`/team/billing/invoices`)
6. Usage Analytics (`/team/usage`)
7. Team Invite (`/team/:teamId/invite`)
8. Team Upgrade (`/team/:teamId/upgrade`)

**New Location:** `apps/customer/src/pages/Team*.tsx`

---

## Active Frontend

**Use this instead:** `apps/customer/`

- **Tech Stack:** Vite + React Router
- **Port:** 8101 (dev)
- **Routes:** All team/billing routes migrated
- **Theme:** Dark theme with glass-surface styling

---

## Do Not Use

❌ **Don't create new features here**
❌ **Don't fix bugs (unless critical)**
❌ **Don't update dependencies**

---

## Action Required

**This directory can be:**
1. **Archived** - Move to `archive/frontend-nextjs-customer/`
2. **Deleted** - Remove after confirming migration is complete

**Before deleting:**
- ✅ Confirm all features work in `apps/customer/`
- ✅ Verify no references in CI/CD
- ✅ Update any documentation

---

## Questions?

See: `docs/FRONTEND_ARCHITECTURE_DECISION.md`
