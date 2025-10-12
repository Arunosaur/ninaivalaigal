# Ninaivalaigal Customer Frontend

**Status:** 🚧 Phase-5 Active Development
**SPEC:** [SPEC-122 Customer Frontend Rollout](../specs/122-customer-frontend-rollout/)
**Branch:** `feature/122-customer-app-baseline`

## Overview

Customer-facing Next.js 15 application for Ninaivalaigal memory management platform. Built with React 19, TypeScript, and TailwindCSS.

## Tech Stack

- **Framework:** Next.js 15.5.4 (App Router + Turbopack)
- **React:** 19.1.0
- **TypeScript:** 5.x (strict mode)
- **Styling:** TailwindCSS v4
- **Shared Library:** `@ninaivalaigal/ui-components`
- **Build Time:** ~2s
- **Bundle Size:** 115-145 KB First Load JS

## Getting Started

### Prerequisites
```bash
# Ensure shared library is built first
cd ../frontend-shared
npm install
npm run build
```

### Development
```bash
# Install dependencies
npm install

# Start dev server (port 3000)
npm run dev

# Open browser
open http://localhost:3000
```

### Build & Test
```bash
# Type check
npm run type-check

# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend-nextjs-customer/
├── app/                      # Next.js App Router pages
│   ├── page.tsx             # Landing page (/)
│   ├── login/page.tsx       # Authentication (/login)
│   ├── dashboard/page.tsx   # User dashboard (/dashboard)
│   ├── memories/page.tsx    # Memory list (/memories)
│   ├── layout.tsx           # Root layout
│   └── globals.css          # Global styles
├── components/              # Customer-specific components
│   └── MemoryCard.tsx       # Memory display card
├── public/                  # Static assets
├── package.json             # Dependencies
└── tsconfig.json            # TypeScript config
```

## Routes

| Route | Component | Status | Description |
|-------|-----------|--------|-------------|
| `/` | `page.tsx` | ✅ | Landing page with hero + features |
| `/login` | `login/page.tsx` | ✅ | Authentication (uses shared LoginForm) |
| `/dashboard` | `dashboard/page.tsx` | ✅ | User dashboard with stats cards |
| `/memories` | `memories/page.tsx` | ✅ | Memory list with search + filters |

## Shared Components Used

From `@ninaivalaigal/ui-components`:
- **Button:** Primary/secondary/ghost variants with loading states
- **Input:** Text/search inputs with proper types
- **Card:** Container component for content blocks
- **LoginForm:** Complete authentication form
- **useDebounce:** Hook for debounced search

## Customer-Specific Components

### MemoryCard
Memory display card with:
- Category badges (personal/work/shared)
- Content preview (3-line clamp)
- Tags display
- Share/edit actions
- Responsive design

## Development Notes

### Phase-5 Integration
- **Day 1:** ✅ Baseline scaffolding + shared library integration
- **Day 2:** 🚧 Active - Enhanced dashboard, memories page, MemoryCard component
- **Day 3-4:** Customer-specific features (search, filtering, memory CRUD)
- **Week 2:** API integration, authentication flow, state management

### Shared Library Updates
When `frontend-shared` is updated:
```bash
cd ../frontend-shared
npm run build

cd ../frontend-nextjs-customer
npm install  # Refresh link
npm run build  # Verify
```

### TypeScript Configuration
- Strict mode enabled
- Path aliases: `@/*` maps to root
- React 19 types configured
- Next.js App Router types

### Styling Approach
- TailwindCSS v4 utility-first
- Shared design tokens from `ui-components`
- Custom components in `components/`
- Responsive mobile-first design

## Next Steps

- [ ] Implement memory creation flow
- [ ] Add memory detail view
- [ ] Integrate with backend API
- [ ] Add authentication state management
- [ ] Implement real-time search
- [ ] Add loading states
- [ ] Expand test coverage
- [ ] Add error boundaries
- [ ] Implement optimistic UI updates

## Related Documentation

- **Shared Library:** `../frontend-shared/README.md`
- **SPEC-122:** `../specs/122-customer-frontend-rollout/`
- **Phase-5 Plan:** `../specs/PHASE_SUMMARIES/PHASE_5_KICKOFF.md`
- **Onboarding:** `../docs/DEVELOPER_ONBOARDING.md`

## Build Metrics

Current production build:
```
Route (app)                    Size  First Load JS
┌ ○ /                         4.65 kB      145 kB
├ ○ /dashboard                 706 B       141 kB
├ ○ /login                     598 B       141 kB
└ ○ /memories                1.09 kB      142 kB
```

Target: Keep First Load JS under 150 KB for optimal performance.
