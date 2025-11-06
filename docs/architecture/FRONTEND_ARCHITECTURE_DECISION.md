# Frontend Architecture Decision

**Date:** November 2025
**Status:** ✅ **IMPLEMENTED**

---

## Decision: Consolidate to Single Frontend (Vite)

### Problem Statement

We had **two separate frontend applications**:
1. `apps/customer/` - Vite + React Router (port 8101)
2. `frontend-nextjs-customer/` - Next.js 15 (port 3000)

**Issues:**
- Duplication of signup/login/dashboard features
- Next.js is overkill with FastAPI backend
- Maintenance burden with two apps
- Confusion about which app to use

---

## Decision

**Consolidate everything into `apps/customer/` (Vite)**

### Why Vite Instead of Next.js?

With **FastAPI** as the backend:

❌ **Next.js Provides (Not Needed):**
- API Routes → FastAPI handles all API
- Server-Side Rendering → API-based architecture
- Server Components → All client-side
- Middleware for API → FastAPI is the API

✅ **Vite Provides (What We Need):**
- Client-side React components ✅
- Client-side routing (React Router) ✅
- Fast dev experience ✅
- Simple build process ✅

**Conclusion:** Vite is a better fit for API-based architecture.

---

## Migration Completed

### Pages Migrated (8 total)

1. ✅ **TeamCreate** - Team creation wizard
2. ✅ **TeamDashboard** - Team overview with stats
3. ✅ **TeamBilling** - Main billing page
4. ✅ **TeamPaymentMethod** - Stripe Elements integration
5. ✅ **TeamInvoiceList** - Invoice table with pagination
6. ✅ **TeamUsage** - Usage analytics with charts
7. ✅ **TeamInvite** - Invite members page
8. ✅ **TeamUpgrade** - Upgrade to organization

### Routes Added

All routes are now in `apps/customer/src/App.tsx`:

```
/team/create
/team/dashboard
/team/billing
/team/billing/payment-method
/team/billing/invoices
/team/usage
/team/:teamId/invite
/team/:teamId/upgrade
```

---

## Code Patterns Used

### React Router (Not Next.js)

| Pattern | Implementation |
|---------|----------------|
| Navigation | `import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'` |
| Routes | `<Route path="/path" element={<Component />} />` |
| Navigation | `<Link to="/path">` or `navigate('/path')` |
| Params | `const params = useParams<{ id: string }>()` |
| Query Params | `const [searchParams] = useSearchParams()` |

### API Client

Uses `apiClient` from `lib/apiClient.ts` (Axios-based):

```typescript
// GET request
const response = await apiClient.get<Type>('/endpoint');

// POST request
await apiClient.post('/endpoint', { data });

// Error handling
try {
  const response = await apiClient.get('/endpoint');
} catch (err) {
  const errorMsg = getErrorMessage(err, 'Fallback message');
}
```

### Styling Theme

**Dark Theme Applied:**
- Background: `bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900`
- Cards: `glass-surface rounded-2xl border border-gray-700/50`
- Text: `text-white`, `text-slate-400`
- Buttons: `bg-indigo-500 hover:bg-indigo-600`
- Inputs: `bg-slate-900 text-white border border-slate-700`

**Custom CSS Classes (from `index.css`):**
- `glass-surface` - Glass morphism effect
- `brand-gradient` - Brand gradient background
- `gradient-outline` - Gradient border

### Environment Variables

**Vite Pattern:**
```typescript
// Access env var
const key = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;

// Must be prefixed with VITE_ to be exposed to client
```

**Not Next.js Pattern:**
```typescript
// ❌ DON'T USE
const key = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;
```

---

## Stripe Integration

Stripe Elements is integrated in `TeamPaymentMethod.tsx`:

```typescript
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement } from '@stripe/react-stripe-js';

const stripeKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY;
const stripePromise = stripeKey ? loadStripe(stripeKey) : null;
```

**Environment Variable:**
- Name: `VITE_STRIPE_PUBLISHABLE_KEY`
- Location: `.env` file in `apps/customer/`
- Example: `VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...`

---

## Preventing Future Duplication

### Rules

1. **✅ ALWAYS use `apps/customer/` for new features**
   - This is the single source of truth
   - All customer-facing features go here

2. **❌ NEVER create a new frontend app**
   - Don't create `frontend-xyz-customer/`
   - Don't duplicate `apps/customer/` functionality
   - Don't add Next.js unless there's a specific need (SSR/SSG)

3. **📋 Before creating a new app, ask:**
   - Do we need SSR/SSG? → If no, use Vite
   - Do we need API routes? → If no, use Vite
   - Is this customer-facing? → Use `apps/customer/`

### Architecture Decision Process

Before creating a new frontend application:

1. **Check existing apps**
   - Does `apps/customer/` already exist?
   - Can we add the feature there?

2. **Evaluate needs**
   - Do we need Next.js features (SSR, API routes)?
   - Or just client-side React?

3. **Default decision**
   - **Default: Use `apps/customer/`**
   - **Exception: Only if Next.js features are required**

---

## Next.js App Status

**`frontend-nextjs-customer/` is DEPRECATED**

See: `frontend-nextjs-customer/DEPRECATED.md`

**Action Required:**
- Archive or delete `frontend-nextjs-customer/` after confirming migration
- Remove references in documentation
- Update any build/deploy scripts

---

## Related Documentation

- `docs/FRONTEND_CONSOLIDATION_RECOMMENDATION.md` - Original recommendation
- `MIGRATION_PROGRESS.md` - Migration tracking
- `apps/customer/README.md` - Vite app documentation

---

## Summary

✅ **Single Frontend App:** `apps/customer/` (Vite)
✅ **All Features Migrated:** 8 team/billing pages
✅ **Routes Configured:** All team routes added
✅ **Theme Applied:** Dark theme consistency
✅ **Documentation:** Architecture decision documented

**Result:** Simplified architecture, no duplication, easier maintenance.
