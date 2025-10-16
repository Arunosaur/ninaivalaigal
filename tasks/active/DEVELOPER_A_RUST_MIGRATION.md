# Developer A - Rust Migration (Week 1-2)

**Date**: October 16-25, 2025
**Mission**: Migrate Memory Service + Graph/AI Service to Rust
**Why You**: Already mastered Rust with GraphOps today!
**Time**: 10-12 hours/day for 2 weeks

---

## 🎯 Your Mission

**Create 2 high-performance Rust microservices:**
1. **Memory Service** (Week 1) - Memory CRUD, tokenization, retrieval
2. **Graph/AI Service** (Week 2) - Graph intelligence + GraphOps integration

**Goal**: 50-90% latency reduction per SPEC-099 targets

---

## 📅 Week 1: Memory Service (Rust)

### Day 1 (Oct 16) - Architecture & Setup

**Morning (4 hours)**:

1. **Review Python memory code**:
```bash
cd server/routers
cat memory.py | head -100
cat memory_substrate.py | head -100

# Identify key operations:
# - POST /memory/remember
# - GET /memory/recall
# - GET /memory/memories
# - DELETE /memory/memories/{id}
```

2. **Design Rust architecture**:
```
rust-services/
└── memory-service/
    ├── Cargo.toml
    ├── src/
    │   ├── main.rs          # HTTP server (Axum/Actix)
    │   ├── memory.rs        # Memory CRUD logic
    │   ├── storage.rs       # PostgreSQL integration
    │   ├── cache.rs         # Redis integration
    │   └── models.rs        # Data structures
    └── Dockerfile
```

3. **Create Cargo project**:
```bash
cd rust-services
cargo new memory-service --bin
cd memory-service
```

**Afternoon (6 hours)**:

4. **Add dependencies** (`Cargo.toml`):
```toml
[dependencies]
tokio = { version = "1.35", features = ["full"] }
axum = "0.7"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
sqlx = { version = "0.7", features = ["postgres", "runtime-tokio-native-tls"] }
redis = { version = "0.24", features = ["tokio-comp"] }
uuid = { version = "1.6", features = ["serde", "v4"] }
chrono = { version = "0.4", features = ["serde"] }
tower = "0.4"
tower-http = { version = "0.5", features = ["cors", "trace"] }
tracing = "0.1"
tracing-subscriber = "0.3"
```

5. **Create basic HTTP server** (`src/main.rs`):
```rust
use axum::{
    routing::{get, post, delete},
    Router, Json,
    extract::{Path, State},
    http::StatusCode,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/health", get(health))
        .route("/memory/remember", post(remember))
        .route("/memory/recall", get(recall))
        .route("/memory/memories", get(list_memories))
        .route("/memory/memories/:id", delete(delete_memory));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8001")
        .await
        .unwrap();

    println!("Memory Service listening on :8001");
    axum::serve(listener, app).await.unwrap();
}

async fn health() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "healthy",
        "service": "memory-service",
        "language": "rust"
    }))
}
```

6. **Test basic server**:
```bash
cargo run
# In another terminal:
curl http://localhost:8001/health
```

**End of Day 1 Deliverable**: Basic Rust HTTP server running

---

### Day 2 (Oct 17) - PostgreSQL Integration

**Morning (4 hours)**:

1. **Create memory models** (`src/models.rs`):
```rust
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;
use chrono::{DateTime, Utc};

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Memory {
    pub id: Uuid,
    pub user_id: Uuid,
    pub content: String,
    pub context_id: Option<Uuid>,
    pub metadata: serde_json::Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateMemoryRequest {
    pub content: String,
    pub context_id: Option<Uuid>,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct RecallRequest {
    pub query: String,
    pub limit: Option<i32>,
}
```

2. **Create database layer** (`src/storage.rs`):
```rust
use sqlx::{PgPool, Error};
use uuid::Uuid;
use crate::models::{Memory, CreateMemoryRequest};

pub struct MemoryStorage {
    pool: PgPool,
}

impl MemoryStorage {
    pub async fn new(database_url: &str) -> Result<Self, Error> {
        let pool = PgPool::connect(database_url).await?;
        Ok(Self { pool })
    }

    pub async fn create_memory(
        &self,
        user_id: Uuid,
        req: CreateMemoryRequest,
    ) -> Result<Memory, Error> {
        let memory = sqlx::query_as::<_, Memory>(
            r#"
            INSERT INTO memories (id, user_id, content, context_id, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(&req.content)
        .bind(req.context_id)
        .bind(req.metadata.unwrap_or(serde_json::json!({})))
        .fetch_one(&self.pool)
        .await?;

        Ok(memory)
    }

    pub async fn get_memories(&self, user_id: Uuid) -> Result<Vec<Memory>, Error> {
        let memories = sqlx::query_as::<_, Memory>(
            "SELECT * FROM memories WHERE user_id = $1 ORDER BY created_at DESC"
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await?;

        Ok(memories)
    }

    pub async fn delete_memory(&self, id: Uuid, user_id: Uuid) -> Result<(), Error> {
        sqlx::query("DELETE FROM memories WHERE id = $1 AND user_id = $2")
            .bind(id)
            .bind(user_id)
            .execute(&self.pool)
            .await?;

        Ok(())
    }
}
```

**Afternoon (6 hours)**:

3. **Implement memory endpoints** (`src/main.rs`):
```rust
async fn remember(
    State(storage): State<Arc<MemoryStorage>>,
    Json(req): Json<CreateMemoryRequest>,
) -> Result<Json<Memory>, StatusCode> {
    // TODO: Get user_id from JWT token
    let user_id = Uuid::new_v4(); // Temporary

    match storage.create_memory(user_id, req).await {
        Ok(memory) => Ok(Json(memory)),
        Err(e) => {
            eprintln!("Error creating memory: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn list_memories(
    State(storage): State<Arc<MemoryStorage>>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let user_id = Uuid::new_v4(); // Temporary

    match storage.get_memories(user_id).await {
        Ok(memories) => Ok(Json(memories)),
        Err(e) => {
            eprintln!("Error fetching memories: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}
```

4. **Test database operations**:
```bash
# Start PostgreSQL if not running
make stack-up

# Set database URL
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ninaivalaigal  # pragma: allowlist secret

# Run service
cargo run

# Test endpoints
curl -X POST http://localhost:8001/memory/remember \
  -H "Content-Type: application/json" \
  -d '{"content": "Test memory from Rust!"}'

curl http://localhost:8001/memory/memories
```

**End of Day 2 Deliverable**: PostgreSQL integration working

---

### Day 3 (Oct 18) - Redis Caching

**Morning (4 hours)**:

1. **Create Redis cache layer** (`src/cache.rs`):
```rust
use redis::{Client, Commands, RedisError};
use uuid::Uuid;
use crate::models::Memory;

pub struct MemoryCache {
    client: Client,
}

impl MemoryCache {
    pub fn new(redis_url: &str) -> Result<Self, RedisError> {
        let client = Client::open(redis_url)?;
        Ok(Self { client })
    }

    pub fn cache_memory(&self, memory: &Memory) -> Result<(), RedisError> {
        let mut conn = self.client.get_connection()?;
        let key = format!("memory:{}", memory.id);
        let value = serde_json::to_string(memory).unwrap();
        conn.set_ex(key, value, 3600)?; // 1 hour TTL
        Ok(())
    }

    pub fn get_memory(&self, id: Uuid) -> Result<Option<Memory>, RedisError> {
        let mut conn = self.client.get_connection()?;
        let key = format!("memory:{}", id);
        let value: Option<String> = conn.get(key)?;

        match value {
            Some(v) => Ok(serde_json::from_str(&v).ok()),
            None => Ok(None),
        }
    }

    pub fn invalidate_user_memories(&self, user_id: Uuid) -> Result<(), RedisError> {
        let mut conn = self.client.get_connection()?;
        let pattern = format!("memories:user:{}:*", user_id);
        // TODO: Implement key pattern deletion
        Ok(())
    }
}
```

2. **Integrate cache into endpoints**:
```rust
// Check cache first, then database
async fn list_memories(
    State(app_state): State<Arc<AppState>>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let user_id = Uuid::new_v4(); // Temporary

    // Try cache first (implement user-level caching)
    match app_state.storage.get_memories(user_id).await {
        Ok(memories) => Ok(Json(memories)),
        Err(e) => {
            eprintln!("Error: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}
```

**Afternoon (6 hours)**:

3. **Performance optimization**:
- Add connection pooling
- Implement batch operations
- Add metrics collection

4. **Load testing**:
```bash
# Install hey
brew install hey

# Test memory creation
hey -n 1000 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"content":"Load test memory"}' \
  http://localhost:8001/memory/remember

# Test memory retrieval
hey -n 10000 -c 50 \
  http://localhost:8001/memory/memories
```

**End of Day 3 Deliverable**: Redis caching with <30ms P95 latency

---

### Day 4 (Oct 19) - Authentication & gRPC

**Morning (4 hours)**:

1. **JWT authentication**:
```rust
use jsonwebtoken::{decode, DecodingKey, Validation};

#[derive(Debug, Deserialize)]
struct Claims {
    sub: String,  // user_id
    exp: usize,
}

async fn extract_user_id(headers: &HeaderMap) -> Result<Uuid, StatusCode> {
    let token = headers
        .get("Authorization")
        .and_then(|v| v.to_str().ok())
        .and_then(|s| s.strip_prefix("Bearer "))
        .ok_or(StatusCode::UNAUTHORIZED)?;

    let key = DecodingKey::from_secret(b"your-secret");
    let token_data = decode::<Claims>(token, &key, &Validation::default())
        .map_err(|_| StatusCode::UNAUTHORIZED)?;

    Uuid::parse_str(&token_data.claims.sub)
        .map_err(|_| StatusCode::UNAUTHORIZED)
}
```

2. **Add to all endpoints**:
```rust
async fn remember(
    headers: HeaderMap,
    State(storage): State<Arc<MemoryStorage>>,
    Json(req): Json<CreateMemoryRequest>,
) -> Result<Json<Memory>, StatusCode> {
    let user_id = extract_user_id(&headers).await?;
    // ... rest of implementation
}
```

**Afternoon (6 hours)**:

3. **Optional: Add gRPC interface**:
```proto
// proto/memory.proto
syntax = "proto3";

service MemoryService {
    rpc CreateMemory(CreateMemoryRequest) returns (Memory);
    rpc GetMemories(GetMemoriesRequest) returns (MemoriesResponse);
    rpc DeleteMemory(DeleteMemoryRequest) returns (Empty);
}
```

**End of Day 4 Deliverable**: Authenticated Memory Service

---

### Day 5 (Oct 20) - Containerization

**Morning (4 hours)**:

1. **Create Dockerfile**:
```dockerfile
# rust-services/memory-service/Dockerfile
FROM rust:1.75 as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/memory-service /usr/local/bin/memory-service

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["memory-service"]
```

2. **Build container**:
```bash
# Build for ARM64 (Apple Silicon)
docker build -t memory-service:arm64 -f Dockerfile .

# Transfer to Apple Container CLI
docker save memory-service:arm64 -o /tmp/memory-service.tar
container image load --input /tmp/memory-service.tar
rm /tmp/memory-service.tar
```

**Afternoon (6 hours)**:

3. **Integration testing with other services**:
```bash
# Start full stack
docker-compose up -d postgres redis core-api
container run -d --name memory-service \
  -p 8001:8001 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/ninaivalaigal \  # pragma: allowlist secret
  -e REDIS_URL=redis://host.docker.internal:6379 \
  memory-service:arm64

# Test end-to-end
curl http://localhost:8001/health
```

4. **Write tests**:
```bash
cd rust-services/memory-service
cargo test
```

**End of Day 5 Deliverable**: Containerized Memory Service ready for production

---

## 📅 Week 2: Graph/AI Service (Rust)

### Day 1-2 (Oct 21-22) - GraphOps Integration

**Key tasks**:
1. Review GraphOps gRPC client from today's work
2. Create Rust Graph/AI service shell
3. Integrate GraphOps gRPC calls
4. Implement graph intelligence endpoints

### Day 3-4 (Oct 23-24) - AI Features

**Key tasks**:
1. Port insight generation logic
2. Port feedback processing
3. Add relevance scoring
4. Redis caching for AI results

### Day 5 (Oct 25) - Containerization

**Key tasks**:
1. Create Dockerfile
2. Build and test container
3. Integration testing with Memory Service
4. Performance benchmarking

---

## ✅ Success Criteria

**Week 1 (Memory Service)**:
- [ ] Rust HTTP server running
- [ ] PostgreSQL CRUD operations working
- [ ] Redis caching with <30ms P95
- [ ] JWT authentication integrated
- [ ] Container builds successfully
- [ ] Passes integration tests
- [ ] **Target**: 50-90% faster than Python version

**Week 2 (Graph/AI Service)**:
- [ ] GraphOps gRPC integration working
- [ ] AI endpoints functional
- [ ] Container builds successfully
- [ ] All services communicate properly
- [ ] Load tests show performance gains

---

## 🆘 If You Get Stuck

### Rust Compilation Errors
1. Read the error message carefully (Rust errors are detailed!)
2. Check Cargo.toml dependencies
3. Ask Developer C for help with architecture

### PostgreSQL Connection Issues
1. Verify DATABASE_URL format
2. Check PostgreSQL is running
3. Test with `psql` directly

### Performance Not Meeting Targets
1. Add more Redis caching
2. Use connection pooling
3. Profile with `cargo flamegraph`

---

**Focus**: You already proved you can write production Rust with GraphOps. Now apply that skill to Memory + Graph/AI services!

**Philosophy**: Fast, safe, concurrent - Rust's sweet spot

**Goal**: 50-90% latency reduction vs Python!
