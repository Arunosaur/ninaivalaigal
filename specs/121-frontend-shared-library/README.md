# SPEC-121: Frontend Shared Library Implementation
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Frontend Engineering
**Last Updated:** 2025-10-11
**Phase:** 5 - Frontend Decomposition

---

## 1) Problem

We need a production-grade shared component library that both `customer` and `admin` apps can import without code duplication. Current monolith has no formalized component sharing strategy.

**Key Issues:**
- No reusable state management (auth, cache, session)
- Duplicate UI components across potential splits
- No visual regression testing (Storybook/Chromatic)
- No versioned component library

---

## 2) Solution

Create `@ninaivalaigal/ui-components` as an npm workspace package with:
- **Atomic Design** component architecture (atoms → molecules → organisms)
- **Zustand** for lightweight global state (auth, theme, notifications)
- **Storybook + Chromatic** for component development + visual regression
- **TypeScript + Tailwind** with strict typing and theme tokens

---

## 3) Architecture

```mermaid
graph TB
    subgraph "Frontend Shared Library"
        UI[components/ui/]
        Dashboard[components/dashboard/]
        Forms[components/forms/]
        State[state/]
        Hooks[hooks/]
        Lib[lib/]
    end

    subgraph "Consumer Apps"
        Customer[frontend-nextjs-customer]
        Admin[frontend-nextjs-admin]
    end

    UI --> Customer
    UI --> Admin
    Dashboard --> Customer
    Dashboard --> Admin
    Forms --> Customer
    Forms --> Admin
    State --> Customer
    State --> Admin
    Hooks --> Customer
    Hooks --> Admin
    Lib --> Customer
    Lib --> Admin

    Storybook[Storybook + Chromatic] --> UI
    Storybook --> Dashboard
    Storybook --> Forms
```

---

## 4) Implementation

### Directory Structure
```
frontend-shared/
├── components/
│   ├── ui/              # Atoms (Button, Input, Card)
│   ├── dashboard/       # Organisms (DashboardContainer, AIInsightPanel)
│   └── forms/           # Molecules (LoginForm, MemoryForm)
├── state/
│   ├── authStore.ts     # Zustand auth state
│   ├── themeStore.ts    # Dark/light theme
│   └── notificationStore.ts
├── hooks/
│   ├── useAuth.ts       # Auth hooks
│   ├── useApi.ts        # API call hooks
│   └── useDebounce.ts   # Utility hooks
├── lib/
│   ├── utils.ts         # cn(), formatters
│   ├── api.ts           # fetchApi client
│   └── schemas.ts       # Zod schemas
├── styles/
│   └── globals.css      # Tailwind base + theme tokens
├── .storybook/
│   ├── main.ts
│   └── preview.ts
├── package.json
└── tsconfig.json
```

### Key Files

See implementation stubs:
- `package.json` - npm workspace config
- `state/authStore.ts` - Zustand auth store
- `.storybook/main.ts` - Storybook config
- `components/ui/Button.tsx` - Example component

---

## 5) Success Criteria

- [ ] `@ninaivalaigal/ui-components` package created
- [ ] 15+ UI components extracted (Button, Card, Input, etc.)
- [ ] Zustand stores for auth, theme, notifications
- [ ] 5+ custom hooks (useAuth, useApi, useDebounce)
- [ ] Storybook running on `localhost:6006`
- [ ] Chromatic visual regression tests configured
- [ ] TypeScript compilation successful
- [ ] Both customer + admin apps import successfully
- [ ] Build time < 10s (Turbo cache enabled)

---

## 6) Dependencies

- **SPEC-103**: Next.js 15 baseline (source for component extraction)
- **SPEC-114**: Auth & Security (JWT, session management)
- **SPEC-124**: Turborepo (monorepo build orchestration)

---

## 7) Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Version drift between apps | High | Strict semver, automated dependency updates |
| Breaking changes in shared lib | High | Comprehensive tests, canary deployments |
| Storybook build time | Medium | Turbo cache, incremental builds |

---

## 8) Testing Strategy

1. **Unit Tests**: Jest for hooks and utilities (80%+ coverage)
2. **Component Tests**: Storybook stories for all components
3. **Visual Regression**: Chromatic on every PR
4. **Integration**: Test imports in both customer + admin apps

---

## 9) Rollout Plan

**Week 1:**
- Create package structure
- Extract 15+ UI components
- Configure Storybook

**Week 2:**
- Add Zustand state stores
- Create custom hooks
- Configure Chromatic

**Week 3:**
- Integration testing with customer app
- Integration testing with admin app
- Documentation + examples

---

## 10) Monitoring

- **Build time**: Track via Turbo cache analytics
- **Bundle size**: Monitor with `@next/bundle-analyzer`
- **Component usage**: Track imports via dependency graph
- **Visual regressions**: Chromatic dashboard

---

**Status**: Ready for implementation
**Next Steps**: Begin extraction of UI components from `/frontend-nextjs/`
