use axum::{
    extract::State,
    http::{HeaderValue, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tracing::{info, warn};

mod auth;
mod config;
mod db;
mod error;
mod memory;
mod metrics;
mod redis_client;

use auth::validate_jwt;
use axum::middleware;

use config::Config;
use error::AppError;

#[derive(Clone)]
pub struct AppState {
    db: sqlx::PgPool,
    redis: redis::aio::ConnectionManager,
    config: Arc<Config>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    service: String,
    version: String,
    database: String,
    redis: String,
}

#[derive(Serialize)]
struct MetricsResponse {
    active_connections: u32,
    total_requests: u64,
    cache_hits: u64,
    cache_misses: u64,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info")),
        )
        .json()
        .init();

    info!("🚀 Starting Memory Service (Rust)");

    // Load configuration
    let config = Config::from_env()?;
    info!("📝 Configuration loaded");

    // Initialize database connection
    let db = db::create_pool(&config.database_url).await?;
    info!("✅ Database connection established");

    // Initialize Redis connection
    let redis = redis_client::create_connection(&config.redis_url).await?;
    info!("✅ Redis connection established");

    // Create application state
    let state = AppState {
        db,
        redis,
        config: Arc::new(config),
    };

    // Configure CORS
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Build router with protected API routes
    let api_routes = Router::new()
        .route(
            "/api/v1/memories",
            get(memory::list_memories).post(memory::create_memory),
        )
        .route("/api/v1/memories/:id", get(memory::get_memory))
        .route_layer(middleware::from_fn(validate_jwt));

    // Initialize global Prometheus metrics
    let _ = metrics::Metrics::new().expect("Failed to initialize metrics");

    let app = Router::new()
        .route("/health", get(health_check))
        .route("/metrics", get(metrics_handler))
        .merge(api_routes)
        .with_state(state)
        .layer(cors);

    // Start server
    let addr = format!("0.0.0.0:{}", 8000);
    let listener = tokio::net::TcpListener::bind(&addr).await?;

    info!("🎧 Memory Service listening on {}", addr);
    info!("📍 Health check: http://localhost:13393/health");
    info!("📊 Metrics: http://localhost:13393/metrics");

    axum::serve(listener, app).await?;

    Ok(())
}

async fn health_check(State(state): State<AppState>) -> Result<Json<HealthResponse>, AppError> {
    // Check database
    let db_status = match sqlx::query("SELECT 1").fetch_one(&state.db).await {
        Ok(_) => "healthy",
        Err(e) => {
            warn!("Database health check failed: {}", e);
            "unhealthy"
        }
    };

    // Check Redis
    let redis_status = match redis::cmd("PING")
        .query_async::<_, String>(&mut state.redis.clone())
        .await
    {
        Ok(_) => "healthy",
        Err(e) => {
            warn!("Redis health check failed: {}", e);
            "unhealthy"
        }
    };

    let overall_status = if db_status == "healthy" && redis_status == "healthy" {
        "healthy"
    } else {
        "degraded"
    };

    Ok(Json(HealthResponse {
        status: overall_status.to_string(),
        service: "memory-service".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        database: db_status.to_string(),
        redis: redis_status.to_string(),
    }))
}

async fn metrics_handler() -> Result<Response<String>, AppError> {
    // Use Prometheus encoder to output metrics in Prometheus text format
    use prometheus::{Encoder, TextEncoder, gather};

    let encoder = TextEncoder::new();
    let metric_families = gather();
    let mut buffer = Vec::new();

    encoder.encode(&metric_families, &mut buffer)
        .map_err(|e| AppError::Internal(e.to_string()))?;

    let metrics_text = String::from_utf8(buffer)
        .map_err(|e| AppError::Internal(format!("Invalid UTF-8 in metrics: {}", e)))?;

    let mut response = Response::new(metrics_text);
    response.headers_mut().insert(
        axum::http::header::CONTENT_TYPE,
        HeaderValue::from_static("text/plain; version=0.0.4; charset=utf-8")
    );

    Ok(response)
}
