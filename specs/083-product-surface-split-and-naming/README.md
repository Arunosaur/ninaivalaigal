---
status: Partial Implementation
last_updated: 2025-01-11
---

# SPEC-083: Product Surface Split & Naming (Customer App + Admin Console)

**Status:** 🔄 **PARTIAL IMPLEMENTATION**
**Last Updated:** January 2025

## Current Implementation Status

### ✅ Completed
- Customer app exists (`apps/customer/`)
- Admin console exists (`apps/admin-console/`)
- Shared UI package exists (`packages/ui/`)
- OpenAPI filtering implemented (SPEC-087)
- CI policy test structure created

### ⚠️ In Progress
- API client SDKs generation
- Full CI guardrails implementation
- Deployment/routing configuration

### 📋 Documentation
- Implementation status: `docs/spec-083-implementation-status.md`
- Validation script: `taiga/scripts/validate_us565.py`

---




## 2) Canonical Names

### Customer App
The end-user experience for individuals, teams, and orgs.
*Formerly referred to as: "UI," "public app."*

### Admin Console
Internal/operational surface for staff/ops/analysts.
*Replaces "Vendor Console."*

(If/when we expose a partner-facing surface, that will be the **Partner Portal** as a third app—not part of this SPEC.)

> **Optional alternates** you may use in docs/UI copy, but **not** in code or URLs: "Ops Console," "Management Portal."

---

## 3) Scope & Responsibilities

### Customer App
- Signup/login (individual/team/org), billing, profile
- Memory UI: record, tokenize, recall, scoped views
- MCP configuration & "Record" (CCTV-style capture) UX
- Public API docs (gated by sign-in; filtered by role/scopes)

### Admin Console
- Org & tenant administration (RBAC, policy)
- Observability/metrics, audit trails, support tooling
- Data lifecycle & compliance workflows
- Internal analytics & operational dashboards

### Non-goals (for both):
- No mixed pages across apps
- No internal routes mounted on the Customer host
- No public exposure of Admin Console docs or OpenAPI

---

## 4) URLs / Routing

### Customer App
- **Host:** `https://app.<domain>` (or `/app` during transition)
- **Examples:** `/signup`, `/login`, `/dashboard`, `/memory`, `/billing`

### Admin Console
- **Host:** `https://admin.<domain>` (or `/admin` during transition; Tailnet/SSO only)
- **Examples:** `/analytics`, `/audit`, `/support`, `/lifecycle`

### API
- **Public API:** `https://api.<domain>/v1/...` (exposed via Funnel/ingress)
- **Internal API:** `https://internal-api.<domain>` (Tailnet/SSO only)
  - If single-process split is used, admin routes mount under `/_internal` but are **not** exposed publicly.

---

## 5) Repository & Packages

### Monorepo layout
```
apps/
  customer/           # Next.js/Vite React app
  admin-console/      # Next.js/Vite React app
packages/
  ui/                 # shared design system (tokens, components)
  charts/             # shared charts (D3/Recharts viz primitives)
  auth/               # shared auth client utils (JWT, scopes)
  api-client/         # generated SDKs:
    #   - @nina/api-client/customer  (public OpenAPI)
    #   - @nina/api-client/admin     (internal OpenAPI)
```

- **Design cohesion:** both apps consume `packages/ui` tokens & primitives.
- **Branding layer:** each app can override logo/accents, not tokens.

---

## 6) OpenAPI & Docs Policy (ties to SPEC-087)

### Two OpenAPI specs:
- **Public:** filtered allow-list of tags/paths; `/openapi.json` gated by sign-in.
- **Internal:** full schema; docs behind Tailnet/SSO on Admin host.

### Swagger/ReDoc (interactive)
- Visible **only** to authenticated users; schema filtered by role/scope.

### CI guardrails:
- Fail if any non-allow-listed path appears in **public** schema.
- Fail if `/_internal` or "admin" tag appears in public schema.
- Fail if any route lacks an explicit tag (forces classification).

---

## 7) Auth & RBAC

### Distinct OAuth/OIDC clients & JWT audiences:
- `aud=customer-app` vs `aud=admin-console`.

### Customer App
- End-user roles (owner/admin/member) + org/team scopes.

### Admin Console
- Staff roles (support, ops, analyst) + elevated scopes.

### Separate OAuth clients / JWT audiences:
- `aud=customer-app` vs `aud=admin-console`.

### Public routes
- Least privilege, sanitized outputs.

### Internal routes
- `require_staff` dependency + scope checks (admin:\*, ops:\*, analytics:\*).

### Audit logs
- Both surfaces (auth failures, memory access).

---

## 8) Deployment & Network

### Customer App + Public API
- Exposed via Funnel/ingress.

### Admin Console + Internal API
- Tailnet/SSO only; not funneled publicly.

### Optional
- Move to separate ports/processes for stronger isolation (recommended for prod).

---

## 9) Acceptance Criteria

1. Codebase contains **two apps**: `apps/customer`, `apps/admin-console`.
2. Shared UI tokens/components live in `packages/ui` and are used by **both** apps.
3. Two SDKs generated in `packages/api-client` (public/internal).
4. Public docs gated by sign-in and filtered by role; internal docs staff-only.
5. Ingress/Funnel exposes **only** Customer App + Public API.
6. CI policy tests block **any** public-surface drift.
7. E2E flows pass:
   - **Customer:** Signup → Record → Token visible → Copilot uses context
   - **Admin:** Login (SSO) → Admin dashboard loads → Metrics/audit visible

---

## 10) Migration Plan (low risk)

1. **Define public contract** (allow-listed tags/paths; versioned `/v1`).
2. **Split apps:** scaffold `apps/customer`, `apps/admin-console`; wire to the right API.
3. **Extract UI** into `packages/ui`; refactor both apps to use it.
4. **Generate SDKs** for public/internal OpenAPI to `packages/api-client`.
5. **Docs gating:** enable sign-in-only Swagger; role-filtered OpenAPI.
6. **Ingress:** publish Customer host only; keep Admin on Tailnet/SSO.
7. **CI guardrails:** add policy tests; fail on any leak.
8. **Agentic UI tests** (nightly):
   - Customer signup/record/tokenize
   - Admin login/metrics/audit
9. **Cut release tags:** `customer@v0.9`, `admin-console@v0.9`.

---

## 11) Naming Rules (enforced)

### Code & file system
- Use `customer` and `admin-console` only.

### UI labels/copy
- "Customer App", "Admin Console".

### Never use
- "Vendor" in code, envs, or URLs.

### If/when we add a partner-facing surface
- Name it **partner-portal** (third app).

---

## 12) Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Public/internal drift over time | CI policy tests + required tags; reviews require SPEC-087 alignment |
| Docs leak internal endpoints | Gated docs + role-filtered OpenAPI; ingress deny rules |
| Design divergence | Shared tokens/components; Storybook visual regression (optional) |

---

## 13) Deliverables

- New folders: `apps/customer`, `apps/admin-console`.
- Updated build scripts & CI (two web builds).
- OpenAPI split + generated SDKs.
- Docs: `CUSTOMER_APP_GUIDE.md`, `ADMIN_CONSOLE_GUIDE.md`.
- Policy tests: `tests/policy/test_public_surface.py`.

---

## 14) Success Metrics

- ✅ Two apps exist and build independently
- ✅ Shared `packages/ui` used by both
- ✅ Two generated SDKs (public/internal)
- ✅ Public docs gated & filtered; internal docs staff-only
- ✅ CI policy tests prevent public-surface drift
- ✅ E2E basic flows pass (customer & admin)
- ✅ Zero internal routes exposed on public host
- ✅ Agentic tests validate both surfaces nightly

---

**Next Steps:**
1. Approve SPEC-083
2. Create `apps/customer` and `apps/admin-console` scaffolds
3. Extract shared UI to `packages/ui`
4. Implement SPEC-087 (API Surface Contracts)
5. Run agentic tests (SPEC-084)
