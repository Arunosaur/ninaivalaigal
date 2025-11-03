# Memory Service Integration Tests

Comprehensive integration tests for the Memory Service (Rust).

## Test Files

1. **`integration_test.rs`** - Rust integration tests using reqwest
2. **`test_helpers.rs`** - Test utilities and helper functions
3. **`../tests/integration/test_memory_service_rust.py`** - Python integration tests

## Prerequisites

### Services Required
- Memory Service running on port 8000 (or configured port)
- PostgreSQL database accessible via PgBouncer
- Redis running on port 6379
- Core API running (for JWT token generation)

### Environment Variables
```bash
export DATABASE_URL="postgresql://nina:password@localhost:6432/ninaivalaigal_dev"
export REDIS_URL="redis://localhost:6379/0"
export NINAIVALAIGAL_JWT_SECRET="your-jwt-secret"
```

## Running Tests

### Rust Integration Tests

```bash
# Run all integration tests (requires running service)
cd services/memory-service-rust
cargo test --test integration_test -- --ignored --nocapture

# Run specific test
cargo test --test integration_test test_health_check -- --ignored --nocapture

# Run all tests (including ignored ones)
cargo test -- --ignored
```

**Note**: Tests are marked with `#[ignore]` because they require the service to be running. Use `--ignored` flag to run them.

### Python Integration Tests

```bash
# Activate conda environment (dependencies already installed)
conda activate nina

# Run all tests
pytest tests/integration/test_memory_service_rust.py -v

# Or use conda run
conda run -n nina pytest tests/integration/test_memory_service_rust.py -v

# Run specific test class
pytest tests/integration/test_memory_service_rust.py::TestHealthAndMetrics -v

# Run with output
pytest tests/integration/test_memory_service_rust.py -v -s
```

## Test Coverage

### ✅ Health & Metrics
- Health check endpoint
- Metrics endpoint
- Service status reporting

### ✅ Authentication
- JWT token validation
- Missing authorization header
- Invalid token rejection
- Authentication requirement for protected endpoints

### ✅ CRUD Operations
- List memories (requires auth)
- Create memory (requires auth)
- Get memory by ID (requires auth)
- Error handling for not found

### ✅ Error Handling
- Invalid JSON requests
- Missing required fields
- Unauthorized access attempts

### ⏳ Cache Behavior
- Cache-aside pattern (when implemented)
- Cache hit/miss metrics
- Cache invalidation

### ⏳ Performance
- Response time checks
- Load testing capabilities

## Getting Test JWT Tokens

### Option 1: Use Core API

```bash
# Login and get token
TOKEN=$(curl -s http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}' \
  | jq -r .access_token)

# Use token in tests
export TEST_JWT_TOKEN=$TOKEN
```

### Option 2: Generate Test Token Programmatically

See `test_helpers.rs` for utilities to generate test tokens.

## Test Structure

### Rust Tests

```rust
#[tokio::test]
#[ignore] // Requires running service
async fn test_health_check() {
    // Test implementation
}
```

### Python Tests

```python
class TestHealthAndMetrics:
    def test_health_check(self, client_no_auth):
        # Test implementation
        pass
```

## Continuous Integration

For CI/CD pipelines:

1. Start test infrastructure (PostgreSQL, Redis)
2. Build and start Memory Service
3. Run Rust tests: `cargo test --test integration_test -- --ignored`
4. Run Python tests: `pytest tests/integration/test_memory_service_rust.py`

## Troubleshooting

### "Connection refused"
- Ensure Memory Service is running: `cargo run` or `./nv-memory-service-start.sh`
- Check port: default is 8000 (external 13393)

### "Authentication failed"
- Check `NINAIVALAIGAL_JWT_SECRET` matches Core API
- Ensure token is valid and not expired
- Verify Core API is running for token generation

### "Database connection failed"
- Verify PostgreSQL is accessible via PgBouncer (port 6432)
- Check `DATABASE_URL` environment variable
- Ensure database exists: `ninaivalaigal_dev`

### "Redis connection failed"
- Verify Redis is running: `redis-cli ping`
- Check `REDIS_URL` environment variable
- Ensure Redis is accessible on port 6379

## Next Steps

1. **Complete CRUD Implementation**: Once memory operations are fully implemented, update tests to verify actual database operations
2. **Cache Testing**: When Redis caching is implemented, add comprehensive cache behavior tests
3. **Performance Tests**: Add load testing with wrk or similar tools
4. **E2E Tests**: Create end-to-end tests that test full user workflows

## References

- [Memory Service README](../README.md)
- [Axum Testing Guide](https://docs.rs/axum/latest/axum/#testing)
- [Rust Testing Book](https://doc.rust-lang.org/book/ch11-00-testing.html)
