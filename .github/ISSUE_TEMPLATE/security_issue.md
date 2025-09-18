---
name: Security Issue
about: Report a security vulnerability (use private reporting for sensitive issues)
title: '[SECURITY] '
labels: ['security', 'critical']
assignees: ['swami']

---

## ⚠️ Security Issue Notice

**For sensitive security vulnerabilities, please use GitHub's private vulnerability reporting instead of creating a public issue.**

Go to: Repository → Security → Report a vulnerability

## Security Issue Type

- [ ] Authentication/Authorization bypass
- [ ] Data exposure/privacy violation
- [ ] Injection vulnerability (SQL, command, etc.)
- [ ] Cryptographic weakness
- [ ] Supply chain security issue
- [ ] Container/deployment security
- [ ] Secrets management issue
- [ ] Other security concern

## Affected Components

- [ ] API Server (FastAPI)
- [ ] Database (PostgreSQL/PgBouncer)
- [ ] mem0 Sidecar
- [ ] UI Frontend
- [ ] Apple Container CLI scripts
- [ ] CI/CD Pipeline
- [ ] Configuration/Environment
- [ ] Documentation

## Severity Assessment

- [ ] **Critical** - Immediate risk to production systems
- [ ] **High** - Significant security risk
- [ ] **Medium** - Moderate security concern
- [ ] **Low** - Minor security improvement

## Issue Description

Provide a clear description of the security issue:

## Steps to Reproduce

If applicable, provide steps to reproduce the issue:
1. 
2. 
3. 

## Impact Assessment

Describe the potential impact:
- **Confidentiality**: 
- **Integrity**: 
- **Availability**: 
- **Scope**: 

## Affected Versions

Which versions are affected?
- [ ] Latest main branch
- [ ] Specific version: 
- [ ] All versions
- [ ] Unknown

## Mitigation

Are there any workarounds or temporary mitigations?

## Proposed Fix

If you have ideas for fixing this issue:

## Additional Context

Any additional information that might be helpful:

---

**Note**: This project implements multiple security layers:
- Supply chain hardening with pinned images
- SBOM generation and vulnerability scanning
- Pre-commit hooks with secrets detection
- Authentication for mem0 sidecar
- Comprehensive backup verification
- SLO monitoring with health checks

Please consider which security layer this issue affects.
