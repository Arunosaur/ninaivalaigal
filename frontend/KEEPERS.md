# Frontend Keeper Files - Port to Next.js

**Purpose**: Canonical list of files to maintain and migrate to Next.js
**Date**: October 9, 2025

---

## ✅ **KEEP & FIX** (Port to Next.js)

### **Reusable UI Components** (~40 issues)

```
components/Button.tsx
components/Narrative/Stepper.tsx         # Fix 3 a11y issues
components/Narrative/Overlay.tsx         # Fix 2 unused imports
components/Narrative/Callout.tsx         # Fix 1 unused import
components/Narrative/useGraphOpsNarrative.ts
components/Narrative/index.ts
components/index.ts
```

**Migration Target**: `ninaivalaigal-next/src/components/ui/`

### **Dashboard Components** (~25 issues)

```
src/components/dashboard/DashboardContainer.tsx    # Fix 2 console.log
src/components/dashboard/AIInsightPanel.tsx        # Fix 1 unused import
src/components/dashboard/SentimentTrendGraph.tsx   # Fix 1 unused import, 1 entity
src/components/dashboard/SmartNotificationDrawer.tsx # Fix 3 console.log, 1 entity
src/components/dashboard/TopMemoryCard.tsx
```

**Migration Target**: `ninaivalaigal-next/src/components/dashboard/`

### **Gamification Components** (~8 issues)

```
src/components/gamification/BadgeDisplay.tsx
```

**Migration Target**: `ninaivalaigal-next/src/components/gamification/`

### **Utilities** (~8 issues)

```
utils/cn.ts                             # Class name utility
```

**Migration Target**: `ninaivalaigal-next/src/utils/`

### **Configuration** (~5 issues)

```
tailwind.config.js                      # Works with Next.js
jest.config.js                          # Testing stays
.eslintrc.json                          # Quality enforcement
.husky/                                 # Pre-commit hooks
package.json                            # Update dependencies
```

**Migration Target**: `ninaivalaigal-next/` (root)

### **Storybook** (0 issues - already excluded)

```
*.stories.tsx                           # Keep for UI development
.storybook/                             # Works with Next.js
```

**Migration Target**: `ninaivalaigal-next/.storybook/`

---

## ❌ **DELETE** (Do NOT fix lint issues)

### **Legacy HTML Pages** (~60 issues)

```
index.html
enhanced-signup.html
team-dashboard.html
partner-dashboard.html
organization-management.html
team-api-keys.html
invoice-management.html
admin/*.html (20+ files)
```

**Reason**: Replaced by Next.js App Router pages

### **Vanilla JavaScript** (~25 issues)

```
js/token-management.js
js/memory-browser.js
js/graphops-narrative.js
js/team-invitations.js
admin/*.js (legacy)
```

**Reason**: Replaced by Next.js Server Actions

### **Duplicate Components** (~60 issues)

```
admin/Narrative/Stepper.tsx             # Delete (keep components/Narrative/)
admin/Narrative/Overlay.tsx
admin/Narrative/Callout.tsx
admin/Narrative/Button.tsx
admin/Narrative/useGraphOpsNarrative.ts
admin/Narrative/index.ts

customer/Narrative/Stepper.tsx          # Delete (keep components/Narrative/)
customer/Narrative/Overlay.tsx
customer/Narrative/Callout.tsx
customer/Narrative/Button.tsx
customer/Narrative/useGraphOpsNarrative.ts
customer/Narrative/index.ts
```

**Reason**: Consolidate to single `components/Narrative/` folder

---

## 📊 **Summary**

| Category | Files | Lint Issues | Action |
|----------|-------|-------------|--------|
| **Keep & Fix** | 17 files | ~81 issues | Fix before migration |
| **Delete** | 40+ files | ~120 issues | Ignore - will be deleted |
| **Total** | 57+ files | 201 issues | Focus on 81 keeper issues |

---

## 🎯 **Priority Fixes (Before Migration)**

### **P1: Accessibility** (6 issues) - Critical

```typescript
// components/Narrative/Stepper.tsx - Line 142
// Add role="button", tabIndex, onKeyDown
```

### **P2: Console Statements** (5 issues) - Easy

```typescript
// src/components/dashboard/DashboardContainer.tsx
// Comment with TODO markers
```

### **P3: Unused Imports** (15 issues) - Easy

```typescript
// Multiple dashboard components
// Remove dead imports
```

### **P4: Unescaped Entities** (2 issues) - Easy

```typescript
// "Tomorrow's" → "Tomorrow&apos;s"
// "You're" → "You&apos;re"
```

### **P5: TypeScript any** (45 issues) - Defer

```typescript
// Fix after Next.js migration
// Many will resolve automatically
```

**Expected Result After Fixing**: **81 → ~35 issues**

---

## 🚀 **Migration Checklist**

- [ ] Update ESLint to ignore legacy files
- [ ] Tag legacy files with migration comments
- [ ] Fix P1-P4 issues in keeper files (10 hours)
- [ ] Run `npm run lint` → confirm ~35 issues
- [ ] Bootstrap Next.js 15 project
- [ ] Copy keepers to new project
- [ ] Port ESLint + Husky configuration
- [ ] Delete legacy frontend/ folder
- [ ] Final lint check → <20 issues

---

*See: NEXTJS_MIGRATION_IMPACT_REPORT.md for full strategy*
