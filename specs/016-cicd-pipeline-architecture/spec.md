# SPEC-016: CI/CD Pipeline Architecture

## Overview

This specification defines the Continuous Integration and Continuous Deployment (CI/CD) pipeline architecture for ninaivalaigal, providing automated testing, building, and deployment workflows with multi-architecture support and comprehensive quality gates.

## Motivation

- **Automated Quality Assurance**: Comprehensive testing on every code change
- **Multi-Architecture Validation**: Ensure compatibility across ARM64 and x86_64
- **Automated Releases**: Tag-triggered container builds and deployments
- **Infrastructure Automation**: Automated infrastructure deployment and updates
- **Security Integration**: Automated security scanning and compliance checks
- **Developer Experience**: Fast feedback loops and easy deployment processes

## Specification

### 1. CI/CD Architecture Overview

#### 1.1 Pipeline Stages
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │───▶│   Build     │───▶│   Test      │───▶│   Deploy    │
│   Control   │    │   & Package │    │   & Verify  │    │   & Release │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                    │                    │                    │
      ▼                    ▼                    ▼                    ▼
  Git Push            Multi-Arch           Integration         Container
  PR Creation         Container            Testing             Registry
  Tag Release         Building             Security            Infrastructure
                                          Scanning            Deployment
```

#### 1.2 Workflow Triggers
```yaml
Triggers:
  push:
    branches: [main, master]           # Continuous Integration
    tags: ['v*.*.*']                   # Release Automation
  pull_request:
    branches: [main, master]           # PR Validation
  workflow_dispatch:                   # Manual Execution
  schedule:                            # Nightly Builds (future)
    - cron: '0 2 * * *'
```

### 2. Development Stack Validation

#### 2.1 Dev Stack CI Workflow
```yaml
# .github/workflows/dev-stack-validation.yml
Name: Dev Stack Validation
Purpose: Validate complete development stack on x86_64
Components:
  - PostgreSQL + pgvector
  - PgBouncer connection pooling
  - FastAPI application
  - Health endpoint validation
  - Database connectivity testing
```

#### 2.2 Validation Steps
```yaml
Steps:
  1. Checkout repository
  2. Set up Docker Buildx
  3. Install dependencies (jq)
  4. Build PostgreSQL image (x86_64)
  5. Build PgBouncer image (x86_64)
  6. Build API image (x86_64)
  7. Start PostgreSQL container
  8. Retrieve SCRAM password
  9. Start PgBouncer container
  10. Start API container
  11. Validate health endpoints
  12. Test database connectivity
  13. Cleanup containers
```

#### 2.3 Health Validation
```bash
Endpoints Tested:
  - GET /health              # Basic health check
  - GET /health/detailed     # Detailed system status
  - GET /memory/health       # Memory provider health

Database Tests:
  - PostgreSQL connectivity
  - PgBouncer connection pooling
  - pgvector extension availability
```

### 3. Multi-Architecture Container Release

#### 3.1 Release Workflow
```yaml
# .github/workflows/release-containers.yml
Name: Release Multi-Arch Docker Image
Trigger: Tag push (v*.*.*)
Architecture: linux/amd64,linux/arm64
Registry: GitHub Container Registry (GHCR)
```

#### 3.2 Build Process
```yaml
Steps:
  1. Checkout code
  2. Set up Docker Buildx
  3. Login to GHCR
  4. Build multi-arch API image
  5. Push to registry with tags:
     - ghcr.io/arunosaur/ninaivalaigal-api:latest
     - ghcr.io/arunosaur/ninaivalaigal-api:v{version}
  6. Generate release summary
```

#### 3.3 Container Images
```yaml
Images Built:
  - ninaivalaigal-api:      FastAPI application
  - ninaivalaigal-postgres: PostgreSQL + pgvector
  - ninaivalaigal-pgbouncer: Connection pooler

Platforms:
  - linux/amd64:  x86_64 architecture
  - linux/arm64:  ARM64 architecture
```

### 4. Infrastructure Deployment

#### 4.1 Infrastructure Workflow
```yaml
# .github/workflows/infra-deploy.yml
Name: Infrastructure Deployment
Trigger: workflow_dispatch (manual)
Providers: AWS, GCP, Azure
Actions: plan, apply, destroy
```

#### 4.2 Terraform Integration
```yaml
Cloud Providers:
  AWS:
    - Authentication: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    - Resources: ECS Fargate, ALB, CloudWatch
  GCP:
    - Authentication: GCP_SA_KEY (service account)
    - Resources: Cloud Run, Cloud SQL
  Azure:
    - Authentication: AZURE_CREDENTIALS
    - Resources: Container Instances, PostgreSQL
```

#### 4.3 Deployment Process
```yaml
Steps:
  1. Checkout code
  2. Setup Terraform
  3. Configure cloud credentials
  4. Initialize Terraform
  5. Plan infrastructure changes
  6. Apply changes (if approved)
  7. Output deployment results
```

### 5. Quality Gates and Security

#### 5.1 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
Hooks:
  - detect-secrets:     Secret scanning
  - shellcheck:         Shell script linting
  - black:              Python code formatting
  - flake8:             Python linting
  - mypy:               Python type checking
```

#### 5.2 Security Scanning
```yaml
# Future enhancement
Security Checks:
  - Container vulnerability scanning (Trivy)
  - Dependency vulnerability scanning
  - SAST (Static Application Security Testing)
  - License compliance checking
  - SBOM (Software Bill of Materials) generation
```

#### 5.3 Test Coverage
```yaml
Test Types:
  - Unit tests:         Individual component testing
  - Integration tests:  Component interaction testing
  - End-to-end tests:   Full workflow validation
  - Security tests:     Vulnerability and compliance
  - Performance tests:  Load and stress testing (future)
```

### 6. Deployment Strategies

#### 6.1 Environment Promotion
```yaml
Environments:
  Development:
    - Trigger: Every push to main
    - Validation: Basic health checks
    - Deployment: Automatic

  Staging:
    - Trigger: Tag creation
    - Validation: Full test suite
    - Deployment: Automatic with approval

  Production:
    - Trigger: Manual workflow dispatch
    - Validation: Comprehensive testing
    - Deployment: Manual approval required
```

#### 6.2 Rollback Strategy
```yaml
Rollback Mechanisms:
  - Container Registry: Previous image tags available
  - Kubernetes: Rolling update with health checks
  - Terraform: State rollback capabilities
  - Database: Migration rollback scripts
```

### 7. Monitoring and Observability

#### 7.1 Pipeline Metrics
```yaml
Metrics Tracked:
  - Build success/failure rates
  - Build duration and performance
  - Test coverage and results
  - Deployment frequency
  - Lead time for changes
  - Mean time to recovery (MTTR)
```

#### 7.2 Alerting
```yaml
Alert Conditions:
  - Build failures
  - Test failures
  - Security vulnerabilities
  - Deployment failures
  - Performance degradation
```

#### 7.3 Reporting
```yaml
Reports Generated:
  - Build status summaries
  - Test coverage reports
  - Security scan results
  - Deployment status
  - Performance metrics
```

## Implementation

### 1. GitHub Actions Workflows
```
.github/workflows/
├── dev-stack-validation.yml    # Development stack CI
├── release-containers.yml      # Multi-arch container release
└── infra-deploy.yml            # Infrastructure deployment
```

### 2. Makefile Integration
```makefile
# CI/CD related targets
ci-test:                # Local CI simulation with act
release:                # Build and push containers
release-local:          # Local multi-arch testing
terraform-apply-aws:    # Deploy AWS infrastructure
terraform-apply-gcp:    # Deploy GCP infrastructure
terraform-apply-azure:  # Deploy Azure infrastructure
```

### 3. Local Development Support
```bash
# Local CI testing
make ci-test            # Simulate GitHub Actions locally

# Local container testing
make release-local      # Test multi-arch builds locally

# Local infrastructure testing
make terraform-plan-aws # Plan infrastructure changes
```

## Security Considerations

### 1. Secrets Management
```yaml
GitHub Secrets:
  - GITHUB_TOKEN:         Container registry access
  - AWS_ACCESS_KEY_ID:    AWS authentication
  - AWS_SECRET_ACCESS_KEY: AWS authentication
  - GCP_SA_KEY:           GCP service account
  - AZURE_CREDENTIALS:    Azure authentication
```

### 2. Access Control
```yaml
Permissions:
  - Repository access:    Limited to authorized developers
  - Workflow permissions: Minimal required permissions
  - Registry access:      Read/write for CI, read-only for deployments
  - Cloud access:         Environment-specific service accounts
```

### 3. Supply Chain Security
```yaml
Security Measures:
  - Signed commits:       Verify code authenticity
  - Dependency scanning:  Check for vulnerable dependencies
  - Container scanning:   Scan images for vulnerabilities
  - SBOM generation:      Track software components
```

## Testing Strategy

### 1. Pipeline Testing
```bash
# Test workflows locally
act -j dev-stack                    # Test dev stack validation
act -j release                      # Test container release
act workflow_dispatch               # Test manual workflows
```

### 2. Integration Testing
```bash
# End-to-end pipeline testing
git tag v1.0.0-test                # Trigger release workflow
git push origin v1.0.0-test        # Push test tag

# Verify container registry
docker pull ghcr.io/arunosaur/ninaivalaigal-api:v1.0.0-test
```

### 3. Infrastructure Testing
```bash
# Test infrastructure deployment
terraform plan -var="environment=test"
terraform apply -var="environment=test"
curl https://test-api.ninaivalaigal.com/health
terraform destroy -var="environment=test"
```

## Success Criteria

### 1. Functional Requirements
- ✅ All workflows execute successfully
- ✅ Multi-architecture containers build and deploy
- ✅ Infrastructure deploys across all cloud providers
- ✅ Health checks pass consistently
- ✅ Rollback mechanisms work properly

### 2. Performance Requirements
- ✅ Build time < 10 minutes for complete pipeline
- ✅ Test execution < 5 minutes
- ✅ Deployment time < 3 minutes
- ✅ Pipeline feedback < 15 minutes total

### 3. Quality Requirements
- ✅ Test coverage > 80%
- ✅ Security scans pass
- ✅ No critical vulnerabilities
- ✅ All quality gates pass

## Future Enhancements

1. **Advanced Testing**: Performance testing, chaos engineering
2. **Security Enhancement**: Advanced SAST/DAST integration
3. **Deployment Strategies**: Blue-green, canary deployments
4. **Monitoring Integration**: Pipeline metrics in observability stack
5. **GitOps**: ArgoCD integration for declarative deployments
6. **Multi-Environment**: Automated environment provisioning

## Dependencies

- GitHub Actions (CI/CD platform)
- Docker Buildx (multi-architecture builds)
- GitHub Container Registry (image storage)
- Terraform (infrastructure as code)
- Cloud provider accounts (AWS, GCP, Azure)
- act (local workflow testing)

This specification ensures ninaivalaigal has enterprise-grade CI/CD capabilities with comprehensive automation, quality gates, and deployment strategies suitable for production environments.
