# Phase-5 Project Board Setup

**Last Updated:** 2025-10-11
**Duration:** 9 weeks (Oct 13 - Dec 13, 2025)
**Team:** 2 developers (same computer)

---

## 🎯 Overview

This document provides the task breakdown for GitHub Projects to track Phase-5 Frontend Split execution. Import these tasks into a GitHub Project board for visual sprint management.

---

## 📊 Board Structure

### **Columns (Kanban)**
1. **Backlog** - Not started
2. **In Progress** - Active work
3. **Review** - PR open, awaiting review
4. **Testing** - Merged to main, testing in staging
5. **Done** - Deployed and verified

### **Labels**
- `SPEC-121` - Frontend shared library
- `SPEC-122` - Customer app
- `SPEC-123` - Admin app
- `SPEC-124` - CI/CD
- `SPEC-105` - Backend integration
- `SPEC-106` - E2E tests
- `SPEC-107` - Profile/Settings
- `SPEC-108` - Auth & Security
- `SPEC-109` - Real-time features
- `priority-high` - Blocking work
- `priority-medium` - Standard work
- `priority-low` - Nice to have
- `blocked` - Waiting on dependency

---

## 📋 Week 1-2: Foundation (Oct 13-24)

### **SPEC-121: Frontend Shared Library** (Developer A)

#### Task: Initialize Shared Workspace
- **Assignee:** Developer A
- **Priority:** High
- **SPEC:** SPEC-121
- **Description:**
  ```
  Bootstrap frontend-shared/ workspace
  - Create package.json with TypeScript
  - Configure tsconfig.json (strict mode)
  - Set up build tooling (tsup/rollup)
  - Add to Turborepo workspaces
  ```
- **Acceptance Criteria:**
  - [ ] `npm run build` succeeds
  - [ ] TypeScript types exported
  - [ ] Other workspaces can import via `@ninaivalaigal/shared`
- **Estimate:** 1 day

#### Task: Design System Tokens
- **Assignee:** Developer A
- **Priority:** High
- **SPEC:** SPEC-121
- **Description:**
  ```
  Create design system foundation
  - Color palette (primary, secondary, neutral)
  - Typography scale
  - Spacing system
  - Border radius, shadows
  ```
- **Acceptance Criteria:**
  - [ ] `src/styles/tokens.ts` created
  - [ ] CSS variables exported
  - [ ] Documentation in Storybook
- **Estimate:** 1 day

#### Task: Base UI Components
- **Assignee:** Developer A
- **Priority:** High
- **SPEC:** SPEC-121
- **Description:**
  ```
  Implement foundational components
  - Button (variants: primary, secondary, ghost)
  - Input (text, password, email)
  - Card (container component)
  - Layout (Container, Stack, Grid)
  ```
- **Acceptance Criteria:**
  - [ ] Components fully typed
  - [ ] Unit tests for each component
  - [ ] Storybook stories
  - [ ] Accessible (ARIA labels)
- **Estimate:** 3 days

#### Task: Shared Hooks
- **Assignee:** Developer A
- **Priority:** Medium
- **SPEC:** SPEC-121
- **Description:**
  ```
  Create reusable React hooks
  - useAuth() - Authentication state
  - useMemory() - Memory operations
  - useDebounce() - Input debouncing
  - useLocalStorage() - Persistent state
  ```
- **Acceptance Criteria:**
  - [ ] Hooks fully typed
  - [ ] Unit tests with @testing-library/react-hooks
  - [ ] Documentation with examples
- **Estimate:** 2 days

---

### **SPEC-122: Customer Frontend Baseline** (Developer B)

#### Task: Initialize Next.js Customer App
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-122
- **Dependencies:** Waits for SPEC-121 task "Initialize Shared Workspace"
- **Description:**
  ```
  Bootstrap customer Next.js application
  - npx create-next-app@latest frontend-nextjs-customer
  - Configure App Router (Next.js 15)
  - Set up TypeScript strict mode
  - Add to Turborepo workspaces
  ```
- **Acceptance Criteria:**
  - [ ] `npm run dev` starts on localhost:3000
  - [ ] TypeScript builds without errors
  - [ ] Can import from `@ninaivalaigal/shared`
- **Estimate:** 1 day

#### Task: Routing Structure
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-122
- **Description:**
  ```
  Set up customer app routes
  - app/page.tsx (homepage)
  - app/login/page.tsx (authentication)
  - app/dashboard/page.tsx (main dashboard)
  - app/memories/page.tsx (memory list)
  - app/memories/[id]/page.tsx (memory detail)
  ```
- **Acceptance Criteria:**
  - [ ] All routes accessible
  - [ ] Layouts configured
  - [ ] Navigation working
  - [ ] Loading states implemented
- **Estimate:** 2 days

#### Task: Customer-Specific Components
- **Assignee:** Developer B
- **Priority:** Medium
- **SPEC:** SPEC-122
- **Description:**
  ```
  Build customer-facing components
  - MemoryCard (displays memory preview)
  - SearchBar (memory search)
  - MemoryTimeline (chronological view)
  - UserAvatar (profile picture)
  ```
- **Acceptance Criteria:**
  - [ ] Components use shared library base
  - [ ] Unit tests for each
  - [ ] Responsive design (mobile-first)
- **Estimate:** 3 days

#### Task: Mock Data Integration
- **Assignee:** Developer B
- **Priority:** Medium
- **SPEC:** SPEC-122
- **Description:**
  ```
  Create mock data for development
  - Mock memory data (fixtures)
  - Mock user authentication
  - Local storage persistence
  - API route mocks (Next.js API routes)
  ```
- **Acceptance Criteria:**
  - [ ] Dashboard shows mock memories
  - [ ] Search functionality works
  - [ ] CRUD operations simulated
- **Estimate:** 2 days

---

### **SPEC-124: Turborepo CI/CD** (Lead/You)

#### Task: Root Turborepo Configuration
- **Assignee:** Lead
- **Priority:** High
- **SPEC:** SPEC-124
- **Description:**
  ```
  Configure Turborepo monorepo
  - Root package.json with workspaces
  - turbo.json with pipeline definitions
  - Shared dependencies (React, TypeScript)
  - Build caching configuration
  ```
- **Acceptance Criteria:**
  - [ ] `turbo build` builds all workspaces
  - [ ] `turbo lint` lints all workspaces
  - [ ] Caching working (local and remote)
- **Estimate:** 1 day

#### Task: GitHub Actions Workflow
- **Assignee:** Lead
- **Priority:** High
- **SPEC:** SPEC-124
- **Description:**
  ```
  Set up CI/CD pipelines
  - .github/workflows/frontend-ci.yml
  - Run lint, type-check, test on PR
  - Build all workspaces
  - Upload build artifacts
  ```
- **Acceptance Criteria:**
  - [ ] PR checks run automatically
  - [ ] Failing checks block merge
  - [ ] Build time < 5 minutes
- **Estimate:** 2 days

#### Task: Integration Smoke Tests
- **Assignee:** Lead
- **Priority:** Medium
- **SPEC:** SPEC-124
- **Description:**
  ```
  Add frontend smoke tests
  - Can import from shared library
  - Customer app builds successfully
  - Admin app builds successfully
  - No circular dependencies
  ```
- **Acceptance Criteria:**
  - [ ] Tests run in CI
  - [ ] Tests pass consistently
  - [ ] < 30 second execution time
- **Estimate:** 1 day

---

## 📋 Week 3-4: Integration (Oct 27 - Nov 7)

### **SPEC-123: Admin Frontend Baseline** (Developer A)

#### Task: Initialize Next.js Admin App
- **Assignee:** Developer A
- **Priority:** High
- **SPEC:** SPEC-123
- **Description:**
  ```
  Bootstrap admin Next.js application
  - Similar structure to customer app
  - Internal-only authentication
  - Admin-specific routing
  - Uses shared components
  ```
- **Acceptance Criteria:**
  - [ ] Runs on localhost:3001
  - [ ] Separate from customer app
  - [ ] Can import shared library
- **Estimate:** 1 day

#### Task: Admin-Specific Components
- **Assignee:** Developer A
- **Priority:** Medium
- **SPEC:** SPEC-123
- **Description:**
  ```
  Build admin tools
  - UserManagementTable
  - SystemMetricsDashboard
  - AuditLogViewer
  - FeatureFlagPanel
  ```
- **Acceptance Criteria:**
  - [ ] Components use shared base
  - [ ] Admin-only styling
  - [ ] RBAC checks integrated
- **Estimate:** 3 days

---

### **SPEC-105: Backend Integration** (Developer B)

#### Task: Next.js API Routes
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-105
- **Description:**
  ```
  Create API route proxies
  - app/api/memories/route.ts
  - app/api/auth/route.ts
  - app/api/users/route.ts
  - Proxy to FastAPI backend
  ```
- **Acceptance Criteria:**
  - [ ] API routes working
  - [ ] Environment variables configured
  - [ ] Error handling
  - [ ] CORS configured
- **Estimate:** 2 days

#### Task: Database Integration
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-105
- **Dependencies:** Requires PgBouncer running
- **Description:**
  ```
  Connect to PostgreSQL via PgBouncer
  - Environment variables for DB connection
  - Connection pooling
  - Error handling
  - Migration verification
  ```
- **Acceptance Criteria:**
  - [ ] Can read from database
  - [ ] Can write to database
  - [ ] Transactions working
  - [ ] Connection pool stable
- **Estimate:** 2 days

#### Task: Replace Mock Data
- **Assignee:** Developer B
- **Priority:** Medium
- **SPEC:** SPEC-105
- **Description:**
  ```
  Replace mock data with real API calls
  - Dashboard fetches real memories
  - Search queries real database
  - CRUD operations persist
  - Loading states handled
  ```
- **Acceptance Criteria:**
  - [ ] No more mock data in components
  - [ ] Real-time data displayed
  - [ ] Error states handled
  - [ ] Loading spinners working
- **Estimate:** 3 days

---

## 📋 Week 5-6: Enhancement (Nov 10-21)

### **SPEC-106: E2E Tests** (Developer B)

#### Task: Playwright Setup
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-106
- **Description:**
  ```
  Configure Playwright for E2E testing
  - Install @playwright/test
  - Configure playwright.config.ts
  - Set up test fixtures
  - Add to CI pipeline
  ```
- **Acceptance Criteria:**
  - [ ] `npm run test:e2e` runs tests
  - [ ] Tests run in CI
  - [ ] Parallel execution working
- **Estimate:** 1 day

#### Task: Critical User Flows
- **Assignee:** Developer B
- **Priority:** High
- **SPEC:** SPEC-106
- **Description:**
  ```
  Test critical paths
  - User login flow
  - Memory creation flow
  - Memory search flow
  - Logout flow
  ```
- **Acceptance Criteria:**
  - [ ] All flows passing
  - [ ] Screenshots on failure
  - [ ] Video recording enabled
- **Estimate:** 3 days

---

### **SPEC-107: Profile & Settings** (Developer A)

#### Task: User Profile Page
- **Assignee:** Developer A
- **Priority:** Medium
- **SPEC:** SPEC-107
- **Description:**
  ```
  Build user profile functionality
  - Profile page UI
  - Edit profile form
  - Avatar upload
  - Password change
  ```
- **Acceptance Criteria:**
  - [ ] Profile editable
  - [ ] Changes persist to DB
  - [ ] Validation working
  - [ ] Success/error messages
- **Estimate:** 3 days

#### Task: Settings Dashboard
- **Assignee:** Developer A
- **Priority:** Medium
- **SPEC:** SPEC-107
- **Description:**
  ```
  Create settings UI
  - Account settings
  - Privacy settings
  - Notification preferences
  - Theme toggle (light/dark)
  ```
- **Acceptance Criteria:**
  - [ ] Settings persist
  - [ ] UI responsive
  - [ ] Accessibility compliant
- **Estimate:** 2 days

---

### **SPEC-108: Auth & Security** (Lead/You)

#### Task: NextAuth.js Integration
- **Assignee:** Lead
- **Priority:** High
- **SPEC:** SPEC-108
- **Description:**
  ```
  Implement secure authentication
  - Configure NextAuth.js
  - JWT session management
  - Secure cookie handling
  - CSRF protection
  ```
- **Acceptance Criteria:**
  - [ ] Login/logout working
  - [ ] Sessions persist
  - [ ] Secure headers configured
  - [ ] CSRF tokens validated
- **Estimate:** 3 days

#### Task: RBAC Middleware
- **Assignee:** Lead
- **Priority:** High
- **SPEC:** SPEC-108
- **Description:**
  ```
  Implement role-based access control
  - Middleware for route protection
  - Role checking utilities
  - Customer vs Admin separation
  - Permission denied pages
  ```
- **Acceptance Criteria:**
  - [ ] Customers can't access admin routes
  - [ ] Admins can access all routes
  - [ ] Proper error pages (401, 403)
- **Estimate:** 2 days

---

## 📋 Week 7-8: Polish (Nov 24 - Dec 5)

### **SPEC-109: Real-Time Features** (Developer B)

#### Task: WebSocket Integration
- **Assignee:** Developer B
- **Priority:** Medium
- **SPEC:** SPEC-109
- **Description:**
  ```
  Add real-time updates
  - WebSocket connection management
  - Live memory updates
  - Collaborative editing notifications
  - Connection status indicators
  ```
- **Acceptance Criteria:**
  - [ ] Real-time updates working
  - [ ] Reconnection logic
  - [ ] Graceful degradation
- **Estimate:** 4 days

---

### **Component Library V2** (Developer A)

#### Task: Advanced Components
- **Assignee:** Developer A
- **Priority:** Low
- **SPEC:** SPEC-121
- **Description:**
  ```
  Expand shared component library
  - Modal/Dialog
  - Dropdown menu
  - Tabs
  - Toast notifications
  - Skeleton loaders
  ```
- **Acceptance Criteria:**
  - [ ] Components accessible
  - [ ] Unit tests
  - [ ] Storybook stories
- **Estimate:** 5 days

---

### **Performance Optimization** (Lead/You)

#### Task: Bundle Size Optimization
- **Assignee:** Lead
- **Priority:** Medium
- **SPEC:** SPEC-124
- **Description:**
  ```
  Optimize frontend bundles
  - Code splitting
  - Dynamic imports
  - Tree shaking verification
  - Image optimization
  ```
- **Acceptance Criteria:**
  - [ ] Bundle size < 200KB (gzipped)
  - [ ] Lighthouse score 90+
  - [ ] LCP < 2.5s
- **Estimate:** 3 days

---

## 📋 Week 9: Launch Prep (Dec 8-13)

### **Final Testing & Documentation**

#### Task: Production Deployment Dry Run
- **Assignee:** Lead
- **Priority:** High
- **Description:**
  ```
  Verify deployment readiness
  - Build production bundles
  - Deploy to staging
  - Run full E2E suite
  - Load testing
  ```
- **Acceptance Criteria:**
  - [ ] Staging deployment successful
  - [ ] All tests passing
  - [ ] Performance benchmarks met
- **Estimate:** 2 days

#### Task: Documentation Finalization
- **Assignee:** Both
- **Priority:** Medium
- **Description:**
  ```
  Complete documentation
  - Update all SPEC READMEs
  - API documentation
  - Deployment runbook
  - Troubleshooting guide
  ```
- **Acceptance Criteria:**
  - [ ] All SPECs marked "COMPLETE"
  - [ ] Runbooks tested
  - [ ] Links verified
- **Estimate:** 2 days

---

## 📊 GitHub Projects CSV Import

Copy this CSV to import into GitHub Projects:

```csv
Title,Status,Assignee,Priority,SPEC,Estimate
"Initialize Shared Workspace",Backlog,Developer A,High,SPEC-121,1 day
"Design System Tokens",Backlog,Developer A,High,SPEC-121,1 day
"Base UI Components",Backlog,Developer A,High,SPEC-121,3 days
"Shared Hooks",Backlog,Developer A,Medium,SPEC-121,2 days
"Initialize Next.js Customer App",Backlog,Developer B,High,SPEC-122,1 day
"Routing Structure",Backlog,Developer B,High,SPEC-122,2 days
"Customer-Specific Components",Backlog,Developer B,Medium,SPEC-122,3 days
"Mock Data Integration",Backlog,Developer B,Medium,SPEC-122,2 days
"Root Turborepo Configuration",Backlog,Lead,High,SPEC-124,1 day
"GitHub Actions Workflow",Backlog,Lead,High,SPEC-124,2 days
"Integration Smoke Tests",Backlog,Lead,Medium,SPEC-124,1 day
"Initialize Next.js Admin App",Backlog,Developer A,High,SPEC-123,1 day
"Admin-Specific Components",Backlog,Developer A,Medium,SPEC-123,3 days
"Next.js API Routes",Backlog,Developer B,High,SPEC-105,2 days
"Database Integration",Backlog,Developer B,High,SPEC-105,2 days
"Replace Mock Data",Backlog,Developer B,Medium,SPEC-105,3 days
"Playwright Setup",Backlog,Developer B,High,SPEC-106,1 day
"Critical User Flows",Backlog,Developer B,High,SPEC-106,3 days
"User Profile Page",Backlog,Developer A,Medium,SPEC-107,3 days
"Settings Dashboard",Backlog,Developer A,Medium,SPEC-107,2 days
"NextAuth.js Integration",Backlog,Lead,High,SPEC-108,3 days
"RBAC Middleware",Backlog,Lead,High,SPEC-108,2 days
"WebSocket Integration",Backlog,Developer B,Medium,SPEC-109,4 days
"Advanced Components",Backlog,Developer A,Low,SPEC-121,5 days
"Bundle Size Optimization",Backlog,Lead,Medium,SPEC-124,3 days
"Production Deployment Dry Run",Backlog,Lead,High,Launch,2 days
"Documentation Finalization",Backlog,Both,Medium,Launch,2 days
```

---

## 🎯 Sprint Planning Recommendations

### **Sprint 1 (Week 1-2): Foundation**
- **Goal:** All three workspaces scaffolded
- **Demo:** Show working customer app with mock data

### **Sprint 2 (Week 3-4): Integration**
- **Goal:** Backend integration complete
- **Demo:** Real data flowing through customer app

### **Sprint 3 (Week 5-6): Enhancement**
- **Goal:** E2E tests + profile features
- **Demo:** Complete user flows working

### **Sprint 4 (Week 7-8): Polish**
- **Goal:** Real-time features + performance
- **Demo:** Production-ready experience

### **Sprint 5 (Week 9): Launch**
- **Goal:** Documentation + deployment
- **Demo:** Staging deployment walkthrough

---

## 📈 Success Metrics

Track these metrics throughout Phase-5:

- **Velocity:** Story points completed per week
- **Quality:** Test coverage % (target: 80%)
- **Performance:** Lighthouse score (target: 90+)
- **Deployment:** Time from merge to staging (target: < 10 mins)
- **Bugs:** Critical bugs found in production (target: 0)

---

**Ready to import?** Create a new GitHub Project and import the CSV above!
