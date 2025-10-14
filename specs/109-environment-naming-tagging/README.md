---
title: Untitled SPEC
---


# SPEC-109: Environment Naming, Tagging & Versioning
**Status:** Draft
**Owner:** Release Engineering
**Last Updated:** 2025-10-11

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
