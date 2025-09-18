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

- [ ] Tests pass locally with `make spec-test`
- [ ] Pre-commit hooks pass with `pre-commit run --all-files`
- [ ] Health checks pass with `make stack-status`
- [ ] Authentication tests pass with `make test-mem0-auth` (if applicable)
- [ ] Backup verification works with `make verify-latest` (if applicable)

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
