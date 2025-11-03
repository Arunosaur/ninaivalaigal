# Ninaivalaigal Customer App

The public-facing customer application for Ninaivalaigal (e^M - Exponential Memory System).

## Overview

This is the **Customer App** - the end-user experience for individuals, teams, and organizations using Ninaivalaigal.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tooling
- **TailwindCSS** - Styling (from `@nina/ui`)
- **React Router** - Client-side routing
- **Axios** - API client

## Features

- ✅ Signup/login flows
- ✅ Token management with axios interceptors
- ✅ Protected routing + landing redirect guards
- ✅ Memory recording UI
- ✅ MCP configuration
- ✅ **Team Management** (create, dashboard, invite, upgrade)
- ✅ **Billing & Subscriptions** (plans, payment methods, invoices)
- ✅ **Usage Analytics** (memory, API calls, storage)
- ✅ Public API docs (gated by sign-in)

## Development

```bash
# Install dependencies
npm install
npm run preview

# Type check
npm run type-check

# Lint
npm run lint
```

## Environment Variables

# Start dev server (runs on port 8101)
npm run dev

# Build for production
npm run build

Create a `.env` file:

```env
VITE_API_URL=http://localhost:13390
VITE_API_VERSION=v1

# Stripe Configuration (optional, for payment method management)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here
```

See `STRIPE_SETUP.md` for Stripe configuration details.

## Project Structure

# Run unit/component tests (Vitest + Testing Library)
npm run test

```
src/
├── __tests__/auth/      # Vitest + Testing Library suites (auth flows)
├── components/          # Reusable UI building blocks
├── lib/                 # API client + auth persistence helpers
├── pages/               # Routed pages
│   ├── Landing.tsx      # Landing page
│   ├── Login.tsx        # Login page
│   ├── Signup.tsx       # Signup page
│   ├── Dashboard.tsx    # User dashboard
│   ├── MemoryBrowser.tsx # Memory browser
│   ├── Teams.tsx        # Teams list
│   ├── Team*.tsx        # Team management pages (create, dashboard, billing, etc.)
│   └── Settings.tsx     # Settings page
├── styles/              # Tailwind overrides
├── types/               # Shared TypeScript contracts
├── utils/               # Cross-cutting utilities
├── App.tsx              # Main app component
├── main.tsx             # Entry point
├── setupTests.ts        # Global test setup (jsdom, matchers)
├── test-utils.tsx       # Custom render helpers (HistoryRouter, AuthProvider)
└── index.css            # Global styles
```

## Shared Packages

This app uses shared packages from the monorepo:

- `@nina/ui` - Design system (tokens, components)
- `@nina/api-client` - Generated API client (public OpenAPI)
- `@nina/auth` - Auth utilities (JWT, scopes)

## Deployment

Built assets are served by nginx on port 8101.

See `Dockerfile.ui` for production build configuration.

## Related

- **Admin Console:** `apps/admin-console/` (internal/operational)
- **Shared UI:** `packages/ui/` (design system)
- **API Client:** `packages/api-client/` (generated SDKs)

## SPEC Reference

- **SPEC-083:** Product Surface Split & Naming
- **SPEC-084:** Agentic UI Testing Framework
- **SPEC-087:** API Surface Contracts
