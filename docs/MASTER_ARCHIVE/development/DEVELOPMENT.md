# Development Guide

This guide covers the development workflow, tools, and best practices for the ninaivalaigal project.

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for UI development)
- Apple Container CLI or Docker
- Git

### Setup Development Environment

```bash
# Clone with submodules (recommended)
git clone --recurse-submodules <repo-url>
cd ninaivalaigal

# Or if already cloned, initialize submodules
git submodule update --init --recursive

# Install pre-commit hooks (REQUIRED)
pip install pre-commit
pre-commit install

# Install development dependencies
pip install -r requirements-dev.txt

# Verify setup
make system-info
```

## Pre-commit Hooks

**All commits are automatically validated** with comprehensive checks:

### Code Quality
- **Black**: Python code formatting
- **isort**: Import sorting
- **Ruff**: Fast Python linting and formatting
- **Flake8**: Python style guide enforcement
- **MyPy**: Static type checking

### Security
- **detect-secrets**: Prevents secrets from being committed
- **Bandit**: Security linting for Python code
- **Shellcheck**: Shell script analysis

### General
- **YAML/JSON validation**: Syntax checking
- **Trailing whitespace removal**
- **Large file detection** (>1MB blocked)
- **Merge conflict detection**

### Running Pre-commit

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run

# Update hook versions
pre-commit autoupdate

# Skip hooks (emergency only)
git commit --no-verify
```

## Development Workflow

### 1. Feature Development
```bash
# Create feature branch
git checkout -b feature/spec-013-team-rollup

# Make changes with system-aware guidance
make spec-new ID=013 NAME="team-rollup"  # Laptop optimized
make spec-test ID=013                     # Studio optimized

# Pre-commit runs automatically on commit
git add .
git commit -m "feat: Add SPEC 013 - Team Rollup Layer"
```

### 2. Testing Strategy
```bash
# Local development (laptop)
make stack-up --skip-mem0    # Lightweight stack
make spec-test ID=013        # Basic validation

# Production validation (Mac Studio)
make stack-up --with-ui      # Full 5-service stack
make spec-test ID=013        # Heavy validation
```

### 3. CI/CD Integration
- **Pre-commit CI**: Runs on every PR
- **SPEC Matrix Testing**: Mac Studio validation
- **Security Scanning**: SBOM + vulnerability detection
- **Deployment**: Automated on main branch

## Code Standards

### Python
- **Line length**: 88 characters (Black standard)
- **Type hints**: Required for all functions
- **Docstrings**: Required for public APIs
- **Testing**: Minimum 80% coverage

### Shell Scripts
- **Shellcheck**: All scripts must pass
- **Error handling**: `set -euo pipefail` required
- **Documentation**: Function comments for complex logic

### Security
- **No secrets**: Use environment variables
- **Input validation**: All user inputs validated
- **Dependency pinning**: Exact versions in requirements.txt

## Tools and Configuration

### Editor Setup
```bash
# VS Code extensions (recommended)
- Python
- Black Formatter
- Ruff
- YAML
- ShellCheck

# Settings
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

### Environment Variables
```bash
# Development (.env)
POSTGRES_PASSWORD=dev_password  # pragma: allowlist secret_change_me
NINAIVALAIGAL_JWT_SECRET=dev-secret-change-in-production
MEMORY_PROVIDER=native  # Laptop: native, Studio: http

# Production
DEPLOYMENT_ENV=production
POSTGRES_PASSWORD=<secure-password  # pragma: allowlist secret>
NINAIVALAIGAL_JWT_SECRET=<secure-jwt-secret>
```

## Troubleshooting

### Pre-commit Issues
```bash
# Hook installation failed
pre-commit clean
pre-commit install

# Secrets detected
detect-secrets scan --baseline .secrets.baseline
# Review and update baseline if legitimate

# Shellcheck errors
shellcheck scripts/problematic-script.sh
# Fix issues or add exclusions
```

### System Detection
```bash
# Check system capabilities
make system-info

# Force deployment mode
DEPLOYMENT_ENV=production make spec-test ID=013

# Debug container issues
container system status
container list
```

### Stack Issues
```bash
# Reset everything
make stack-down
container system stop
container system start
make stack-up

# Check individual services
make stack-status
container logs nv-db
container logs nv-api
```

## Best Practices

### Git Workflow
1. **Small commits**: Single logical change per commit
2. **Descriptive messages**: Follow conventional commits
3. **Pre-commit compliance**: Never skip hooks
4. **Branch naming**: `feature/spec-###-name` or `fix/issue-description`

### SPEC Development
1. **Laptop authoring**: Fast iteration and hot-reload
2. **Studio validation**: Production-like testing
3. **CI verification**: Automated matrix testing
4. **Documentation**: Keep SPECs current and testable

### Security Practices
1. **Environment variables**: Never hardcode secrets
2. **Dependency updates**: Regular security patches
3. **Access control**: Principle of least privilege
4. **Audit logging**: Track all sensitive operations

This development environment provides enterprise-grade quality gates while maintaining developer productivity and system-aware optimization.

## External Submodules

Some platform/infrastructure SPECs are maintained as external repositories:

- **SPEC-013** (Mac Studio validation): `external/spec-013/`
  - Repository: https://github.com/Arunosaur/spec-013-mac-studio-validation
  - Purpose: Apple Container CLI validation toolkit
  - CI: Independent workflows (hosted + self-hosted Mac Studio)

### Working with Submodules

```bash
# Clone with submodules
git clone --recurse-submodules git@github.com:Arunosaur/ninaivalaigal.git

# Update submodule to latest
git submodule update --remote external/spec-013

# Make changes in submodule
cd external/spec-013
# edit, commit, push
git commit -am "update validation scripts"
git push

# Update pointer in main repo
cd ../..
git add external/spec-013
git commit -m "chore: bump SPEC-013 pointer"
git push
```

### Separation of Concerns

- **Main repo**: Core AI memory features, API, and product SPECs
- **External SPECs**: Platform validation, infrastructure testing, reusable toolkits
- **CI isolation**: External SPEC failures don't block main project development
