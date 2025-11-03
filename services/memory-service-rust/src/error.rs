use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("Redis error: {0}")]
    Redis(#[from] redis::RedisError),

    #[error("Authentication error: {0}")]
    Auth(String),

    #[error("Not found: {0}")]
    NotFound(String),

    #[error("Bad request: {0}")]
    BadRequest(String),

    #[error("Internal server error: {0}")]
    Internal(String),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, message) = match self {
            AppError::Database(ref e) => {
                tracing::error!("Database error: {}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Database error")
            }
            AppError::Redis(ref e) => {
                tracing::error!("Redis error: {}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Cache error")
            }
            AppError::Auth(ref msg) => {
                tracing::warn!("Auth error: {}", msg);
                (StatusCode::UNAUTHORIZED, "Authentication failed")
            }
            AppError::NotFound(ref msg) => {
                tracing::debug!("Not found: {}", msg);
                (StatusCode::NOT_FOUND, "Resource not found")
            }
            AppError::BadRequest(ref msg) => {
                tracing::debug!("Bad request: {}", msg);
                (StatusCode::BAD_REQUEST, "Bad request")
            }
            AppError::Internal(ref msg) => {
                tracing::error!("Internal error: {}", msg);
                (StatusCode::INTERNAL_SERVER_ERROR, "Internal server error")
            }
        };

        let body = Json(json!({
            "error": message,
            "details": self.to_string(),
        }));

        (status, body).into_response()
    }
}
