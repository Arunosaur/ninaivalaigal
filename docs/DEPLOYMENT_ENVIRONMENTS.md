# Deployment Environment Compatibility

This document explains how the ninaivalaigal system adapts to different deployment environments while maintaining full functionality.

## Environment Detection

The system automatically detects deployment environments and disables interactive features to ensure compatibility with CI/CD, containers, and cloud deployments.

### Deployment Environment Triggers

The system considers itself in a "deployment environment" when any of these conditions are met:

```bash
# CI/CD Environments
CI=true                    # Generic CI flag
GITHUB_ACTIONS=true        # GitHub Actions
DEPLOYMENT_ENV=production  # Custom deployment flag

# Container Environments  
DOCKER_CONTAINER=true      # Docker container
/.dockerenv               # Docker container file

# Kubernetes
KUBERNETES_SERVICE_HOST    # Kubernetes environment
```

### Behavior Changes in Deployment Mode

#### ✅ **Enabled in Deployment**
- All core functionality (stack management, SPEC testing, etc.)
- System detection and capability reporting
- Automated operations and scripting
- Container runtime detection
- Development tool availability checks

#### 🚫 **Disabled in Deployment**
- Interactive prompts and confirmations
- Hardware-specific recommendations (Mac Studio vs laptop)
- `system_profiler` calls (macOS hardware detection)
- User input requests (`read -p`)

## Platform Compatibility

### macOS (Development & CI)
```bash
# Local development
SYSTEM_ROLE=studio|laptop  # Based on hardware detection
SYSTEM_CAPABILITIES=heavy_validation,ci_runner,production_stack

# CI/CD deployment
SYSTEM_ROLE=deployment
SYSTEM_CAPABILITIES=production_stack,ci_runner,automated_testing
```

### Linux (Servers, Containers, Cloud)
```bash
# Bare metal / VM
SYSTEM_ROLE=server
SYSTEM_CAPABILITIES=ci_runner,production_stack,development

# Container deployment
SYSTEM_ROLE=deployment
SYSTEM_CAPABILITIES=production_stack,ci_runner,automated_testing
SYSTEM_CONTAINER_TYPE=docker|kubernetes|generic
```

### Container Environments

#### Docker
```dockerfile
# Dockerfile example
FROM ubuntu:22.04
ENV DEPLOYMENT_ENV=production
ENV DOCKER_CONTAINER=true
# System will automatically detect deployment mode
```

#### Kubernetes
```yaml
# Deployment example
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: ninaivalaigal
        env:
        - name: DEPLOYMENT_ENV
          value: "production"
        # KUBERNETES_SERVICE_HOST automatically set by K8s
```

## Usage Examples

### Local Development
```bash
# Interactive mode with recommendations
make system-info
make spec-new ID=013 NAME="feature"  # May show Studio vs laptop guidance
```

### CI/CD Pipeline
```bash
# Automated mode - no prompts
CI=true make system-info
CI=true make spec-new ID=013 NAME="feature"  # Proceeds automatically
CI=true make spec-test ID=013  # Runs without user interaction
```

### Cloud Deployment
```bash
# Production deployment
DEPLOYMENT_ENV=production make stack-up
DEPLOYMENT_ENV=production make stack-status
```

### Container Deployment
```bash
# Docker
docker run -e DEPLOYMENT_ENV=production ninaivalaigal make stack-up

# Kubernetes
kubectl set env deployment/ninaivalaigal DEPLOYMENT_ENV=production
```

## Environment Variables Reference

### Core Deployment Flags
```bash
CI=true|false                    # Generic CI environment
GITHUB_ACTIONS=true|false        # GitHub Actions specific
DEPLOYMENT_ENV=production|staging # Custom deployment environment
DOCKER_CONTAINER=true|false      # Docker container flag
```

### System Override Variables
```bash
SYSTEM_ROLE=deployment|studio|laptop|server  # Force specific role
SYSTEM_CAPABILITIES=production_stack,ci_runner  # Override capabilities
```

### Stack Configuration
```bash
# All existing stack variables work in deployment mode
POSTGRES_HOST=db.example.com
MEMORY_PROVIDER=http
API_RELOAD=false
# etc.
```

## Validation

### Test Deployment Mode
```bash
# Simulate CI environment
CI=true make system-info

# Simulate Docker container
DOCKER_CONTAINER=true make system-info

# Simulate production deployment
DEPLOYMENT_ENV=production make stack-up
```

### Expected Output in Deployment Mode
```
SYSTEM_IS_DEPLOYMENT=true
SYSTEM_ROLE=deployment
SYSTEM_CAPABILITIES=production_stack,ci_runner,automated_testing

Recommendations for deployment:
  • Deployment environment detected - automated operations enabled
  • Interactive prompts disabled for CI/CD compatibility
  • Optimized for: automated testing, production deployments
```

## Best Practices

### For CI/CD Pipelines
1. Always set `CI=true` or `DEPLOYMENT_ENV=production`
2. Use environment variables for all configuration
3. Test both local and deployment modes
4. Monitor system detection output for debugging

### For Container Deployments
1. Set `DEPLOYMENT_ENV=production` in container environment
2. Use health checks to verify stack status
3. Configure proper resource limits
4. Use secrets management for sensitive variables

### For Cloud Deployments
1. Use cloud-native environment variable injection
2. Configure proper networking and service discovery
3. Set up monitoring and logging
4. Use managed databases when possible

## Troubleshooting

### System Not Detecting Deployment Mode
```bash
# Manually force deployment mode
export DEPLOYMENT_ENV=production
make system-info

# Check environment variables
env | grep -E "(CI|GITHUB|DEPLOYMENT|DOCKER|KUBERNETES)"
```

### Interactive Prompts in CI
If you see interactive prompts in CI, ensure one of these is set:
- `CI=true`
- `GITHUB_ACTIONS=true` 
- `DEPLOYMENT_ENV=production`
- `DOCKER_CONTAINER=true`

### Container Runtime Issues
```bash
# Check container runtime availability
make system-info | grep CONTAINER_RUNTIME

# Verify Apple Container CLI vs Docker
container --version || docker --version
```

This deployment-aware system ensures your ninaivalaigal stack works seamlessly across all environments while providing optimal user experience in each context.
