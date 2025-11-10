# frontend-nextjs-customer/ - DEPRECATED

**Deprecated Date**: 2025-01-31
**Deprecated By**: Developer F
**Reason**: SPEC-122 (Customer Frontend Rollout) is DEPRECATED, features migrated to `apps/customer/`

---

## Deprecation Details

**Original Purpose**: Next.js 15 customer-facing application

**Replaced By**: `apps/customer/` (Vite + React Router)

**Migration Status**: ✅ **All features migrated** (per `frontend-nextjs-customer/DEPRECATED.md`)

**Migrated Features**:
1. ✅ Team Creation (`/team/create`)
2. ✅ Team Dashboard (`/team/dashboard`)
3. ✅ Team Billing (`/team/billing`)
4. ✅ Payment Method (`/team/billing/payment-method`)
5. ✅ Invoice List (`/team/billing/invoices`)
6. ✅ Usage Analytics (`/team/usage`)
7. ✅ Team Invite (`/team/:teamId/invite`)
8. ✅ Team Upgrade (`/team/:teamId/upgrade`)

---

## SPEC References

- **SPEC-122**: Customer Frontend Rollout
  - **Status**: 🔴 DEPRECATED (Next.js + Vercel deployment)
  - **File**: `specs/122-customer-frontend-rollout/README.md`
  - **Replaced By**: FastAPI templates + static hosting

- **SPEC-116**: Internal Frontend Migration
  - **Status**: 🔴 DEPRECATED (Next.js split architecture)
  - **File**: `specs/116-internal-frontend-migration/README.md`

---

## Active Frontend

**Use**: `apps/customer/` instead
- **Tech Stack**: Vite + React Router
- **Port**: 8101 (dev)
- **Location**: `apps/customer/`

---

## Archive Location

This folder was moved from: `frontend-nextjs-customer/`
To: `.archive/deprecated/frontend-nextjs-customer-2025-01-31/`

**Original Size**: ~88 files

---

**Status**: ✅ Archived - All features available in `apps/customer/`
