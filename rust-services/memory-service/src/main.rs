mod api;
mod auth;
mod cache;
mod models;
mod services;
mod storage;
mod telemetry;

use auth::{require_jwt, AuthenticatedUser, JwtVerifier};
use axum::extract::{Extension, Path, State};
use axum::http::StatusCode;
use axum::routing::{delete, get, post};
use axum::{middleware, Json, Router};
use cache::MemoryCache;
use dotenvy::dotenv;
use models::{CreateMemoryRequest, Memory, RecallRequest};
use serde_json::json;
use services::event_stream::EventStream;
use std::env;
use std::net::SocketAddr;
use std::sync::Arc;
use storage::MemoryStorage;
use tracing::{error, info, warn};
use utoipa::OpenApi;
use utoipa_swagger_ui::SwaggerUi;
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    storage: Arc<MemoryStorage>,
    cache: MemoryCache,
    auth: JwtVerifier,
    event_stream: Arc<tokio::sync::Mutex<EventStream>>,
}

impl AppState {
    fn new(
        storage: MemoryStorage,
        cache: MemoryCache,
        auth: JwtVerifier,
        event_stream: EventStream,
    ) -> Self {
        Self {
            storage: Arc::new(storage),
            cache,
            auth,
            event_stream: Arc::new(tokio::sync::Mutex::new(event_stream)),
        }
    }

    fn storage(&self) -> Arc<MemoryStorage> {
        Arc::clone(&self.storage)
    }

    fn cache(&self) -> MemoryCache {
        self.cache.clone()
    }

    fn event_stream(&self) -> Arc<tokio::sync::Mutex<EventStream>> {
        Arc::clone(&self.event_stream)
    }

    fn auth(&self) -> &JwtVerifier {
        &self.auth
    }
}

#[tokio::main]
async fn main() {
    let _ = dotenv();

    // Initialize distributed tracing (Task #84)
    let service_name = env::var("OTEL_SERVICE_NAME")
        .unwrap_or_else(|_| "ninaivalaigal-memory-service".to_string());
    let jaeger_endpoint = env::var("OTEL_EXPORTER_OTLP_ENDPOINT").ok();
    let tracing_enabled = env::var("OTEL_TRACING_ENABLED")
        .unwrap_or_else(|_| "true".to_string())
        .to_lowercase()
        == "true";

    if tracing_enabled {
        if let Err(e) = telemetry::init_tracing(&service_name, jaeger_endpoint.as_deref()) {
            eprintln!("⚠️  Failed to initialize OpenTelemetry tracing: {}", e);
            eprintln!("ℹ️  Falling back to simple tracing");
            telemetry::init_simple_tracing().ok();
        }
    } else {
        telemetry::init_simple_tracing().ok();
    }
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let redis_url = env::var("REDIS_URL").expect("REDIS_URL must be set");

    let cache_ttl_seconds = env::var("MEMORY_CACHE_TTL_SECONDS")
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .filter(|ttl| *ttl > 0)
        .unwrap_or(3600);

    let storage = MemoryStorage::new(&database_url)
        .await
        .expect("failed to initialise MemoryStorage");

    let cache = MemoryCache::new(&redis_url, cache_ttl_seconds)
        .await
        .expect("failed to initialise MemoryCache");

    // Initialize Redis Streams event publisher (US#646: SPEC-099)
    let stream_name = env::var("REDIS_STREAM_NAME")
        .unwrap_or_else(|_| "events:memory".to_string());
    let event_stream = EventStream::new(redis_url.clone(), Some(stream_name));

    let jwt_secret =
        env::var("NINAIVALAIGAL_JWT_SECRET").expect("NINAIVALAIGAL_JWT_SECRET must be set");
    let jwt = JwtVerifier::new(&jwt_secret);

    let state = Arc::new(AppState::new(storage, cache, jwt, event_stream));

    let port: u16 = env::var("PORT")
        .unwrap_or_else(|_| "8000".to_string())
        .parse()
        .expect("PORT must be a valid u16");
    let addr = SocketAddr::from(([0, 0, 0, 0], port));

    // Injection API routes (US#93/US#95: Memory Router Rationalization)
    let injection_routes = Router::new()
        .route("/memory/injection/analyze", post(api::injection::analyze_injection_opportunities))
        .route("/memory/injection/execute", post(api::injection::execute_memory_injection))
        .route("/memory/injection/bulk", post(api::injection::bulk_inject_memories));

    // Queue API routes (US#93/US#95: Memory Router Rationalization)
    let queue_routes = Router::new()
        .route("/queue/tasks", post(api::queue::enqueue_task))
        .route("/queue/jobs/:job_id", get(api::queue::get_job_status))
        .route("/queue/stats", get(api::queue::get_queue_stats))
        .route("/queue/memory/:memory_id/process", post(api::queue::process_memory_async))
        .route("/queue/health", get(api::queue::queue_health));

    let protected = Router::new()
        .route("/memory/remember", post(remember))
        .route("/memory/recall", post(recall))
        .route("/memory/memories", get(list_memories))
        .route("/memory/memories/:id", delete(delete_memory))
        .merge(injection_routes)
        .merge(queue_routes)
        .layer(middleware::from_fn_with_state(
            Arc::clone(&state),
            require_jwt,
        ));

    #[derive(OpenApi)]
    #[openapi(
        paths(
            health,
            remember,
            recall,
            list_memories,
            delete_memory
        ),
        components(
            schemas(Memory, CreateMemoryRequest, RecallRequest)
        ),
        tags(
            (name = "memory-service", description = "Memory CRUD operations with Redis caching")
        ),
        info(
            title = "Memory Service API",
            version = "1.0.0",
            description = "Rust-based memory service for ninaivalaigal platform (SPEC-100 compliant)"
        )
    )]
    struct ApiDoc;

    let app = Router::new()
        .merge(SwaggerUi::new("/docs").url("/api-docs/openapi.json", ApiDoc::openapi()))
        .route("/health", get(health))
        .merge(protected)
        .with_state(state);

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("bind memory-service");

    info!(?addr, "Memory Service listening");
    axum::serve(listener, app)
        .await
        .expect("serve memory-service");

    // Shutdown tracing gracefully
    telemetry::shutdown_tracing();
}

/// Health check endpoint
///
/// Returns the service health status including database and Redis connection information.
#[utoipa::path(
    get,
    path = "/health",
    tag = "health",
    responses(
        (status = 200, description = "Service is healthy", body = serde_json::Value)
    )
)]
async fn health(State(state): State<Arc<AppState>>) -> Json<serde_json::Value> {
    let storage = state.storage();
    let conn_stats = storage.connection_stats();

    Json(json!({
        "status": "healthy",
        "service": "memory-service",
        "language": "rust",
        "database": {
            "connections_active": conn_stats.active,
            "connections_idle": conn_stats.idle,
            "connections_total": conn_stats.size,
            "connections_max": conn_stats.max_connections,
            "connection_mode": "direct_postgresql",
            "connection_strategy": "short_term_workaround"
        },
        "redis": {
            "enabled": true,
            "ttl_seconds": 3600
        }
    }))
}

/// Create a new memory
///
/// Store a new memory item for the authenticated user with optional metadata.
#[utoipa::path(
    post,
    path = "/memory/remember",
    tag = "memories",
    request_body = CreateMemoryRequest,
    responses(
        (status = 200, description = "Memory created successfully", body = Memory),
        (status = 401, description = "Unauthorized - JWT token required"),
        (status = 500, description = "Internal server error")
    ),
    security(
        ("bearer_auth" = [])
    )
)]
async fn remember(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<CreateMemoryRequest>,
) -> Result<Json<Memory>, StatusCode> {
    let storage = state.storage();
    let cache = state.cache();
    let event_stream = state.event_stream();
    let user_id = user.user_id();

    match storage.create_memory(user_id, request).await {
        Ok(memory) => {
            // Invalidate cache
            if let Err(error) = cache.invalidate_user(user_id).await {
                warn!(?error, user_id = %user_id, "failed to invalidate cache after create");
            }

            // Publish memory.created event to Redis Streams (US#646: SPEC-099)
            let mut stream = event_stream.lock().await;
            if let Err(error) = stream
                .publish_memory_created(
                    memory.id,
                    user_id,
                    &memory.content,
                    memory.context_id,
                )
                .await
            {
                warn!(
                    ?error,
                    memory_id = %memory.id,
                    "failed to publish memory.created event"
                );
                // Don't fail the request if event publishing fails
            }

            Ok(Json(memory))
        }
        Err(error) => {
            error!(?error, "failed to create memory");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Recall/search memories
///
/// Search for memories matching the query text with optional result limit.
#[utoipa::path(
    post,
    path = "/memory/recall",
    tag = "memories",
    request_body = RecallRequest,
    responses(
        (status = 200, description = "Memories retrieved successfully", body = Vec<Memory>),
        (status = 401, description = "Unauthorized - JWT token required"),
        (status = 500, description = "Internal server error")
    ),
    security(
        ("bearer_auth" = [])
    )
)]
async fn recall(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<RecallRequest>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let storage = state.storage();
    let cache = state.cache();
    let event_stream = state.event_stream();
    let user_id = user.user_id();
    let RecallRequest { query, limit } = request;
    let limit = limit.unwrap_or(10).clamp(1, 100) as i64;

    if let Ok(Some(cached)) = cache.get_recall(user_id, &query, limit).await {
        return Ok(Json(cached));
    }

    match storage.recall_memories(user_id, &query, limit).await {
        Ok(memories) => {
            if let Err(error) = cache.cache_recall(user_id, &query, limit, &memories).await {
                warn!(?error, user_id = %user_id, "failed to cache recall result");
            }

            // Publish memory.recalled event to Redis Streams (US#646: SPEC-099)
            let mut stream = event_stream.lock().await;
            if let Err(error) = stream
                .publish_memory_recalled(user_id, &query, memories.len())
                .await
            {
                warn!(
                    ?error,
                    user_id = %user_id,
                    "failed to publish memory.recalled event"
                );
                // Don't fail the request if event publishing fails
            }

            Ok(Json(memories))
        }
        Err(error) => {
            error!(?error, "failed to recall memories");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// List all memories
///
/// Retrieve all memories for the authenticated user.
#[utoipa::path(
    get,
    path = "/memory/memories",
    tag = "memories",
    responses(
        (status = 200, description = "Memories retrieved successfully", body = Vec<Memory>),
        (status = 401, description = "Unauthorized - JWT token required"),
        (status = 500, description = "Internal server error")
    ),
    security(
        ("bearer_auth" = [])
    )
)]
async fn list_memories(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let storage = state.storage();
    let cache = state.cache();
    let user_id = user.user_id();

    if let Ok(Some(cached)) = cache.get_user_memories(user_id).await {
        return Ok(Json(cached));
    }

    match storage.get_memories(user_id).await {
        Ok(memories) => {
            if let Err(error) = cache.cache_user_memories(user_id, &memories).await {
                warn!(?error, user_id = %user_id, "failed to cache user memories");
            }
            Ok(Json(memories))
        }
        Err(error) => {
            error!(?error, "failed to load memories");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Delete a memory
///
/// Delete a specific memory by ID for the authenticated user.
#[utoipa::path(
    delete,
    path = "/memory/memories/{id}",
    tag = "memories",
    params(
        ("id" = Uuid, Path, description = "Memory ID to delete")
    ),
    responses(
        (status = 204, description = "Memory deleted successfully"),
        (status = 404, description = "Memory not found"),
        (status = 401, description = "Unauthorized - JWT token required"),
        (status = 500, description = "Internal server error")
    ),
    security(
        ("bearer_auth" = [])
    )
)]
async fn delete_memory(
    Path(id): Path<Uuid>,
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
) -> StatusCode {
    let storage = state.storage();
    let cache = state.cache();
    let event_stream = state.event_stream();
    let user_id = user.user_id();

    match storage.delete_memory(id, user_id).await {
        Ok(0) => StatusCode::NOT_FOUND,
        Ok(_) => {
            if let Err(error) = cache.invalidate_user(user_id).await {
                warn!(?error, user_id = %user_id, "failed to invalidate cache after delete");
            }

            // Publish memory.deleted event to Redis Streams (US#646: SPEC-099)
            let mut stream = event_stream.lock().await;
            if let Err(error) = stream.publish_memory_deleted(id, user_id).await {
                warn!(
                    ?error,
                    memory_id = %id,
                    "failed to publish memory.deleted event"
                );
                // Don't fail the request if event publishing fails
            }

            StatusCode::NO_CONTENT
        }
        Err(error) => {
            error!(?error, "failed to delete memory");
            StatusCode::INTERNAL_SERVER_ERROR
        }
    }
}
