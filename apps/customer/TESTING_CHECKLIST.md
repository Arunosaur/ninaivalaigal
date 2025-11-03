# Testing Checklist - Team/Billing Features Migration

**Date:** November 2025
**Status:** Ready for Testing

---

## Pre-Testing Setup

- [ ] Backend API server running (port 13390)
- [ ] Database accessible and seeded (if needed)
- [ ] User account created and logged in
- [ ] `.env` file configured with `VITE_STRIPE_PUBLISHABLE_KEY` (if testing payment methods)

---

## Team Management Pages

### 1. Team Creation (`/team/create`)

- [ ] Page loads without errors
- [ ] All 3 steps of wizard display correctly
- [ ] Step 1: Team name validation works (min 2 chars, max 100)
- [ ] Step 1: Max members validation works (2-50 range)
- [ ] Step 2: Can add member invitations with email and role
- [ ] Step 2: Email validation works
- [ ] Step 2: Can remove invitations
- [ ] Step 3: Review page shows all entered data
- [ ] Submit creates team successfully
- [ ] Redirects to team dashboard after creation
- [ ] Error messages display correctly for failed creation
- [ ] Navigation (Back, Cancel) works correctly
- [ ] Dark theme styling is consistent

### 2. Team Dashboard (`/team/dashboard`)

- [ ] Page loads without errors
- [ ] Displays team name and stats correctly
- [ ] Stats cards show: Members, Memories, Contexts, API Calls
- [ ] Team members list displays correctly
- [ ] Team information section shows invite code, created date, status
- [ ] "Invite Member" link works
- [ ] "Upgrade to Organization" link works (if standalone team)
- [ ] Upgrade CTA shows for standalone teams
- [ ] Handles "no team" state correctly
- [ ] Query parameter `?teamId=...` works
- [ ] Dark theme styling is consistent

### 3. Team Invite (`/team/:teamId/invite`)

- [ ] Page loads without errors
- [ ] Email input validation works
- [ ] Role dropdown (viewer, contributor, admin) works
- [ ] Role descriptions display correctly
- [ ] Submit sends invitation successfully
- [ ] Success message displays
- [ ] Pending invitations list displays
- [ ] Error messages display correctly
- [ ] Dark theme styling is consistent

### 4. Team Upgrade (`/team/:teamId/upgrade`)

- [ ] Page loads without errors
- [ ] Organization name field validation works
- [ ] Domain field is optional
- [ ] Organization size dropdown works
- [ ] Industry field is optional
- [ ] Benefits list displays correctly
- [ ] Submit upgrades team successfully
- [ ] Redirects after successful upgrade
- [ ] Error messages display correctly
- [ ] Cancel button returns to dashboard
- [ ] Dark theme styling is consistent

---

## Billing Pages

### 5. Team Billing (`/team/billing`)

- [ ] Page loads without errors
- [ ] Current plan card displays correctly
- [ ] Plan features list displays
- [ ] Subscription status badge shows correctly
- [ ] Next billing date displays (if applicable)
- [ ] Payment method card displays (if set)
- [ ] "Add Payment Method" button works (if no payment method)
- [ ] "Update Payment Method" link works (if payment method exists)
- [ ] Change plan section displays available plans
- [ ] Plan upgrade/downgrade buttons work
- [ ] Cancel subscription section works
- [ ] Cancel confirmation dialog works
- [ ] "Cancel at Period End" works
- [ ] "Cancel Immediately" works
- [ ] Quick links (Usage Analytics, Invoices) work
- [ ] Dark theme styling is consistent

### 6. Payment Method (`/team/billing/payment-method`)

- [ ] Page loads without errors
- [ ] Stripe Elements card input displays
- [ ] Shows warning if Stripe key not configured
- [ ] Card input styling matches dark theme
- [ ] Can enter test card: `4242 4242 4242 4242`
- [ ] Form validation works
- [ ] Submit creates payment method successfully
- [ ] Success message displays
- [ ] Redirects to billing page after success
- [ ] Error messages display correctly (invalid card, etc.)
- [ ] Cancel button works
- [ ] Security notice displays
- [ ] Dark theme styling is consistent

### 7. Invoice List (`/team/billing/invoices`)

- [ ] Page loads without errors
- [ ] Invoice table displays correctly
- [ ] Date filter inputs work
- [ ] "Apply Filter" button works
- [ ] Pagination displays correctly
- [ ] Previous/Next buttons work
- [ ] Invoice status badges show correct colors
- [ ] "Download PDF" button works
- [ ] Empty state displays correctly (no invoices)
- [ ] Error state displays correctly
- [ ] Dark theme styling is consistent

### 8. Usage Analytics (`/team/usage`)

- [ ] Page loads without errors
- [ ] Summary cards display: Memories, API Calls, Storage, Contexts
- [ ] Memory usage chart displays (bar chart)
- [ ] API calls chart displays (bar chart)
- [ ] Storage usage visualization displays (pie chart)
- [ ] "Export Data" button works
- [ ] CSV export downloads correctly
- [ ] Date period displays correctly
- [ ] Error state displays correctly
- [ ] Dark theme styling is consistent

---

## Cross-Page Navigation

- [ ] All internal links work correctly
- [ ] Back buttons navigate correctly
- [ ] Breadcrumb navigation (if present) works
- [ ] Navigation bar links work
- [ ] Protected routes require authentication

---

## Error Handling

- [ ] API errors display user-friendly messages
- [ ] Network errors handled gracefully
- [ ] 401 errors redirect to login
- [ ] 404 errors handled (if applicable)
- [ ] Loading states display correctly
- [ ] Toast notifications work correctly

---

## Theme & Styling

- [ ] Dark theme applied consistently across all pages
- [ ] Glass-surface cards display correctly
- [ ] Button hover states work
- [ ] Form inputs match theme
- [ ] Links have correct colors
- [ ] Error/success messages styled correctly
- [ ] Loading spinners display correctly
- [ ] Responsive design works on mobile/tablet

---

## Browser Compatibility

Test in:
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)

---

## Performance

- [ ] Pages load in < 2 seconds
- [ ] No console errors
- [ ] No unnecessary re-renders
- [ ] Images/assets load correctly

---

## Stripe Integration (If Testing Payment Methods)

- [ ] Stripe Elements loads correctly
- [ ] Test card `4242 4242 4242 4242` works
- [ ] Invalid card shows error message
- [ ] Payment method saved to backend
- [ ] Backend receives payment method ID

---

## Notes

- All pages use React Router (not Next.js)
- All API calls use `apiClient` from `lib/apiClient.ts`
- All pages use dark theme with `glass-surface` styling
- Environment variable: `VITE_STRIPE_PUBLISHABLE_KEY` (not `NEXT_PUBLIC_`)

---

## Issues Found

Document any issues here:

1.
2.
3.

---

## Sign-Off

- [ ] All critical paths tested
- [ ] No blocking issues found
- [ ] Ready for production (or staging)

**Tester:** _________________
**Date:** _________________
