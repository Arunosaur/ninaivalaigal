//! Queue API - Redis-based task management
//! US#93/US#95: Memory Router Rationalization - SPEC-131
//!
//! This module provides queue management for background tasks.
//! Migrated from Python queue_api.py to leverage Rust's async performance.

use axum::extract::{Extension, Path, Query, State};
use axum::http::StatusCode;
use axum::Json;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tracing::{error, info};

use crate::AppState;
use crate::auth::AuthenticatedUser;
use crate::services::queue_service::QueueService;

/// Request to enqueue a task
#[derive(Debug, Deserialize)]
pub struct TaskRequest {
    pub task_type: String,
    pub parameters: Value,
}

/// Response from task enqueue
#[derive(Debug, Serialize)]
pub struct TaskResponse {
    pub job_id: String,
    pub status: String,
    pub message: String,
}

/// Response for job status
#[derive(Debug, Serialize)]
pub struct JobStatusResponse {
    pub id: String,
    pub status: String,
    pub created_at: Option<String>,
    pub started_at: Option<String>,
    pub ended_at: Option<String>,
    pub result: Option<Value>,
    pub error: Option<String>,
}

/// Response for queue statistics
#[derive(Debug, Serialize)]
pub struct QueueStatsResponse {
    pub queues: HashMap<String, QueueStats>,
    pub total_jobs: usize,
    pub healthy: bool,
}

/// Statistics for a queue
#[derive(Debug, Serialize)]
pub struct QueueStats {
    pub length: usize,
    pub failed_job_count: usize,
    pub scheduled_job_count: usize,
    pub started_job_count: usize,
    pub deferred_job_count: usize,
}

/// Enqueue a background task
pub async fn enqueue_task(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<TaskRequest>,
) -> Result<Json<TaskResponse>, StatusCode> {
    let user_id = user.user_id();

    info!(
        user_id = %user_id,
        task_type = %request.task_type,
        "enqueueing task"
    );

    let mut queue_service = QueueService::new(state.cache());

    match queue_service
        .enqueue_task(user_id, &request.task_type, &request.parameters)
        .await
    {
        Ok(job_id) => Ok(Json(TaskResponse {
            job_id,
            status: "enqueued".to_string(),
            message: format!("Task {} enqueued successfully", request.task_type),
        })),
        Err(e) => {
            error!(?e, user_id = %user_id, "failed to enqueue task");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Get status of a background job
pub async fn get_job_status(
    State(state): State<Arc<AppState>>,
    Extension(_user): Extension<AuthenticatedUser>,
    Path(job_id): Path<String>,
) -> Result<Json<JobStatusResponse>, StatusCode> {
    let mut queue_service = QueueService::new(state.cache());

    match queue_service.get_job_status(&job_id).await {
        Ok(Some(status)) => Ok(Json(status)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(e) => {
            error!(?e, job_id = %job_id, "failed to get job status");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Get queue statistics
pub async fn get_queue_stats(
    State(state): State<Arc<AppState>>,
    Extension(_user): Extension<AuthenticatedUser>,
) -> Result<Json<QueueStatsResponse>, StatusCode> {
    let mut queue_service = QueueService::new(state.cache());

    match queue_service.get_queue_stats().await {
        Ok(stats) => Ok(Json(stats)),
        Err(e) => {
            error!(?e, "failed to get queue stats");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Enqueue memory processing task (convenience endpoint)
pub async fn process_memory_async(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Path(memory_id): Path<String>,
    Query(params): Query<HashMap<String, String>>,
) -> Result<Json<Value>, StatusCode> {
    let user_id = user.user_id();
    let text = params.get("text").cloned().unwrap_or_default();
    let metadata = params
        .get("metadata")
        .and_then(|s| serde_json::from_str::<Value>(s).ok());

    let mut queue_service = QueueService::new(state.cache());

    let parameters = serde_json::json!({
        "memory_id": memory_id,
        "text": text,
        "metadata": metadata,
    });

    match queue_service
        .enqueue_task(user_id, "memory_processing", &parameters)
        .await
    {
        Ok(job_id) => Ok(Json(serde_json::json!({
            "job_id": job_id,
            "memory_id": memory_id,
            "status": "processing",
            "message": "Memory processing started in background",
        }))),
        Err(e) => {
            error!(?e, user_id = %user_id, "failed to enqueue memory processing");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Health check for queue system
pub async fn queue_health(
    State(state): State<Arc<AppState>>,
) -> Json<Value> {
    let mut queue_service = QueueService::new(state.cache());

    match queue_service.health_check().await {
        Ok(health) => Json(health),
        Err(e) => {
            error!(?e, "queue health check failed");
            Json(serde_json::json!({
                "status": "unhealthy",
                "error": e.to_string(),
                "connected": false,
            }))
        }
    }
}
