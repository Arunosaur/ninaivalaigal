# 📝 ninaivalaigal Development Setup Guide

## 🚀 Quick Start

### Prerequisites
- **Apple Container CLI** (for ARM64 Mac development)
- **conda** environment manager
- **Python 3.11+**
- **Git**

### 1. Environment Setup
```bash
# Clone the repository
git clone https://github.com/your-org/ninaivalaigal.git
cd ninaivalaigal

# Activate conda environment
conda activate nina

# Install dependencies
pip install -r requirements.txt
```

### 2. Stack Startup
```bash
# Start the complete intelligence stack
make nina-stack-up

# Verify stack is healthy
make stack-status
```

### 3. Verify Installation
```bash
# Check API health
curl http://localhost:13370/health

# Access Swagger UI
open http://localhost:13370/docs

# Run test suite
./tests/curl_tests.sh
```

## 🏗️ Architecture Overview

### Stack Components
- **nina-intelligence-db**: PostgreSQL 15 + pgvector (port 5432)
- **nina-intelligence-cache**: Redis 7-alpine (port 6379)  
- **nv-api**: FastAPI application (port 13370)
- **nv-ui**: Frontend interface (port 8080)

### Key Directories
```
ninaivalaigal/
├── server/                 # FastAPI backend
│   ├── main.py            # Application entry point
│   ├── signup_api.py      # Authentication endpoints
│   └── ...
├── tests/                 # Test suite
│   ├── auth_test_plan.md  # Comprehensive test plan
│   ├── api_tests.http     # HTTP client tests
│   └── curl_tests.sh      # Automated curl tests
├── docs/                  # Documentation
└── Makefile              # Development commands
```

## 🧪 Testing Workflow

### Manual Testing
```bash
# 1. Start the stack
make nina-stack-up

# 2. Run comprehensive test suite
./tests/curl_tests.sh

# 3. Use HTTP client for interactive testing
# Open tests/api_tests.http in VS Code with REST Client extension
```

### Automated Testing
```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=server --cov-report=html

# Generate coverage dashboard
make coverage-dashboard
```

### Auth Flow Testing
```bash
# Test login endpoint
curl -X POST http://localhost:13370/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Test signup endpoint
curl -X POST http://localhost:13370/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","password":"strongpass123","full_name":"Test User"}'
```

## 🔧 Development Commands

### Stack Management
```bash
# Start intelligence stack
make nina-stack-up

# Stop stack
make nina-stack-down

# Check status
make stack-status

# View logs
container logs nv-api -n 50
container logs nina-intelligence-db -n 50
```

### Code Quality
```bash
# Run linting
make lint

# Format code
make format

# Type checking
make type-check

# Security scan
make security-scan
```

### Database Operations
```bash
# Connect to database
container exec -it nina-intelligence-db psql -U nina -d ninaivalaigal

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Container Not Starting
```bash
# Check container status
container list

# View detailed logs
container logs nv-api

# Restart stack
make nina-stack-down && make nina-stack-up
```

#### 2. Auth Endpoints Not Found (404)
```bash
# Verify routes are registered
curl http://localhost:13370/openapi.json | jq '.paths | keys | .[] | select(contains("auth"))'

# Check for import errors in logs
container logs nv-api | grep -i error

# Rebuild API container
container build --no-cache -t nina-api:arm64 -f Dockerfile.api .
make nina-stack-up
```

#### 3. Database Connection Issues
```bash
# Check database is running
container inspect nina-intelligence-db

# Test connection
curl http://localhost:13370/health

# Check environment variables
container exec nv-api env | grep DATABASE
```

#### 4. Redis Connection Issues
```bash
# Check Redis is running
container inspect nina-intelligence-cache

# Test Redis connection
container exec nina-intelligence-cache redis-cli ping

# Check Redis logs
container logs nina-intelligence-cache
```

### Performance Issues
```bash
# Monitor resource usage
container stats

# Check API response times
time curl http://localhost:13370/health

# Profile database queries
container exec nina-intelligence-db psql -U nina -d ninaivalaigal -c "SELECT * FROM pg_stat_activity;"
```

## 🔒 Security Considerations

### Development Environment
- JWT secret is set to test value for development
- Database uses development credentials
- CORS is enabled for localhost
- Rate limiting is disabled for testing

### Production Checklist
- [ ] Change JWT secret to secure random value
- [ ] Use production database credentials
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up HTTPS/TLS
- [ ] Configure proper logging
- [ ] Set up monitoring and alerting

## 📊 Code Coverage

### Current Status
- **Baseline Coverage**: 10%
- **Target Coverage**: 80%
- **Critical Modules**: auth (100%), memory (90%), RBAC (100%)

### Coverage Commands
```bash
# Generate coverage report
make coverage-dashboard

# View HTML report
open htmlcov/index.html

# Run specific module tests
pytest tests/auth/ --cov=server/signup_api --cov-report=term-missing
```

## 🚀 Deployment

### Local Development
```bash
# Standard development stack
make nina-stack-up
```

### Staging Environment
```bash
# Build production images
make build-all

# Deploy to staging
make deploy-staging
```

### Production Deployment
```bash
# Deploy to production
make deploy-production

# Monitor deployment
make monitor-production
```

## 📚 Additional Resources

### API Documentation
- **Swagger UI**: http://localhost:13370/docs
- **OpenAPI Schema**: http://localhost:13370/openapi.json
- **Test Plan**: [tests/auth_test_plan.md](../tests/auth_test_plan.md)

### Development Tools
- **HTTP Client Tests**: [tests/api_tests.http](../tests/api_tests.http)
- **Automated Tests**: [tests/curl_tests.sh](../tests/curl_tests.sh)
- **Coverage Dashboard**: `make coverage-dashboard`

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL + pgvector](https://github.com/pgvector/pgvector)
- [Redis Documentation](https://redis.io/documentation)
- [Apple Container CLI](https://developer.apple.com/documentation/container-cli)

## 🤝 Contributing

### Development Workflow
1. Create feature branch from `main`
2. Make changes and add tests
3. Run test suite: `./tests/curl_tests.sh`
4. Ensure coverage targets are met
5. Submit pull request with test results

### Code Standards
- Follow PEP 8 for Python code
- Add type hints for all functions
- Include docstrings for public APIs
- Write tests for new functionality
- Update documentation for API changes

---

**Need Help?** 
- Check the troubleshooting section above
- Review test outputs for specific error messages
- Consult the comprehensive test plan for expected behaviors
