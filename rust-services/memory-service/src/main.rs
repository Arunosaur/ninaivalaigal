mod auth;
mod models;
mod storage;

use auth::{require_jwt, AuthenticatedUser, JwtVerifier};
use axum::extract::{Extension, Path, State};
use axum::http::StatusCode;
use axum::routing::{delete, get, post};
use axum::{middleware, Json, Router};
use dotenvy::dotenv;
use models::RecallRequest;
use models::{CreateMemoryRequest, Memory};
use serde_json::json;
use std::env;
use std::net::SocketAddr;
use std::sync::Arc;
use storage::MemoryStorage;
use tracing::{error, info};
use tracing_subscriber::EnvFilter;
use uuid::Uuid;

#[derive(Clone)]
pub struct AppState {
    storage: Arc<MemoryStorage>,
    auth: JwtVerifier,
}

impl AppState {
    fn new(storage: MemoryStorage, auth: JwtVerifier) -> Self {
        Self {
            storage: Arc::new(storage),
            auth,
        }
    }

    fn storage(&self) -> Arc<MemoryStorage> {
        Arc::clone(&self.storage)
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

    let storage = MemoryStorage::new(&database_url)
        .await
        .expect("failed to initialise MemoryStorage");

    let jwt_secret =
        env::var("NINAIVALAIGAL_JWT_SECRET").expect("NINAIVALAIGAL_JWT_SECRET must be set");
    let jwt = JwtVerifier::new(&jwt_secret);

    let state = Arc::new(AppState::new(storage, jwt));

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
    let user_id = user.user_id();

    storage
        .create_memory(user_id, request)
        .await
        .map(Json)
        .map_err(|error| {
            error!(?error, "failed to create memory");
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

async fn recall(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<RecallRequest>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let limit = request.limit.unwrap_or(10).clamp(1, 100);
    let storage = state.storage();

    storage
        .recall_memories(user.user_id(), &request.query, limit as i64)
        .await
        .map(Json)
        .map_err(|error| {
            error!(?error, "failed to recall memories");
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

async fn list_memories(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
) -> Result<Json<Vec<Memory>>, StatusCode> {
    let storage = state.storage();

    storage
        .get_memories(user.user_id())
        .await
        .map(Json)
        .map_err(|error| {
            error!(?error, "failed to load memories");
            StatusCode::INTERNAL_SERVER_ERROR
        })
}

async fn delete_memory(
    Path(id): Path<Uuid>,
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
) -> StatusCode {
    let storage = state.storage();

    match storage.delete_memory(id, user.user_id()).await {
        Ok(0) => StatusCode::NOT_FOUND,
        Ok(_) => StatusCode::NO_CONTENT,
        Err(error) => {
            error!(?error, "failed to delete memory");
            StatusCode::INTERNAL_SERVER_ERROR
        }
    }
}
