# 🤝 Contributing to ninaivalaigal

## 🎯 Quick Start

1. **Fork & Clone**: Fork the repo and clone locally
2. **Setup**: Run `make dev-setup` for complete environment
3. **Branch**: Create feature branch `feature/spec-xxx-description`
4. **Develop**: Follow TDD and implement SPEC requirements
5. **Test**: Ensure 80%+ coverage and all tests pass
6. **Submit**: Create PR with clear description

## 📋 Development Process

### SPEC Implementation
1. **Choose SPEC**: Pick from [SPEC_AUDIT_2024.md](SPEC_AUDIT_2024.md)
2. **Read Requirements**: Understand SPEC in `specs/` directory
3. **Create Branch**: `git checkout -b feature/spec-xxx-name`
4. **Implement**: Follow existing patterns and architecture
5. **Test**: Write comprehensive tests
6. **Document**: Update relevant documentation

### Code Standards
- **Python**: PEP 8, type hints, 80% test coverage
- **JavaScript**: ESLint + Prettier
- **Git**: Conventional commits (feat:, fix:, docs:)
- **Documentation**: Update docs for any user-facing changes

### Pull Request Guidelines
- **Title**: Clear, descriptive (e.g., "feat: implement SPEC-060 Apache AGE integration")
- **Description**: What, why, how, testing approach
- **Tests**: All new code must have tests
- **Documentation**: Update relevant docs
- **Breaking Changes**: Clearly marked and documented

## 🧪 Testing Requirements

### Test Coverage
- **Minimum**: 80% overall coverage
- **New Code**: 90%+ coverage required
- **Critical Paths**: 100% coverage (auth, security, data)

### Test Types
```bash
make test-unit        # Unit tests
make test-integration # Integration tests
make test-security    # Security tests
make test-performance # Performance benchmarks
```

## 📚 Documentation

### Required Updates
- **API Changes**: Update `docs/api/README.md`
- **Architecture**: Update `docs/architecture/README.md`
- **Setup Changes**: Update `docs/development/setup.md`
- **SPEC Status**: Update `SPEC_AUDIT_2024.md`

## 🎯 Current Priorities

### High Priority SPECs (Ready for Implementation)
1. **SPEC-060**: Apache AGE Property Graph Model
2. **SPEC-061**: Property Graph Intelligence Framework
3. **SPEC-054**: Secret Management & Environment Hygiene
4. **SPEC-055**: Codebase Refactor & Modularization

### Getting Started Recommendations
- **New Contributors**: Start with SPEC-054 (secret management)
- **Experienced**: Take on SPEC-060/061 (graph intelligence)
- **Frontend**: Work on admin dashboard completion
- **DevOps**: Implement monitoring SPECs (022-024)

## 🆘 Getting Help

- **Documentation**: Check `docs/` directory first
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Setup Problems**: See `docs/development/setup.md`

## 🏆 Recognition

Contributors are recognized in:
- **README.md**: Contributors section
- **CHANGELOG.md**: Release notes
- **GitHub**: Contributor graphs and stats

---

**Thank you for contributing to ninaivalaigal!** 🚀
