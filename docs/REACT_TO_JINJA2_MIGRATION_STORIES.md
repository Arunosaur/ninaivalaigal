# React/Vite to Jinja2 Migration Stories

**Date:** 2025-11-02
**Status:** ✅ **CREATED** - 19 migration stories ready for work
**Total Stories:** 19 (4 admin + 15 customer)

---

## Answer to Your Question

**Q: Are there new stories to convert screens from React/Vite to Jinja2?**
**A:** ✅ **YES** - Just created 19 new migration stories!

---

## Stories Created

### Admin Screens (SPEC-005) - 4 stories

| Story Ref | Subject | Priority | Effort | Status |
|-----------|---------|----------|--------|--------|
| **US#821** | Migrate Admin Login from React/Vite to Jinja2 | P0 | 2-3 hours | New |
| **US#822** | Migrate Analytics Dashboard from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#823** | Migrate User Management from React/Vite to Jinja2 | P0 | 4-6 hours | New |
| **US#824** | Migrate Team Management from React/Vite to Jinja2 | P0 | 4-6 hours | New |

**Total Admin Effort:** 13-17 hours

### Customer Screens (SPEC-146) - 15 stories

| Story Ref | Subject | Priority | Effort | Status |
|-----------|---------|----------|--------|--------|
| **US#825** | Migrate Customer Login from React/Vite to Jinja2 | P0 | 2-3 hours | New |
| **US#826** | Migrate Customer Signup from React/Vite to Jinja2 | P0 | 3-4 hours | New |
| **US#827** | Migrate Dashboard from React/Vite to Jinja2 | P0 | 4-6 hours | New |
| **US#828** | Migrate Memory Browser from React/Vite to Jinja2 | P1 | 6-8 hours | New |
| **US#829** | Migrate Team Dashboard from React/Vite to Jinja2 | P1 | 4-6 hours | New |
| **US#830** | Migrate Team Billing from React/Vite to Jinja2 | P1 | 4-6 hours | New |
| **US#831** | Migrate Team Invoice List from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#832** | Migrate Team Payment Method from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#833** | Migrate Team Usage from React/Vite to Jinja2 | P2 | 4-6 hours | New |
| **US#834** | Migrate Settings from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#835** | Migrate Team Create from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#836** | Migrate Team Invite from React/Vite to Jinja2 | P1 | 3-4 hours | New |
| **US#837** | Migrate Team Upgrade from React/Vite to Jinja2 | P2 | 3-4 hours | New |
| **US#838** | Migrate Discount Non-Profit from React/Vite to Jinja2 | P2 | 3-4 hours | New |
| **US#839** | Migrate Injection Analytics from React/Vite to Jinja2 | P2 | 4-6 hours | New |

**Total Customer Effort:** 50-70 hours

**Grand Total:** 63-87 hours (8-11 days of work)

---

## Story Details

### Each Story Includes:

1. **Objective** - Clear migration goal
2. **Current Implementation** - React/Vite file location
3. **Target Implementation** - FastAPI + Jinja2 approach
4. **Migration Steps** - 5-step process:
   - Create Jinja2 template
   - Create FastAPI route
   - Add interactivity (Alpine.js/HTMX)
   - Test functionality
   - Archive React file
5. **Acceptance Criteria** - Checklist for completion
6. **References** - Links to architecture docs and SPECs
7. **Estimated Effort** - Time estimate
8. **Priority** - P0, P1, or P2

### Tags Added:
- `spec-005` or `spec-146`
- `migration`
- `react-to-jinja2`
- `fastapi`
- `jinja2`
- `templates`
- `admin` or `customer`

---

## Priority Breakdown

### P0 (Critical - 5 stories)
- Admin Login (US#821)
- User Management (US#823)
- Team Management (US#824)
- Customer Login (US#825)
- Customer Signup (US#826)
- Dashboard (US#827)

**Total P0 Effort:** 18-27 hours

### P1 (Important - 10 stories)
- Analytics Dashboard (US#822)
- Memory Browser (US#828)
- Team Dashboard (US#829)
- Team Billing (US#830)
- Team Invoice List (US#831)
- Team Payment Method (US#832)
- Settings (US#834)
- Team Create (US#835)
- Team Invite (US#836)

**Total P1 Effort:** 35-48 hours

### P2 (Nice to Have - 4 stories)
- Team Usage (US#833)
- Team Upgrade (US#837)
- Discount Non-Profit (US#838)
- Injection Analytics (US#839)

**Total P2 Effort:** 13-18 hours

---

## Migration Approach

### For Each Screen:

1. **Reference React Implementation**
   - Use existing React component as design reference
   - Reuse TailwindCSS classes
   - Maintain visual parity

2. **Create Jinja2 Template**
   - Convert React JSX to Jinja2 syntax
   - Extract reusable components to macros/partials
   - Use template inheritance from base.html

3. **Add FastAPI Route**
   - Connect to existing API endpoints
   - Return template with data
   - Handle authentication/authorization

4. **Add Interactivity**
   - Alpine.js for client-side state
   - HTMX for server-side interactions
   - React micro-widget only if truly needed

5. **Archive React File**
   - Move to `/legacy/apps/` when verified
   - Update documentation
   - Remove from active codebase

---

## Next Steps

### Immediate Actions:
1. ✅ **Stories Created** - 19 stories in "New" status
2. ⏳ **Review Stories** - Verify details and priorities
3. ⏳ **Assign Developers** - Assign P0 stories first
4. ⏳ **Start Migration** - Begin with Login pages (P0)

### Recommended Order:
1. **Week 1:** P0 stories (Login, Signup, User/Team Management)
2. **Week 2:** P1 stories (Dashboard, Billing, Settings)
3. **Week 3:** P2 stories (Analytics, Usage, etc.)

### Success Criteria:
- All 19 screens migrated to Jinja2
- React/Vite implementations archived
- Visual parity maintained
- All functionality working
- Documentation updated

---

## Files to Migrate

### Admin Screens:
- `apps/admin-console/src/pages/Login.tsx` → `templates/admin/login.html`
- `apps/admin-console/src/pages/Analytics.tsx` → `templates/admin/analytics.html`
- `apps/admin-console/src/pages/Users.tsx` → `templates/admin/users.html`
- `apps/admin-console/src/pages/Teams.tsx` → `templates/admin/teams.html`

### Customer Screens:
- `apps/customer/src/pages/Login.tsx` → `templates/customer/login.html`
- `apps/customer/src/pages/Signup.tsx` → `templates/customer/signup.html`
- `apps/customer/src/pages/Dashboard.tsx` → `templates/customer/dashboard.html`
- `apps/customer/src/pages/MemoryBrowser.tsx` → `templates/customer/memory_browser.html`
- `apps/customer/src/pages/TeamDashboard.tsx` → `templates/customer/team_dashboard.html`
- `apps/customer/src/pages/TeamBilling.tsx` → `templates/customer/team_billing.html`
- `apps/customer/src/pages/TeamInvoiceList.tsx` → `templates/customer/team_invoice_list.html`
- `apps/customer/src/pages/TeamPaymentMethod.tsx` → `templates/customer/team_payment_method.html`
- `apps/customer/src/pages/TeamUsage.tsx` → `templates/customer/team_usage.html`
- `apps/customer/src/pages/Settings.tsx` → `templates/customer/settings.html`
- `apps/customer/src/pages/TeamCreate.tsx` → `templates/customer/team_create.html`
- `apps/customer/src/pages/TeamInvite.tsx` → `templates/customer/team_invite.html`
- `apps/customer/src/pages/TeamUpgrade.tsx` → `templates/customer/team_upgrade.html`
- `apps/customer/src/pages/DiscountNonProfit.tsx` → `templates/customer/discount_nonprofit.html`
- `apps/customer/src/pages/InjectionAnalytics.tsx` → `templates/customer/injection_analytics.html`

---

## View in Taiga

**Stories:** http://localhost:9000/project/ninaivalaigal/backlog
**Filter by:** `migration` tag or `react-to-jinja2` tag

**Story References:** US#821 - US#839

---

## Summary

✅ **19 new migration stories created**
- 4 admin screens (SPEC-005)
- 15 customer screens (SPEC-146)
- All in "New" status
- Ready for assignment and work
- Comprehensive migration details included

**Total Estimated Effort:** 63-87 hours (8-11 days)

---

**Status:** ✅ Complete
**Next Action:** Assign stories to developers and begin migration work
