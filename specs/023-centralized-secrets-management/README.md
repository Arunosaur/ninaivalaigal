---
title: Untitled SPEC
---


# SPEC-023: Centralized Secrets Management

## Title
Secure Secret Delivery & Encryption

## Objective
Manage secrets securely across environments and cloud providers.

## Features

- Support for:
  - `sealed-secrets` (K8s native)
  - `SOPS` with GPG or KMS
  - External Vault integration (optional)
- GitHub Actions integration for secret delivery
- Secret rotation policies

## Implementation Targets

- Secret pull during GitHub workflow
- K8s support for mounting secrets via sidecars

## Technical Requirements

### Sealed Secrets (Kubernetes Native)
```yaml
# secrets/sealed-secret-controller.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sealed-secrets
---
# Install sealed-secrets controller
```

### SOPS Integration
```yaml
# .sops.yaml
creation_rules:
  - path_regex: secrets/.*\.yaml$
    kms: 'arn:aws:kms:us-west-2:123456789:key/12345678-1234-1234-1234-123456789012'  # pragma: allowlist secret
    pgp: 'FBC7B9E2A4F9289AC0C1D4843D16CEE4A27381B4'  # pragma: allowlist secret
```

### GitHub Actions Secret Management
```yaml
# .github/workflows/secrets.yml
name: Deploy Secrets
on:
  push:
    paths: ['secrets/**']
jobs:
  deploy-secrets:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Decrypt and apply secrets
      run: |
        sops -d secrets/production.yaml | kubectl apply -f -
```

### Secret Rotation
- Automated rotation for database passwords
- JWT secret rotation with zero-downtime
- API key rotation with notification

## Success Criteria
- [ ] Secrets encrypted at rest and in transit
- [ ] Automated secret rotation working
- [ ] GitHub Actions can deploy secrets securely
- [ ] Audit trail for all secret access

## Status
📋 Planned

---

## Related Documentation

### Secret Management Options
- **sealed-secrets:** Kubernetes-native, GitOps friendly
- **SOPS:** File-based encryption with GPG/KMS
- **Vault:** Enterprise solution (optional, heavier weight)

### Related SPECs
- **SPEC-021:** GitOps with ArgoCD (secret deployment workflow)
- **SPEC-015:** Kubernetes Deployment Strategy (secret mounting)
- **SPEC-009:** RBAC Policy Enforcement (access control)

### Taiga Tracking
- **US#153:** SPEC-023 Centralized Secrets Management

---

## Implementation Status

📋 **PLANNED** - Not yet implemented

**Key Decisions Needed:**
1. Choose solution: sealed-secrets vs SOPS vs Vault
2. Encryption backend: GPG vs KMS vs age
3. Rotation frequency: Daily, weekly, or on-demand

**Current Secrets to Migrate:**
- Database credentials
- Redis password
- API keys (OpenAI, Stripe)
- JWT signing secrets
- OAuth client secrets
- Container registry credentials

**Estimated Effort:** 2-3 weeks

---

**Last Updated:** October 30, 2025 (Taiga tracking added)
**Status:** Tracked in Taiga US#153
