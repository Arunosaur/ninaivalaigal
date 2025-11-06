---
title: Untitled SPEC
---


# SPEC-109: Environment Naming, Tagging & Versioning
**Status:** ⚠️ **In Progress** (Partially Implemented)
**Owner:** Release Engineering
**Last Updated:** November 4, 2025 (validation and stories created)

> **Standardizes** service naming, container tags, and semantic versioning for images and artifacts.

## 1. Naming
- **Services:** `ninaivalaigal-{{env}}-{{service}}`
- **Networks:** `{{env}}-ninaivalaigal-net`
- **Volumes:** `ninaivalaigal-{{env}}-{{service}}-data`

## 2. Tags
- `semver`: `vMAJOR.MINOR.PATCH`
- `channel`: `latest`, `dev`, `test`, `prod`
- `meta`: short SHA and date, e.g., `sha-abcdef1_2025-10-10`

## 3. Example
```
ghcr.io/medhasys/ninaivalaigal-api:v1.4.2
ghcr.io/medhasys/ninaivalaigal-api:dev
ghcr.io/medhasys/ninaivalaigal-api:sha-1a2b3c4_2025-10-10
```

## 4. Promotion Workflow (Mermaid)
```mermaid
flowchart LR
   A[Build (PR)] --> B[dev tag]
   B --> C[Tested]
   C --> D[Promote -> vX.Y.Z & test]
   D --> E[Smoke]
   E --> F[Promote -> prod channel]
```

## 5. Acceptance
- Every running container reports `SERVICE_NAME`, `SERVICE_VERSION`, `SERVICE_ENV` env vars.
- Audit script can map running pods to GHCR tags.

## 6. Implementation Status

**Partially Implemented (Nov 4, 2025):**
- ✅ Container naming: `ninaivalaigal-{{env}}-{{service}}` - **WORKING**
- ✅ SERVICE_NAME/SERVICE_VERSION/SERVICE_ENV: **Some usage found**
- ❌ Network naming: `{{env}}-ninaivalaigal-net` - **MISSING**
- ❌ Volume naming: `ninaivalaigal-{{env}}-{{service}}-data` - **MISSING**
- ❌ Semantic versioning tags (vX.Y.Z) - **MISSING**
- ❌ Channel tags (dev/test/prod/latest) - **MISSING**
- ❌ Meta tags (sha-{short_sha}_{date}) - **MISSING**
- ⚠️ Audit script: **Partial** (some scripts exist but not comprehensive)

## 7. Implementation Stories

The following Taiga stories have been created to complete SPEC-109 implementation:

- **US#693**: Enforce network naming convention ({{env}}-ninaivalaigal-net)
- **US#694**: Enforce volume naming convention (ninaivalaigal-{{env}}-{{service}}-data)
- **US#695**: Ensure all containers report SERVICE_NAME, SERVICE_VERSION, SERVICE_ENV env vars
- **US#696**: Implement semantic versioning tags (vMAJOR.MINOR.PATCH)
- **US#697**: Implement channel tags (latest, dev, test, prod)
- **US#698**: Implement meta tags (sha-{short_sha}_{date})
- **US#699**: Create audit script to map running containers to GHCR tags

All stories are tagged with `spec-109` and assigned to Developer C (ID: 8).
