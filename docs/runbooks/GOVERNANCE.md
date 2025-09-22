# Project Governance

This document outlines the governance structure, processes, and policies for the ninaivalaigal project.

## Overview

The ninaivalaigal project is a production-ready Universal Memory Layer for AI Agents and Developers, built with enterprise-grade security and reliability. This governance framework ensures consistent quality, security, and maintainability.

## Project Structure

### Core Components

1. **API Server** - FastAPI with comprehensive authentication and RBAC
2. **Database Layer** - PostgreSQL 15 with pgvector and PgBouncer pooling
3. **Memory Service** - mem0 sidecar with authenticated access
4. **UI Frontend** - React application with Nginx
5. **Infrastructure** - Apple Container CLI scripts for Mac Studio deployment

### Security Framework

- **Supply Chain Hardening** - Pinned container images with SHA digests
- **Vulnerability Management** - Automated SBOM generation and Trivy scanning
- **Code Quality** - Pre-commit hooks with 15+ security and quality checks
- **Secrets Management** - detect-secrets with baseline management
- **Authentication** - HMAC-SHA256 for inter-service communication
- **Observability** - Prometheus metrics with SLO monitoring

## Roles and Responsibilities

### Maintainer (@swami)

**Responsibilities:**
- Overall project direction and architecture decisions
- Security review and approval of all changes
- Release management and version control
- Infrastructure and deployment oversight
- Community management and issue triage

**Permissions:**
- Full repository access
- Release creation and management
- Security vulnerability management
- CI/CD pipeline configuration
- Container registry management

### Contributors

**Responsibilities:**
- Follow contribution guidelines and code standards
- Write comprehensive tests for new features
- Update documentation for changes
- Participate in code review process
- Report security issues responsibly

**Requirements:**
- All contributions must pass pre-commit hooks
- Security-sensitive changes require maintainer approval
- Breaking changes require RFC process
- Follow conventional commit format

## Development Process

### Branching Strategy

- **main** - Production-ready code, protected branch
- **develop** - Integration branch for features (optional)
- **feature/** - Feature development branches
- **hotfix/** - Critical production fixes
- **security/** - Security-related changes

### Code Review Process

1. **All changes require pull request review**
2. **CODEOWNERS automatically assigns reviewers**
3. **Security-sensitive files require maintainer approval**
4. **CI/CD must pass before merge**
5. **Pre-commit hooks must pass**

### Required Checks

- ✅ Pre-commit hooks (15+ quality and security checks)
- ✅ SPEC validation tests
- ✅ Health check and SLO compliance
- ✅ Authentication tests (for HTTP memory provider)
- ✅ Security scanning (SBOM + vulnerability detection)
- ✅ Backup verification (if applicable)

## Release Management

### Semantic Versioning

The project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** - Breaking changes
- **MINOR** - New features (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

### Release Process

1. **Automated Release** - Semantic-release handles version bumping and changelog
2. **Container Images** - Multi-arch builds pushed to GitHub Container Registry
3. **SBOM Generation** - Software Bill of Materials for all containers
4. **Release Notes** - Auto-generated from conventional commits
5. **Artifact Management** - SBOMs and documentation attached to releases

### Release Types

- **Production Releases** - From main branch (stable)
- **Beta Releases** - From develop branch (pre-release)
- **Hotfix Releases** - Critical security/bug fixes

## Security Policies

### Vulnerability Reporting

1. **Private Reporting** - Use GitHub's private vulnerability reporting for sensitive issues
2. **Public Issues** - Use security issue template for general security improvements
3. **Response Time** - 48 hours for critical, 1 week for non-critical
4. **Disclosure** - Coordinated disclosure after fix is available

### Security Review Requirements

**Critical Files (Require Maintainer Approval):**
- Authentication and authorization code
- Database and backup scripts
- Container and deployment configurations
- CI/CD pipeline definitions
- Security configuration files

**Security Checklist:**
- [ ] No hardcoded secrets or credentials
- [ ] Input validation and sanitization
- [ ] Authentication/authorization properly implemented
- [ ] Dependencies are up-to-date and secure
- [ ] Container images use pinned digests

### Supply Chain Security

- **Image Pinning** - All container images pinned with SHA256 digests
- **SBOM Generation** - Software Bill of Materials for compliance
- **Vulnerability Scanning** - Automated scanning with Trivy
- **Dependency Management** - Regular updates with security review
- **Secrets Detection** - Pre-commit hooks prevent secret commits

## Quality Standards

### Code Quality

- **Pre-commit Hooks** - Automated formatting, linting, and security checks
- **Type Safety** - Python type hints required for all functions
- **Documentation** - Comprehensive docstrings and README updates
- **Testing** - Minimum 80% test coverage for new features
- **Shell Scripts** - Must follow `set -euo pipefail` best practices

### Performance Standards

- **SLO Compliance** - 99.9% availability, p95 <250ms response time
- **Health Monitoring** - Detailed health checks with latency tracking
- **Resource Efficiency** - Container resource limits and monitoring
- **Database Performance** - Query optimization and connection pooling

### Documentation Standards

- **API Documentation** - OpenAPI/Swagger for all endpoints
- **Deployment Guides** - Step-by-step setup instructions
- **Security Documentation** - Authentication and security procedures
- **Troubleshooting** - Common issues and solutions
- **Architecture** - System design and component relationships

## Communication

### Issue Management

- **Bug Reports** - Use bug report template with environment details
- **Feature Requests** - Use feature request template with use cases
- **Security Issues** - Use security issue template or private reporting
- **Questions** - Use discussions for general questions

### Decision Making

- **Technical Decisions** - Maintainer has final authority
- **Breaking Changes** - Require RFC process and community input
- **Security Decisions** - Maintainer authority with security-first approach
- **Feature Priorities** - Based on community needs and project roadmap

## Compliance and Audit

### Regular Reviews

- **Monthly** - Security dependency updates
- **Quarterly** - SLO performance review
- **Annually** - Full security audit and governance review

### Audit Trail

- **All changes tracked** - Git history with signed commits
- **Release artifacts** - SBOMs and security scans
- **CI/CD logs** - Complete build and test history
- **Security events** - Authentication logs and security incidents

### Compliance Standards

- **Supply Chain Security** - NIST guidelines and best practices
- **Container Security** - CIS benchmarks and security scanning
- **Code Quality** - Industry-standard linting and formatting
- **Documentation** - Comprehensive and up-to-date

## Amendment Process

This governance document may be updated through:

1. **Pull Request** - Proposed changes via PR
2. **Community Review** - Discussion and feedback period
3. **Maintainer Approval** - Final approval by project maintainer
4. **Documentation Update** - Changes reflected in governance docs

## Contact

For governance questions or concerns:
- **GitHub Issues** - Public discussion
- **Security Issues** - Private vulnerability reporting
- **Direct Contact** - @swami for urgent governance matters

This governance framework ensures the ninaivalaigal project maintains high standards of security, quality, and reliability while fostering a collaborative development environment.
