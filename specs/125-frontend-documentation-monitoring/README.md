# SPEC-125: Frontend Documentation & Monitoring
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Engineering
**Last Updated:** 2025-10-11
**Phase:** 5 - Frontend Decomposition

---

## 1) Problem

Split frontend architecture needs:
- **Architecture documentation** (diagrams, data flow, state management)
- **Deployment guides** (customer vs admin procedures)
- **Testing guides** (E2E, integration, visual regression)
- **Production monitoring** (performance, errors, analytics)

---

## 2) Solution

Create comprehensive documentation suite:
- Architecture overview with Mermaid diagrams
- Step-by-step deployment guides
- Testing runbooks (Playwright, Jest, Chromatic)
- Monitoring dashboards (Vercel + Grafana)

---

## 3) Documentation Structure

```
docs/frontend/
├── ARCHITECTURE_OVERVIEW.md
│   ├── Shared library design
│   ├── Component architecture (Atomic Design)
│   ├── State management (Zustand)
│   └── Data flow diagrams
│
├── DEPLOYMENT_GUIDE.md
│   ├── Customer app (Vercel)
│   ├── Admin app (internal server)
│   ├── Environment variables
│   └── CI/CD workflows
│
├── TESTING_GUIDE.md
│   ├── Playwright E2E tests
│   ├── Jest unit tests
│   ├── Storybook + Chromatic
│   └── Coverage requirements
│
└── MONITORING_GUIDE.md
    ├── Vercel Analytics
    ├── Grafana dashboards
    ├── Error tracking
    └── Performance budgets
```

---

## 4) Monitoring Setup

### Customer App (Vercel)
- Vercel Analytics (Core Web Vitals)
- Error tracking (Sentry)
- Real User Monitoring

### Admin App (Internal)
- Grafana dashboard (API metrics)
- PM2 monitoring
- Nginx logs

---

## 5) Success Criteria

- [ ] Architecture docs complete with diagrams
- [ ] Deployment guides tested by new developer
- [ ] Testing guide covers all test types
- [ ] Monitoring dashboards operational
- [ ] Runbooks for common issues

---

## 6) Templates

See implementation stubs:
- `ARCHITECTURE_OVERVIEW.md`
- `DEPLOYMENT_GUIDE.md`
- `TESTING_GUIDE.md`
- `monitoring/grafana-dashboard.json`
