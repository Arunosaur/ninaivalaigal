# SPEC-124: Unified Workspace & CI/CD Pipelines (Turbo + Tests)
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** DevOps
**Last Updated:** 2025-10-11
**Phase:** 5 - Frontend Decomposition

---

## 1) Problem

Three separate frontend packages need:
- **Monorepo orchestration** (shared dependencies, coordinated builds)
- **Fast builds** (incremental, cached)
- **Automated testing** (E2E, integration, unit)
- **Separate deployments** (customer to Vercel, admin to internal)

---

## 2) Solution

Use **Turborepo** for monorepo with:
- Shared dependency management (npm workspaces)
- Remote caching (Turbo cache)
- Parallel builds and tests
- Separate GitHub Actions workflows per app

---

## 3) Architecture

```mermaid
graph TB
    subgraph "Monorepo Root"
        Turbo[turbo.json]
        Package[package.json workspaces]
    end

    subgraph "Workspaces"
        Shared[frontend-shared]
        Customer[frontend-nextjs-customer]
        Admin[frontend-nextjs-admin]
    end

    subgraph "CI/CD"
        GHA[GitHub Actions]
        CustomerDeploy[Deploy Customer to Vercel]
        AdminDeploy[Deploy Admin to Internal]
        SharedBuild[Validate Shared Library]
    end

    Turbo --> Shared
    Turbo --> Customer
    Turbo --> Admin

    Shared --> Customer
    Shared --> Admin

    GHA --> SharedBuild
    GHA --> CustomerDeploy
    GHA --> AdminDeploy
```

---

## 4) Implementation

**Root `package.json`:**
```json
{
  "name": "ninaivalaigal-monorepo",
  "private": true,
  "workspaces": [
    "frontend-shared",
    "frontend-nextjs-customer",
    "frontend-nextjs-admin"
  ],
  "scripts": {
    "build": "turbo run build",
    "dev": "turbo run dev --parallel",
    "test": "turbo run test",
    "lint": "turbo run lint"
  },
  "devDependencies": {
    "turbo": "^1.11.0"
  }
}
```

**`turbo.json`:**
See implementation stub with pipeline definitions

---

## 5) Success Criteria

- [ ] Turborepo configured with remote caching
- [ ] Build time < 2 minutes (with cache)
- [ ] Tests run in parallel
- [ ] GitHub Actions deploy customer app on push
- [ ] GitHub Actions deploy admin app on push
- [ ] Shared library changes trigger dependent builds

---

## 6) CI/CD Workflows

1. `shared-build-validate.yml` - Test shared library
2. `frontend-customer-deploy.yml` - Deploy to Vercel
3. `frontend-admin-deploy.yml` - Deploy to internal server

---

## 7) Monitoring

- Turbo cache hit rate (target > 80%)
- Build duration (track via GitHub Actions)
- Test execution time
