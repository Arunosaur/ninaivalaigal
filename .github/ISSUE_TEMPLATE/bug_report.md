---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: ['bug', 'needs-triage']
assignees: ['swami']

---

## Bug Description

A clear and concise description of what the bug is.

## To Reproduce

Steps to reproduce the behavior:
1. Run command '...'
2. Navigate to '...'
3. See error

## Expected Behavior

A clear and concise description of what you expected to happen.

## Actual Behavior

What actually happened instead.

## Environment

**System Information:**
- OS: [e.g., macOS 14.1, Ubuntu 22.04]
- Container Runtime: [Apple Container CLI, Docker Desktop]
- System Role: [laptop, Mac Studio, server, deployment]

**Stack Information:**
- ninaivalaigal version: [e.g., 1.2.3]
- Memory Provider: [native, http]
- Database: [direct connection, via PgBouncer]

**Configuration:**
```bash
# Output of: make system-info
[paste output here]
```

## Logs

**Stack Status:**
```bash
# Output of: make stack-status
[paste output here]
```

**Container Logs:**
```bash
# Output of: container logs nv-api (or relevant service)
[paste relevant logs here]
```

**Health Check:**
```bash
# Output of: curl http://localhost:13370/health/detailed
[paste output here]
```

## Additional Context

Add any other context about the problem here.

## Security Considerations

- [ ] This bug does not expose sensitive information
- [ ] This bug does not affect authentication/authorization
- [ ] This bug does not compromise data integrity

## Possible Solution

If you have ideas on how to fix this, please describe them here.
