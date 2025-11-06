//! Memory Injection API - High-throughput bulk operations
//! US#93/US#95: Memory Router Rationalization - SPEC-131
//!
//! This module provides bulk memory injection capabilities optimized for performance.
//! Migrated from Python memory_injection_api.py to leverage Rust's performance benefits.

use axum::extract::{Extension, State};
use axum::http::StatusCode;
use axum::Json;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::sync::Arc;
use tracing::{error, info};

use crate::AppState;
use crate::auth::AuthenticatedUser;
use crate::models::Memory;
use crate::services::injection_service::InjectionService;

/// Request to analyze injection opportunities
#[derive(Debug, Deserialize)]
pub struct InjectionAnalysisRequest {
    pub session_id: Option<String>,
    pub current_activity: Option<String>,
    pub location_context: Value,
    pub temporal_context: Value,
    pub semantic_context: Value,
    pub user_state: Value,
    pub environment: Value,
    #[serde(default = "default_max_candidates")]
    pub max_candidates: usize,
}

fn default_max_candidates() -> usize {
    10
}

/// Response from injection analysis
#[derive(Debug, Serialize)]
pub struct InjectionAnalysisResponse {
    pub candidates: Vec<InjectionCandidate>,
    pub total_candidates: usize,
    pub analysis_time_ms: f64,
    pub rules_evaluated: usize,
    pub context_summary: Value,
}

/// Memory candidate for injection
#[derive(Debug, Serialize)]
pub struct InjectionCandidate {
    pub memory_id: String,
    pub relevance_score: f64,
    pub injection_reason: String,
    pub rule_id: Option<String>,
    pub confidence: f64,
    pub urgency: f64,
    pub context_match: Value,
    pub suggested_timing: String,
    pub metadata: Value,
}

/// Request to execute memory injection
#[derive(Debug, Deserialize)]
pub struct InjectionExecutionRequest {
    pub context: InjectionAnalysisRequest,
    #[serde(default = "default_strategy")]
    pub strategy: String,
    #[serde(default = "default_max_injections")]
    pub max_injections: usize,
}

fn default_strategy() -> String {
    "contextual".to_string()
}

fn default_max_injections() -> usize {
    5
}

/// Response from injection execution
#[derive(Debug, Serialize)]
pub struct InjectionExecutionResponse {
    pub injected_memories: Vec<Memory>,
    pub execution_time_ms: f64,
    pub strategy_used: String,
    pub success_count: usize,
    pub context_snapshot: Value,
}

/// Analyze injection opportunities
///
/// Analyzes current context and identifies memory injection opportunities
/// based on context rules and user state.
pub async fn analyze_injection_opportunities(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<InjectionAnalysisRequest>,
) -> Result<Json<InjectionAnalysisResponse>, StatusCode> {
    let start = std::time::Instant::now();
    let user_id = user.user_id();

    info!(
        user_id = %user_id,
        session_id = ?request.session_id,
        "analyzing injection opportunities"
    );

    let injection_service = InjectionService::new(state.storage(), state.cache());

    let context = serde_json::json!({
        "user_id": user_id.to_string(),
        "session_id": request.session_id,
        "current_activity": request.current_activity,
        "location_context": request.location_context,
        "temporal_context": request.temporal_context,
        "semantic_context": request.semantic_context,
        "user_state": request.user_state,
        "environment": request.environment,
    });

    match injection_service
        .analyze_opportunities(user_id, &context, request.max_candidates)
        .await
    {
        Ok(candidates) => {
            let analysis_time = start.elapsed().as_secs_f64() * 1000.0;
            let total_candidates = candidates.len();

            Ok(Json(InjectionAnalysisResponse {
                candidates,
                total_candidates,
                analysis_time_ms: analysis_time,
                rules_evaluated: 0, // TODO: Implement rule tracking
                context_summary: serde_json::json!({
                    "activity": request.current_activity,
                    "session_id": request.session_id,
                    "context_keys": request.semantic_context.as_object().map(|o| o.keys().collect::<Vec<_>>()),
                }),
            }))
        }
        Err(e) => {
            error!(?e, user_id = %user_id, "failed to analyze injection opportunities");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Execute memory injection
///
/// Executes memory injection based on context and strategy.
pub async fn execute_memory_injection(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<InjectionExecutionRequest>,
) -> Result<Json<InjectionExecutionResponse>, StatusCode> {
    let start = std::time::Instant::now();
    let user_id = user.user_id();

    info!(
        user_id = %user_id,
        strategy = %request.strategy,
        max_injections = request.max_injections,
        "executing memory injection"
    );

    let injection_service = InjectionService::new(state.storage(), state.cache());

    let context = serde_json::json!({
        "user_id": user_id.to_string(),
        "session_id": request.context.session_id,
        "current_activity": request.context.current_activity,
        "location_context": request.context.location_context,
        "temporal_context": request.context.temporal_context,
        "semantic_context": request.context.semantic_context,
        "user_state": request.context.user_state,
        "environment": request.context.environment,
    });

    match injection_service
        .inject_memories(user_id, &context, &request.strategy, request.max_injections)
        .await
    {
        Ok(injected_memories) => {
            let execution_time = start.elapsed().as_secs_f64() * 1000.0;
            let success_count = injected_memories.len();

            Ok(Json(InjectionExecutionResponse {
                injected_memories,
                execution_time_ms: execution_time,
                strategy_used: request.strategy,
                success_count,
                context_snapshot: context,
            }))
        }
        Err(e) => {
            error!(?e, user_id = %user_id, "failed to execute memory injection");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Bulk inject memories (high-performance path)
///
/// High-throughput bulk memory injection for pipeline processing.
/// This is the primary performance-critical endpoint for bulk operations.
pub async fn bulk_inject_memories(
    State(state): State<Arc<AppState>>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(request): Json<Vec<serde_json::Value>>,
) -> Result<Json<BulkInjectionResponse>, StatusCode> {
    let start = std::time::Instant::now();
    let user_id = user.user_id();

    info!(
        user_id = %user_id,
        batch_size = request.len(),
        "bulk injecting memories"
    );

    let injection_service = InjectionService::new(state.storage(), state.cache());

    match injection_service.bulk_inject(user_id, &request).await {
        Ok(results) => {
            let execution_time = start.elapsed().as_secs_f64() * 1000.0;
            let success_count = results.iter().filter(|r| r.success).count();

            Ok(Json(BulkInjectionResponse {
                total_requested: request.len(),
                success_count,
                failed_count: results.len() - success_count,
                execution_time_ms: execution_time,
                results,
            }))
        }
        Err(e) => {
            error!(?e, user_id = %user_id, "failed to bulk inject memories");
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Response from bulk injection
#[derive(Debug, Serialize)]
pub struct BulkInjectionResponse {
    pub total_requested: usize,
    pub success_count: usize,
    pub failed_count: usize,
    pub execution_time_ms: f64,
    pub results: Vec<BulkInjectionResult>,
}

/// Result for a single bulk injection item
#[derive(Debug, Serialize)]
pub struct BulkInjectionResult {
    pub success: bool,
    pub memory_id: Option<String>,
    pub error: Option<String>,
}
