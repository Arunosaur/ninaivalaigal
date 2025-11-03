# Memory Service (Rust)

High-performance memory CRUD operations service built with Rust, Axum, SQLx, and Redis.

## 🎯 Story Coverage

This scaffolding supports the following Taiga stories:
- **#42**: Rust HTTP server running
- **#43**: PostgreSQL CRUD operations working
- **#44**: Redis caching with <30ms P95
- **#45**: JWT authentication integrated
- **#46**: Container builds successfully
- **#47**: Passes integration tests
- **#48**: Performance benchmarking vs Python

---

## 🚀 Quick Start

### Prerequisites

1. **Rust** (1.75 or later)
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup update
```

2. **Running Infrastructure**
- PostgreSQL via PgBouncer (port 6432)
- Redis (port 6379)

### Local Development

1. **Clone and setup**
```bash
cd services/memory-service-rust
cp .env.example .env
```

2. **Update `.env`** with actual values:
```bash
DATABASE_URL=postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev
REDIS_URL=redis://localhost:6379/0
NINAIVALAIGAL_JWT_SECRET=<copy from Core API>
RUST_LOG=info,memory_service=debug
```

3. **Build and run**
```bash
# Development mode (with hot reload)
cargo watch -x run

# Or standard run
cargo run

# Release build
cargo build --release
cargo run --release
```

4. **Test the service**
```bash
# Health check
curl http://localhost:13393/health

# Metrics
curl http://localhost:13393/metrics
```

---

## 🏗️ Architecture

### Tech Stack
- **Web Framework**: Axum 0.7 (modern, performant, tokio-native)
- **Database**: SQLx 0.7 + PostgreSQL (compile-time checked queries)
- **Cache**: Redis (async client with connection pooling)
- **Auth**: JWT validation (matches Core API)
- **Logging**: tracing + tracing-subscriber (structured JSON logs)
- **Metrics**: Prometheus

### Port Allocation
- **Internal**: 8000 (container port)
- **External (Apple Dev)**: 13393
- **External (Docker)**: 13383
- **External (Colima)**: 13373

### Service Dependencies
```
Memory Service
├── PgBouncer (6432) → PostgreSQL (5432)
└── Redis (6379)
```

---

## 📁 Project Structure

```
src/
├── main.rs           # Server setup, routing, health/metrics endpoints
├── config.rs         # Environment configuration
├── error.rs          # Unified error handling
├── auth.rs           # JWT validation middleware
├── db.rs             # Database connection pooling
├── redis_client.rs   # Redis connection + cache-aside helpers
├── memory.rs         # Memory CRUD operations (stub)
└── metrics.rs        # Prometheus metrics
```

---

## 🔐 Authentication

JWT tokens from Core API are validated using the same secret.

**Token format** (from Core API `/auth/login`):
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Request example**:
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:13393/api/v1/memories
```

**JWT Claims** (decoded):
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1234567890,
  "iat": 1234567890,
  "user_id": "user-uuid"
}
```

---

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_parse_user_id
```

### Integration Tests (requires running services)
```bash
# Run ignored tests (need DB + Redis)
cargo test -- --ignored
```

### Manual API Testing
```bash
# 1. Get JWT token from Core API
TOKEN=$(curl -s http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}' \
  | jq -r .access_token)

# 2. List memories
curl http://localhost:13393/api/v1/memories \
  -H "Authorization: Bearer $TOKEN"

# 3. Create memory
curl -X POST http://localhost:13393/api/v1/memories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Test memory","metadata":{"tag":"test"}}'
```

---

## 🐳 Docker

### Build
```bash
# Build the image
docker build -t memory-service:latest .

# Or use Apple Container CLI (ARM64)
container build -t memory-service:latest .
```

### Run
```bash
# Using Docker
docker run -p 13393:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@host.docker.internal:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  -e NINAIVALAIGAL_JWT_SECRET="your-secret" \
  memory-service:latest

# Using Apple Container CLI
container run -p 13393:8000 \
  -e DATABASE_URL="postgresql://nina:dev_password_change_in_production@host.containers.internal:6432/ninaivalaigal_dev" \
  -e REDIS_URL="redis://host.containers.internal:6379" \
  -e NINAIVALAIGAL_JWT_SECRET="your-secret" \
  memory-service:latest
```

### Health Check
```bash
curl http://localhost:13393/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "memory-service",
  "version": "0.1.0",
  "database": "healthy",
  "redis": "healthy"
}
```

---

## 📊 Performance Targets (#48)

| Metric | Python (Core API) | Rust Target | Status |
|--------|-------------------|-------------|--------|
| Throughput (req/s) | 500-1000 | 5000-10000 | 🚧 TBD |
| Latency P50 | 50-100ms | 5-10ms | 🚧 TBD |
| Latency P95 | 200-500ms | 20-50ms | 🚧 TBD |
| Memory usage | 200-400MB | 50-100MB | 🚧 TBD |

**Benchmark with**:
```bash
# Install wrk
brew install wrk

# Run benchmark
wrk -t4 -c100 -d30s \
  -H "Authorization: Bearer $TOKEN" \
  http://localhost:13393/api/v1/memories
```

---

## 📝 Next Steps for Developer A

### Phase 1: Complete #42 (Server Running)
- ✅ Server scaffolding complete
- ✅ Health endpoint working
- ✅ Metrics endpoint working
- ✅ CORS configured
- 🚧 Update Taiga status to "Done"

### Phase 2: #45 (JWT Auth)
- ✅ JWT middleware implemented
- 🚧 Test with real tokens from Core API
- 🚧 Add to protected routes

### Phase 3: #43 (PostgreSQL CRUD)
- 🚧 Create `memories` table schema
- 🚧 Implement `list_memories` query
- 🚧 Implement `create_memory` insert
- 🚧 Implement `get_memory` select
- 🚧 Implement `update_memory` update
- 🚧 Implement `delete_memory` delete

### Phase 4: #44 (Redis Caching)
- ✅ Redis connection manager ready
- ✅ Cache-aside helper function ready
- 🚧 Implement caching in `get_memory`
- 🚧 Measure P95 latency
- 🚧 Tune TTL values

### Phase 5: #38 (Integration Tests)
- 🚧 Test full auth flow
- 🚧 Test CRUD operations
- 🚧 Test cache behavior
- 🚧 Test error handling

### Phase 6: #46-47 (Container & E2E)
- 🚧 Test container build
- 🚧 Test container run
- 🚧 Run full integration suite

### Phase 7: #48 (Performance)
- 🚧 Run benchmarks vs Python
- 🚧 Document results
- 🚧 Optimize hot paths

---

## 🔍 Troubleshooting

### "Failed to connect to database"
```bash
# Check PgBouncer is running
lsof -i:6432

# Test connection
psql -h localhost -p 6432 -U nina -d ninaivalaigal_dev
```

### "Failed to connect to Redis"
```bash
# Check Redis is running
redis-cli ping

# Or with port
redis-cli -p 6379 ping
```

### "JWT validation failed"
- Ensure `NINAIVALAIGAL_JWT_SECRET` matches Core API exactly
- Check token hasn't expired (`exp` claim)
- Verify `Authorization: Bearer <token>` header format

---

## 📚 Resources

- [Axum Documentation](https://docs.rs/axum/latest/axum/)
- [SQLx Documentation](https://docs.rs/sqlx/latest/sqlx/)
- [Redis-rs Documentation](https://docs.rs/redis/latest/redis/)
- [Tokio Documentation](https://tokio.rs/)
- [JWT RFC 7519](https://datatracker.ietf.org/doc/html/rfc7519)

---

## 🎯 Success Criteria

✅ Server starts and listens on port 8000
✅ Health check returns 200 OK
✅ Metrics endpoint returns Prometheus format
✅ JWT tokens are validated correctly
⏳ CRUD operations work against PostgreSQL
⏳ Redis caching achieves <30ms P95
⏳ Container builds and runs successfully
⏳ Integration tests pass
⏳ Performance 50-90% better than Python

---

**Ready to go! Start with `cargo run` and check http://localhost:13393/health** 🚀
