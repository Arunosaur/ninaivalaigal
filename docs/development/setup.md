# 🚀 Developer Setup Guide

## 🎯 Quick Start (5 Minutes)

### Prerequisites
- **Apple Silicon Mac** (M1/M2/M3) or x86_64 Linux
- **Apple Container CLI** or Docker Desktop
- **Python 3.11+**
- **Node.js 18+**
- **Git**

### One-Command Setup
```bash
# Clone and setup
git clone https://github.com/Arunosaur/ninaivalaigal.git
cd ninaivalaigal
make dev-setup
```

## 🛠️ Detailed Setup

### Step 1: Environment Setup
```bash
# Install Apple Container CLI (Mac)
curl -fsSL https://get.docker.com | sh

# Or install Docker Desktop (alternative)
# Download from: https://www.docker.com/products/docker-desktop

# Verify installation
container --version
```

### Step 2: Repository Setup
```bash
# Clone repository
git clone https://github.com/Arunosaur/ninaivalaigal.git
cd ninaivalaigal

# Install Python dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Setup environment variables
cp .env.example .env
```

### Step 3: Database Setup
```bash
# Start PostgreSQL with pgvector
./scripts/nv-db-start.sh

# Run database migrations
make db-migrate

# Verify database connection
make db-test
```

### Step 4: Redis Setup
```bash
# Start Redis cache
./scripts/nv-redis-start.sh

# Verify Redis connection
make redis-test
```

### Step 5: API Server
```bash
# Start FastAPI server
./scripts/nv-api-start.sh

# Verify API health
curl http://localhost:8000/health
```

### Step 6: Frontend Setup
```bash
# Install frontend dependencies
cd frontend
npm install

# Start development server
npm run dev

# Verify frontend (http://localhost:3000)
```

## 🧪 Development Workflow

### Running Tests
```bash
# Run all tests
make test

# Run specific test suites
make test-auth        # Authentication tests
make test-memory      # Memory system tests
make test-redis       # Redis integration tests
make test-security    # Security tests
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Type checking
make typecheck

# Security scanning
make security-scan
```

### Database Operations
```bash
# Create migration
make db-migration name="add_new_feature"

# Apply migrations
make db-migrate

# Reset database (development only)
make db-reset
```

## 🔧 Development Tools

### Recommended IDE Setup
- **VS Code** with extensions:
  - Python
  - Pylance
  - Black Formatter
  - GitLens
  - Docker

### Debugging
```bash
# Debug API server
make debug-api

# Debug with breakpoints
python -m debugpy --listen 5678 --wait-for-client server/main.py

# View container logs
container logs nv-api --follow
```

### Performance Profiling
```bash
# Profile API performance
make profile-api

# Memory usage analysis
make profile-memory

# Redis performance testing
make benchmark-redis
```

## 🎯 Development Guidelines

### Code Standards
- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use ESLint + Prettier
- **Git**: Conventional commits (feat:, fix:, docs:)
- **Testing**: Minimum 80% code coverage

### Branch Strategy
```bash
# Feature development
git checkout -b feature/spec-xxx-description
git commit -m "feat: implement SPEC-XXX feature"
git push origin feature/spec-xxx-description

# Create pull request with:
# - Clear description
# - Test coverage
# - Documentation updates
```

### SPEC Implementation Process
1. **Read SPEC**: Understand requirements in `specs/`
2. **Create Branch**: `feature/spec-xxx-name`
3. **Implement**: Follow TDD approach
4. **Test**: Comprehensive test coverage
5. **Document**: Update relevant docs
6. **Review**: Submit PR for review

## 🚨 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check port usage
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # API

# Kill processes if needed
kill -9 <PID>
```

#### Container Issues
```bash
# Reset containers
make containers-reset

# Clean container cache
container system prune -a

# Rebuild containers
make containers-rebuild
```

#### Database Connection Issues
```bash
# Check database status
./scripts/nv-db-status.sh

# Reset database
make db-reset

# Check logs
container logs nv-db
```

### Getting Help
- **Documentation**: Check `docs/` directory
- **Issues**: Create GitHub issue with logs
- **Discussions**: Use GitHub Discussions
- **Slack**: Internal team channel

## 📊 Development Metrics

### Performance Targets (Local Dev)
- **API Startup**: < 5 seconds
- **Test Suite**: < 30 seconds
- **Database Migration**: < 10 seconds
- **Container Startup**: < 15 seconds

### Quality Gates
- **Test Coverage**: > 80%
- **Type Coverage**: > 90%
- **Security Scan**: No high/critical issues
- **Performance**: No regressions

## 🎯 Next Steps

After setup completion:
1. **Explore Codebase**: Start with `server/main.py`
2. **Run Test Suite**: Ensure everything works
3. **Pick a SPEC**: Choose from `SPEC_AUDIT_2024.md`
4. **Join Community**: GitHub Discussions
5. **Contribute**: Submit your first PR

## 📚 Related Documentation

- [API Documentation](../api/README.md)
- [Testing Guide](../testing/README.md)
- [Architecture Overview](../architecture/README.md)
- [SPEC Process](../specs/README.md)

---

**Setup Time**: 5 minutes | **Difficulty**: Beginner | **Support**: Full documentation
