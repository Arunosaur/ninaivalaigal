# Memory Service Tests

**US#93/US#95:** Memory Router Rationalization - SPEC-131

## Test Structure

### Unit Tests
Unit tests are located in the source files using `#[cfg(test)]` modules:
- `src/services/injection_service.rs` - Injection service logic tests
- Additional unit tests can be added to respective modules

### Integration Tests
Integration tests are in the `tests/` directory:
- `injection_api_tests.rs` - Injection API endpoint tests
- `queue_api_tests.rs` - Queue API endpoint tests

### Performance Tests
- `benches/injection_benchmark.rs` - Criterion benchmarks for injection operations
- `scripts/run_performance_tests.sh` - Performance test script

## Running Tests

### Unit Tests
```bash
# Run all unit tests
cargo test

# Run specific test module
cargo test services::injection_service::tests

# Run with output
cargo test -- --nocapture
```

### Integration Tests
```bash
# Run integration tests (requires running service)
cargo test --test injection_api_tests
cargo test --test queue_api_tests

# Run all integration tests
cargo test --test '*'
```

### Performance Benchmarks
```bash
# Run Criterion benchmarks
cargo bench --bench injection_benchmark

# Run performance test script
./scripts/run_performance_tests.sh
```

## Test Requirements

### For Unit Tests
- No external dependencies required
- Run with: `cargo test`

### For Integration Tests
- Running memory service (port 8000 by default)
- PostgreSQL database connection
- Redis connection
- Valid JWT token (set `TEST_JWT_TOKEN` environment variable)

### For Performance Tests
- All integration test requirements
- Service running and accessible
- Test data in database

## Environment Variables

```bash
# Service URL
export TEST_API_BASE_URL="http://localhost:8000"

# JWT Token for authenticated requests
export TEST_JWT_TOKEN="your-jwt-token-here"

# Bulk test size
export BULK_SIZE=1000
```

## Performance Targets (SPEC-131)

### Injection API
- **Bulk Injection:** >1000 memories/sec
- **Analysis:** <100ms for typical context

### Queue API
- **Enqueue:** P99 < 10ms
- **Status Check:** <50ms
- **Stats:** <100ms

## Test Coverage

### Current Coverage
- ✅ Unit tests for injection service logic
- ✅ Integration test structure (placeholders)
- ✅ Performance benchmark structure

### TODO
- [ ] Full integration test implementation
- [ ] End-to-end test scenarios
- [ ] Load testing with concurrent requests
- [ ] Error case testing
- [ ] Authentication/authorization tests
