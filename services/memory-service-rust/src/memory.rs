use crate::{auth::AuthenticatedUser, error::AppError, AppState};
use axum::{
    extract::{Path, State},
    Extension, Json,
};
use chrono::{DateTime, Utc};
use redis::aio::ConnectionManager;
use serde::{Deserialize, Serialize};
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow)]
pub struct Memory {
    pub id: Uuid,
    pub user_id: Uuid,
    #[sqlx(default)]
    pub team_id: Option<Uuid>,
    #[sqlx(default)]
    pub org_id: Option<Uuid>,
    pub scope: String,
    pub kind: String,
    pub text: String,
    #[sqlx(default)]
    pub metadata: Option<serde_json::Value>,
    #[sqlx(default)]
    pub embedding: Option<String>, // pgvector stored as text, parsed if needed
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateMemoryRequest {
    pub content: String,
    #[serde(default)]
    pub metadata: Option<serde_json::Value>,
    #[serde(default = "default_kind")]
    pub kind: String,
    #[serde(default = "default_scope")]
    pub scope: String,
}

fn default_kind() -> String {
    "note".to_string()
}

fn default_scope() -> String {
    "personal".to_string()
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryResponse {
    pub id: Uuid,
    pub content: String,
    pub metadata: Option<serde_json::Value>,
    pub scope: String,
    pub kind: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// List all memories for authenticated user
pub async fn list_memories(
    State(state): State<AppState>,
    Extension(user): Extension<AuthenticatedUser>,
) -> Result<Json<Vec<MemoryResponse>>, AppError> {
    tracing::info!("Fetching memories for user: {}", user.user_id);

    let memories = sqlx::query_as::<_, Memory>(
        r#"
        SELECT id, user_id, team_id, org_id, scope, kind, text, metadata,
               embedding::text as embedding, created_at, updated_at
        FROM memory.memory_records
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 100
        "#,
    )
    .bind(user.user_id)
    .fetch_all(&state.db)
    .await?;

    let responses: Vec<MemoryResponse> = memories
        .into_iter()
        .map(|m| MemoryResponse {
            id: m.id,
            content: m.text,
            metadata: m.metadata,
            scope: m.scope,
            kind: m.kind,
            created_at: m.created_at,
            updated_at: m.updated_at,
        })
        .collect();

    Ok(Json(responses))
}

/// Create a new memory
pub async fn create_memory(
    State(state): State<AppState>,
    Extension(user): Extension<AuthenticatedUser>,
    Json(req): Json<CreateMemoryRequest>,
) -> Result<Json<MemoryResponse>, AppError> {
    tracing::info!("Creating memory for user: {}", user.user_id);

    // Validate scope
    if !["personal", "team", "organization"].contains(&req.scope.as_str()) {
        return Err(AppError::BadRequest(
            "Scope must be one of: personal, team, organization".to_string(),
        ));
    }

    let memory_id = Uuid::new_v4();
    let metadata_json = req.metadata.unwrap_or_else(|| serde_json::json!({}));

    let memory = sqlx::query_as::<_, Memory>(
        r#"
        INSERT INTO memory.memory_records
            (id, user_id, scope, kind, text, metadata, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        RETURNING id, user_id, team_id, org_id, scope, kind, text, metadata,
                   embedding::text as embedding, created_at, updated_at
        "#,
    )
    .bind(memory_id)
    .bind(user.user_id)
    .bind(&req.scope)
    .bind(&req.kind)
    .bind(&req.content)
    .bind(&metadata_json)
    .fetch_one(&state.db)
    .await?;

    let response = MemoryResponse {
        id: memory.id,
        content: memory.text,
        metadata: memory.metadata,
        scope: memory.scope,
        kind: memory.kind,
        created_at: memory.created_at,
        updated_at: memory.updated_at,
    };

    Ok(Json(response))
}

/// Get a specific memory by ID with Redis caching
pub async fn get_memory(
    State(state): State<AppState>,
    Extension(user): Extension<AuthenticatedUser>,
    Path(id): Path<Uuid>,
) -> Result<Json<MemoryResponse>, AppError> {
    tracing::info!("Fetching memory {} for user: {}", id, user.user_id);

    let cache_key = format!("memory:{}:{}", user.user_id, id);
    let cache_ttl = 3600; // 1 hour TTL

    // Try cache first
    let mut redis_conn = state.redis.clone();
    if let Ok(cached_json) = redis::cmd("GET")
        .arg(&cache_key)
        .query_async::<_, String>(&mut redis_conn)
        .await
    {
        if let Ok(response) = serde_json::from_str::<MemoryResponse>(&cached_json) {
            tracing::debug!("Cache hit for memory: {}", id);
            return Ok(Json(response));
        }
    }

    tracing::debug!("Cache miss for memory: {}, fetching from database", id);

    // Cache miss - fetch from database
    let memory = sqlx::query_as::<_, Memory>(
        r#"
        SELECT id, user_id, team_id, org_id, scope, kind, text, metadata,
               embedding::text as embedding, created_at, updated_at
        FROM memory.memory_records
        WHERE id = $1 AND user_id = $2
        "#,
    )
    .bind(id)
    .bind(user.user_id)
    .fetch_optional(&state.db)
    .await?;

    match memory {
        Some(m) => {
            let response = MemoryResponse {
                id: m.id,
                content: m.text,
                metadata: m.metadata,
                scope: m.scope,
                kind: m.kind,
                created_at: m.created_at,
                updated_at: m.updated_at,
            };

            // Store in cache (non-blocking)
            let response_json = serde_json::to_string(&response)
                .unwrap_or_else(|_| "{}".to_string());

            // Spawn async task to cache (fire and forget)
            let redis_clone = state.redis.clone();
            let cache_key_clone = cache_key.clone();
            tokio::spawn(async move {
                if let Err(e) = redis::cmd("SETEX")
                    .arg(&cache_key_clone)
                    .arg(cache_ttl)
                    .arg(&response_json)
                    .query_async::<_, ()>(&mut redis_clone.clone())
                    .await
                {
                    tracing::warn!("Failed to cache memory: {}", e);
                } else {
                    tracing::debug!("Cached memory: {}", cache_key_clone);
                }
            });

            Ok(Json(response))
        }
        None => Err(AppError::NotFound(format!("Memory {} not found", id))),
    }
}

/// Update an existing memory
pub async fn update_memory(
    State(state): State<AppState>,
    Extension(user): Extension<AuthenticatedUser>,
    Path(id): Path<Uuid>,
    Json(req): Json<CreateMemoryRequest>,
) -> Result<Json<MemoryResponse>, AppError> {
    tracing::info!("Updating memory {} for user: {}", id, user.user_id);

    // Validate scope
    if !["personal", "team", "organization"].contains(&req.scope.as_str()) {
        return Err(AppError::BadRequest(
            "Scope must be one of: personal, team, organization".to_string(),
        ));
    }

    let metadata_json = req.metadata.unwrap_or_else(|| serde_json::json!({}));

    let memory = sqlx::query_as::<_, Memory>(
        r#"
        UPDATE memory.memory_records
        SET text = $1,
            metadata = $2,
            scope = $3,
            kind = $4,
            updated_at = NOW()
        WHERE id = $5 AND user_id = $6
        RETURNING id, user_id, team_id, org_id, scope, kind, text, metadata,
                   embedding::text as embedding, created_at, updated_at
        "#,
    )
    .bind(&req.content)
    .bind(&metadata_json)
    .bind(&req.scope)
    .bind(&req.kind)
    .bind(id)
    .bind(user.user_id)
    .fetch_optional(&state.db)
    .await?;

    match memory {
        Some(m) => {
            // Invalidate cache
            let cache_key = format!("memory:{}:{}", user.user_id, id);
            let mut redis_conn = state.redis.clone();
            let _ = redis::cmd("DEL")
                .arg(&cache_key)
                .query_async::<_, ()>(&mut redis_conn)
                .await;

            let response = MemoryResponse {
                id: m.id,
                content: m.text,
                metadata: m.metadata,
                scope: m.scope,
                kind: m.kind,
                created_at: m.created_at,
                updated_at: m.updated_at,
            };

            Ok(Json(response))
        }
        None => Err(AppError::NotFound(format!("Memory {} not found", id))),
    }
}

/// Delete a memory
pub async fn delete_memory(
    State(state): State<AppState>,
    Extension(user): Extension<AuthenticatedUser>,
    Path(id): Path<Uuid>,
) -> Result<axum::http::StatusCode, AppError> {
    tracing::info!("Deleting memory {} for user: {}", id, user.user_id);

    let rows_affected = sqlx::query(
        r#"
        DELETE FROM memory.memory_records
        WHERE id = $1 AND user_id = $2
        "#,
    )
    .bind(id)
    .bind(user.user_id)
    .execute(&state.db)
    .await?
    .rows_affected();

    if rows_affected == 0 {
        return Err(AppError::NotFound(format!("Memory {} not found", id)));
    }

    // Invalidate cache
    let cache_key = format!("memory:{}:{}", user.user_id, id);
    let mut redis_conn = state.redis.clone();
    let _ = redis::cmd("DEL")
        .arg(&cache_key)
        .query_async::<_, ()>(&mut redis_conn)
        .await;

    Ok(axum::http::StatusCode::NO_CONTENT)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_memory_request() {
        let req = CreateMemoryRequest {
            content: "Test memory".to_string(),
            metadata: Some(serde_json::json!({"tag": "test"})),
        };

        assert_eq!(req.content, "Test memory");
    }
}
