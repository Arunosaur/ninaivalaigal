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
