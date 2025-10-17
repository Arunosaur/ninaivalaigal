mod auth;
mod cache;
mod models;
mod storage;

use auth::{require_jwt, AuthenticatedUser, JwtVerifier};
use axum::extract::{Extension, Path, State};
use axum::http::StatusCode;
use axum::routing::{delete, get, post};
use axum::{middleware, Json, Router};
use cache::MemoryCache;
use dotenvy::dotenv;
use models::{CreateMemoryRequest, Memory, RecallRequest};
use serde_json::json;
use std::env;
use std::net::SocketAddr;
use std::sync::Arc;
use storage::MemoryStorage;
use tracing::{error, info, warn};
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    storage: Arc<MemoryStorage>,
    cache: MemoryCache,
    auth: JwtVerifier,
}

impl AppState {
    fn new(storage: MemoryStorage, cache: MemoryCache, auth: JwtVerifier) -> Self {
        Self {
            storage: Arc::new(storage),
            cache,
            auth,
        }
    }

    fn storage(&self) -> Arc<MemoryStorage> {
        Arc::clone(&self.storage)
    }

    fn cache(&self) -> MemoryCache {
        self.cache.clone()
    }

    fn auth(&self) -> &JwtVerifier {
        &self.auth
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())
        .with_target(false)
        .compact()
        .init();

    let _ = dotenv();
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

    let jwt_secret =
        env::var("NINAIVALAIGAL_JWT_SECRET").expect("NINAIVALAIGAL_JWT_SECRET must be set");
    let jwt = JwtVerifier::new(&jwt_secret);

    let state = Arc::new(AppState::new(storage, cache, jwt));

    let port: u16 = env::var("PORT")
        .unwrap_or_else(|_| "8000".to_string())
        .parse()
        .expect("PORT must be a valid u16");
    let addr = SocketAddr::from(([0, 0, 0, 0], port));

    let protected = Router::new()
        .route("/memory/remember", post(remember))
        .route("/memory/recall", post(recall))
        .route("/memory/memories", get(list_memories))
        .route("/memory/memories/:id", delete(delete_memory))
        .layer(middleware::from_fn_with_state(
            Arc::clone(&state),
            require_jwt,
        ));

    let app = Router::new()
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
}

async fn health() -> Json<serde_json::Value> {
    Json(json!({
        "status": "healthy",
        "service": "memory-service",
        "language": "rust"
    }))
}

async fn remember(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<CreateMemoryRequest>,
) -> Result<Json<Memory>, StatusCode> {
    let storage = state.storage();
    let cache = state.cache();
    let user_id = user.user_id();

    match storage.create_memory(user_id, request).await {
        Ok(memory) => {
            if let Err(error) = cache.invalidate_user(user_id).await {
                warn!(?error, user_id = %user_id, "failed to invalidate cache after create");
            }
            Ok(Json(memory))
        }
        Err(error) => {
            error!(?error, "failed to create memory");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

async fn recall(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<RecallRequest>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let storage = state.storage();
    let cache = state.cache();
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
            Ok(Json(memories))
        }
        Err(error) => {
            error!(?error, "failed to recall memories");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

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

async fn delete_memory(
    Path(id): Path<Uuid>,
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
) -> StatusCode {
    let storage = state.storage();
    let cache = state.cache();
    let user_id = user.user_id();

    match storage.delete_memory(id, user_id).await {
        Ok(0) => StatusCode::NOT_FOUND,
        Ok(_) => {
            if let Err(error) = cache.invalidate_user(user_id).await {
                warn!(?error, user_id = %user_id, "failed to invalidate cache after delete");
            }
            StatusCode::NO_CONTENT
        }
        Err(error) => {
            error!(?error, "failed to delete memory");
            StatusCode::INTERNAL_SERVER_ERROR
        }
    }
}
