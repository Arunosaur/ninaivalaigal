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
- ✅ Memory recording UI
- ✅ Token management
- ✅ MCP configuration
- ✅ Billing pages
- ✅ Public API docs (gated by sign-in)

## Development

```bash
# Install dependencies
npm install

# Start dev server (runs on port 8101)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint
npm run lint
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:13390
VITE_API_VERSION=v1
```

## Project Structure

```
src/
├── pages/           # Page components
│   ├── Signup.tsx
│   ├── Login.tsx
│   └── Dashboard.tsx
├── components/      # Reusable components
├── hooks/           # Custom React hooks
├── lib/             # Utilities and helpers
├── App.tsx          # Main app component
├── main.tsx         # Entry point
└── index.css        # Global styles
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
