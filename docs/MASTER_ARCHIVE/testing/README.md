# 🧪 Testing Guide

## 🎯 Testing Overview

Comprehensive testing strategy covering unit tests, integration tests, security tests, and performance benchmarks.

## 🚀 Quick Testing

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test suites
make test-auth
make test-memory
make test-redis
make test-security
```

## 📋 Test Categories

### Unit Tests
- **Location**: `tests/unit/`
- **Coverage**: 80%+ required
- **Focus**: Individual functions and classes
- **Speed**: < 1 second per test

### Integration Tests
- **Location**: `tests/integration/`
- **Coverage**: Critical user flows
- **Focus**: Component interactions
- **Speed**: < 10 seconds per test

### Security Tests
- **Location**: `tests/security/`
- **Coverage**: Authentication, authorization, input validation
- **Focus**: Security vulnerabilities
- **Tools**: Bandit, safety, custom security tests

### Performance Tests
- **Location**: `tests/performance/`
- **Coverage**: API endpoints, database queries, Redis operations
- **Focus**: Response times and throughput
- **Targets**: P95 < 200ms API, < 1ms Redis

## 🎯 Test Requirements

### New Code Requirements
- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All user-facing features
- **Security Tests**: All authentication/authorization code
- **Performance Tests**: All API endpoints

### Test Quality Standards
- **Descriptive Names**: Clear test purpose
- **Isolated**: No dependencies between tests
- **Deterministic**: Consistent results
- **Fast**: Quick feedback loop

## 📊 Current Test Status

### Test Coverage (by SPEC)
- **SPEC-001-012**: 85% coverage (core features)
- **SPEC-031**: 90% coverage (memory relevance)
- **SPEC-033**: 95% coverage (Redis integration)
- **SPEC-052**: 100% coverage (test framework)
- **SPEC-053**: 90% coverage (authentication)

### Performance Benchmarks
- **Memory Retrieval**: 0.15ms average (Redis-cached)
- **API Response**: P95 < 150ms
- **Database Queries**: P95 < 100ms
- **Concurrent Users**: 1000+ validated

## 🔧 Testing Tools

### Python Testing Stack
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **factory_boy**: Test data factories
- **freezegun**: Time mocking

### Security Testing
- **bandit**: Security linting
- **safety**: Dependency vulnerability scanning
- **detect-secrets**: Secret detection
- **Custom**: Authentication/authorization tests

### Performance Testing
- **locust**: Load testing
- **pytest-benchmark**: Performance benchmarking
- **Redis**: Cache performance validation
- **PostgreSQL**: Database performance testing

## 📚 Related Documentation

- [Developer Setup](../development/setup.md)
- [Security Testing](../security/README.md)
- [Performance Benchmarks](performance.md)
- [API Testing](../api/README.md)

---

**Test Coverage**: 85% | **Security**: Comprehensive | **Performance**: Validated
