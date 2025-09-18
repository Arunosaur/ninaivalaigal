# Pull Request

## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] 🚀 New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔒 Security improvement
- [ ] ⚡ Performance improvement
- [ ] 🧹 Code cleanup/refactoring
- [ ] 🚨 Test improvement
- [ ] 🛠 Build/CI improvement

## Testing

### **Core Validation (Required)**
- [ ] **SPEC Tests**: `make spec-test` - All SPECs pass
- [ ] **Pre-commit Hooks**: `pre-commit run --all-files` - All 15+ hooks pass
- [ ] **Stack Health**: `make stack-up && make stack-status` - All 5 services healthy
- [ ] **SLO Compliance**: `curl http://localhost:13370/health/detailed` - Latency under targets

### **Security & Authentication (If Applicable)**
- [ ] **mem0 Authentication**: `make test-mem0-auth` - All auth tests pass
- [ ] **Secrets Detection**: No new secrets detected in baseline
- [ ] **Container Security**: SBOM generation successful
- [ ] **Vulnerability Scan**: No new CRITICAL/HIGH vulnerabilities

### **Backup & Recovery (If Applicable)**
- [ ] **Backup Creation**: `make backup` - Backup completes successfully
- [ ] **Backup Verification**: `make verify-latest` - Integrity check passes
- [ ] **Restore Rehearsal**: Backup can be restored without issues

### **Mac Studio Validation (Production)**
- [ ] **Apple Container CLI**: All scripts use `container` commands (no `docker`)
- [ ] **Error Handling**: Scripts follow `set -euo pipefail` best practices
- [ ] **Health Monitoring**: Container logs show healthy startup sequences
- [ ] **Network Connectivity**: Services can reach each other properly

## Security Checklist

- [ ] No hardcoded secrets or credentials
- [ ] Input validation implemented where needed
- [ ] Authentication/authorization considered
- [ ] Dependency updates are security-reviewed
- [ ] Container images use pinned digests (if applicable)

## Documentation

- [ ] Code is self-documenting with clear variable/function names
- [ ] Complex logic includes comments
- [ ] API changes are documented
- [ ] README updated if needed
- [ ] New environment variables added to `.env.example`

## Deployment

- [ ] Changes are backward compatible
- [ ] Database migrations included (if applicable)
- [ ] Environment variables documented
- [ ] Rollback plan considered
- [ ] SLO impact assessed

## Apple Container CLI (Mac Studio)

- [ ] Scripts follow `set -euo pipefail` best practices
- [ ] Container commands use Apple Container CLI syntax
- [ ] Error handling and logging implemented
- [ ] Health checks and status monitoring included
- [ ] Integration with existing stack management

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Related Issues

Closes #(issue number)

## Screenshots (if applicable)

## Additional Notes

Any additional information that reviewers should know.
