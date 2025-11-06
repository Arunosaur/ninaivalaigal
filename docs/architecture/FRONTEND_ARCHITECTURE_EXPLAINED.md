# Frontend Architecture Explanation

## Overview

The project has **two separate frontend applications** that serve different purposes:

1. **`apps/customer/`** - Vite + React Router app (legacy/migration in progress)
2. **`frontend-nextjs-customer/`** - Next.js 15 app (modern, actively developed)

---

## Applications Comparison

### 1. `apps/customer/` (Vite/React Router)

**Location:** `/apps/customer/`
**Tech Stack:**
- React 18
- Vite (build tool)
- React Router (client-side routing)
- Port: **8101**

**Purpose:**
- Original customer-facing app
- Contains signup, login, dashboard, memory browser
- Being migrated to Next.js gradually

**Features:**
- ✅ Signup (`/signup`)
- ✅ Login (`/login`)
- ✅ Dashboard (`/dashboard`)
- ✅ Memory Browser (`/memory-browser`)
- ✅ Teams (`/teams`)
- ✅ Settings (`/settings`)

**Routes:**
```
/ → Landing page
/signup → Signup form
/login → Login form
/dashboard → User dashboard (protected)
/memory-browser → Memory browser (protected)
/teams → Teams page (protected)
/settings → Settings page (protected)
```

---

### 2. `frontend-nextjs-customer/` (Next.js 15)

**Location:** `/frontend-nextjs-customer/`
**Tech Stack:**
- Next.js 15.5.4 (App Router)
- React 19
- Turbopack (fast bundler)
- Port: **3000**

**Purpose:**
- Modern Next.js app for new features
- Team management and billing features
- Built with App Router (server components support)

**Features:**
- ✅ Signup (`/signup`) - **DUPLICATE of apps/customer**
- ✅ Login (`/login`) - **DUPLICATE of apps/customer**
- ✅ Dashboard (`/dashboard`) - **DUPLICATE of apps/customer**
- ✅ Memories (`/memories`)
- ✅ **Team Creation** (`/team/create`) - **NEW**
- ✅ **Team Dashboard** (`/team/dashboard`) - **NEW**
- ✅ **Team Billing** (`/team/billing`) - **NEW**
- ✅ **Payment Method** (`/team/billing/payment-method`) - **NEW**
- ✅ **Team Usage** (`/team/usage`) - **NEW**
- ✅ **Team Invites** (`/team/[teamId]/invite`) - **NEW**

**Routes:**
```
/ → Landing page
/signup → Signup form (DUPLICATE)
/login → Login form (DUPLICATE)
/dashboard → User dashboard (DUPLICATE)
/memories → Memory list
/team/create → Team creation wizard (NEW)
/team/dashboard → Team dashboard (NEW)
/team/billing → Billing management (NEW)
/team/billing/payment-method → Stripe payment method (NEW)
/team/billing/invoices → Invoice list (NEW)
/team/usage → Usage analytics (NEW)
/team/[teamId]/invite → Invite members (NEW)
/team/[teamId]/upgrade → Upgrade to org (NEW)
```

---

## Why Two Separate Apps?

### Historical Context

1. **`apps/customer/`** was built first using Vite + React Router
2. **Migration to Next.js** was planned (SPEC-122)
3. **New features** (teams, billing) were built in Next.js instead of migrating everything
4. **Result:** Two apps running in parallel

### Current State

- **Signup/Login:** Duplicated in both apps
- **Dashboard:** Duplicated in both apps
- **Teams/Billing:** Only in Next.js app
- **Memory Browser:** Only in Vite app

### Migration Status

- ✅ Next.js app scaffolded
- ✅ New features (teams) built in Next.js
- ⏳ Old features still in Vite app
- ⏳ Full migration pending

---

## Running Both Apps

### Start Vite App (apps/customer/)
```bash
cd apps/customer
npm run dev
# Runs on http://localhost:8101
```

### Start Next.js App (frontend-nextjs-customer/)
```bash
cd frontend-nextjs-customer
npm run dev
# Runs on http://localhost:3000
```

### Why Different Ports?

- **Port 8101:** Vite dev server default (or custom configured)
- **Port 3000:** Next.js default dev port
- Both can run simultaneously

---

## Recommendations

### Option 1: Complete Migration (Recommended)
- Migrate all features from `apps/customer/` to `frontend-nextjs-customer/`
- Deprecate `apps/customer/`
- Single source of truth

### Option 2: Feature Split
- Keep `apps/customer/` for core features (signup, login, dashboard)
- Use `frontend-nextjs-customer/` for new features (teams, billing)
- **Problem:** Duplication and confusion

### Option 3: Consolidate Now
- Move teams/billing features to `apps/customer/`
- **Problem:** Doesn't leverage Next.js benefits

---

## Current Issue: Payment Method Page

**Problem:** Cannot reach `http://localhost:3000/team/billing/payment-method`

**Solutions:**

1. **Check if Next.js server is running:**
   ```bash
   cd frontend-nextjs-customer
   npm run dev
   ```

2. **Verify port 3000:**
   ```bash
   lsof -ti:3000
   # Should show a process ID
   ```

3. **Check for build errors:**
   ```bash
   cd frontend-nextjs-customer
   npm run build
   ```

4. **Try alternative port:**
   ```bash
   cd frontend-nextjs-customer
   PORT=3001 npm run dev
   ```

---

## Summary

- **Two apps** because of migration strategy
- **Signup/login duplicated** in both apps
- **Teams/billing** only in Next.js app
- **Payment method page** is in Next.js app (port 3000)
- **Need to start Next.js dev server** to access it
