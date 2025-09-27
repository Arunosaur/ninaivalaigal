# SPEC-013: Multi-Architecture Container Strategy

## Overview

This specification defines the multi-architecture container build and distribution strategy for ninaivalaigal, enabling universal deployment across ARM64 and x86_64 architectures with professional container registry distribution.

## Motivation

- **Universal Compatibility**: Support both ARM64 (Apple Silicon, AWS Graviton) and x86_64 (traditional servers) architectures
- **Performance Optimization**: Native performance on each architecture without emulation overhead
- **Professional Distribution**: Centralized container registry with proper versioning and access control
- **CI/CD Integration**: Automated multi-arch builds triggered by releases and tags

## Specification

### 1. Multi-Architecture Build System

#### 1.1 Docker Buildx Configuration
```yaml
# Required: Docker Buildx with multi-platform support
platforms:
  - linux/amd64   # x86_64 architecture
  - linux/arm64   # ARM64 architecture
```

#### 1.2 Dockerfile Requirements
- **Multi-stage builds** for optimization
- **Architecture-agnostic** base images
- **Health checks** for container orchestration
- **Non-root user** for security
- **Proper entry points** with path handling

### 2. Container Registry Strategy

#### 2.1 GitHub Container Registry (GHCR)
```
Registry: ghcr.io
Namespace: arunosaur/ninaivalaigal
Images:
  - ghcr.io/arunosaur/ninaivalaigal-api:latest
  - ghcr.io/arunosaur/ninaivalaigal-postgres:latest
  - ghcr.io/arunosaur/ninaivalaigal-pgbouncer:latest
```

#### 2.2 Tagging Strategy
- **latest**: Latest stable release
- **v{major}.{minor}.{patch}**: Semantic versioning
- **{timestamp}**: Build timestamp for traceability

### 3. Build Automation

#### 3.1 GitHub Actions Integration
```yaml
Triggers:
  - push: tags (v*.*.*)
  - workflow_dispatch: manual releases

Workflow:
  1. Checkout code
  2. Setup Docker Buildx
  3. Login to GHCR
  4. Build multi-arch images
  5. Push to registry
  6. Generate release summary
```

#### 3.2 Local Development Support
```bash
# Local multi-arch testing
make release-local

# Production release
make release
```

### 4. Image Specifications

#### 4.1 API Container (ninaivalaigal-api)
```dockerfile
Base: python:3.11-slim
Architecture: linux/amd64,linux/arm64
Features:
  - Multi-stage build (builder + runtime)
  - FastAPI application
  - Health checks (/health endpoint)
  - Non-root user (apiuser)
  - Proper Python path handling
```

#### 4.2 Database Container (ninaivalaigal-postgres)
```dockerfile
Base: postgres:15
Architecture: linux/amd64,linux/arm64
Features:
  - pgvector extension
  - Initialization scripts
  - Health checks (pg_isready)
  - Environment variable configuration
```

#### 4.3 PgBouncer Container (ninaivalaigal-pgbouncer)
```dockerfile
Base: debian:12-slim
Architecture: linux/amd64,linux/arm64
Features:
  - PgBouncer connection pooling
  - SCRAM-SHA-256 authentication
  - Template-based configuration
  - Environment variable substitution
```

## Implementation

### 1. File Structure
```
├── Dockerfile.api          # API container definition
├── Dockerfile.postgres     # Database container definition
├── Dockerfile.pgbouncer    # Connection pooler definition
├── requirements.txt        # Python dependencies
├── .github/workflows/
│   └── release-containers.yml  # Automated builds
└── Makefile                # Build automation
```

### 2. Makefile Targets
```makefile
release:          # Build and push multi-arch containers
release-local:    # Local multi-arch testing
```

### 3. GitHub Actions Workflow
- **Trigger**: Tag-based releases (v*.*.*)
- **Authentication**: GITHUB_TOKEN for GHCR access
- **Build**: Docker Buildx with platform targeting
- **Distribution**: Automated push to registry

## Testing Strategy

### 1. Local Testing
```bash
# Test multi-arch build locally
make release-local

# Verify images work on current architecture
docker run --rm ghcr.io/arunosaur/ninaivalaigal-api:local-test
```

### 2. CI Validation
- **x86_64 CI**: GitHub Actions runners validate x86_64 builds
- **ARM64 Local**: Apple Container CLI validates ARM64 builds
- **Health Checks**: All containers must pass health check validation

### 3. Registry Validation
```bash
# Pull and test from registry
docker pull ghcr.io/arunosaur/ninaivalaigal-api:latest
docker run --rm -p 8000:8000 ghcr.io/arunosaur/ninaivalaigal-api:latest
curl http://localhost:8000/health
```

## Security Considerations

### 1. Registry Access
- **Public Images**: No authentication required for pulls
- **Private Images**: GHCR_PAT token required
- **Build Secrets**: Managed via GitHub Secrets

### 2. Container Security
- **Non-root users** in all containers
- **Minimal base images** to reduce attack surface
- **Health checks** for proper lifecycle management
- **Secret management** via environment variables

## Monitoring & Observability

### 1. Build Metrics
- **Build duration** tracking
- **Image size** optimization monitoring
- **Success/failure rates** for multi-arch builds

### 2. Registry Metrics
- **Pull statistics** from GHCR
- **Image vulnerability scanning** (future enhancement)
- **Storage usage** monitoring

## Success Criteria

### 1. Functional Requirements
- ✅ Images build successfully on both ARM64 and x86_64
- ✅ Containers run natively on both architectures
- ✅ Automated builds trigger on tag releases
- ✅ Images are publicly accessible from GHCR

### 2. Performance Requirements
- ✅ Native performance on each architecture (no emulation)
- ✅ Build time < 10 minutes for all images
- ✅ Image sizes optimized (< 500MB for API container)

### 3. Operational Requirements
- ✅ One-command local testing (`make release-local`)
- ✅ One-command production release (`make release`)
- ✅ Automated CI/CD integration
- ✅ Proper versioning and tagging

## Future Enhancements

1. **Image Scanning**: Integrate vulnerability scanning
2. **SBOM Generation**: Software Bill of Materials for supply chain security
3. **Multi-Registry**: Support additional registries (Docker Hub, ECR)
4. **Optimization**: Further image size reduction and build speed improvements

## Dependencies

- Docker Buildx (multi-platform support)
- GitHub Container Registry access
- GitHub Actions (automated builds)
- Semantic versioning for releases

This specification ensures ninaivalaigal has professional, multi-architecture container distribution suitable for enterprise deployment across diverse infrastructure environments.
