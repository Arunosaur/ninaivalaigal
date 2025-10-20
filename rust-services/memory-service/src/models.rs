use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sqlx::FromRow;
use utoipa::ToSchema;
use uuid::Uuid;

/// Memory object representing a stored memory item
#[derive(Debug, Serialize, Deserialize, FromRow, Clone, ToSchema)]
pub struct Memory {
    /// Unique identifier for the memory
    pub id: Uuid,
    /// User who owns this memory
    pub user_id: Uuid,
    /// The actual content/text of the memory
    pub content: String,
    /// Optional context/session identifier
    pub context_id: Option<Uuid>,
    /// Additional metadata as JSON
    pub metadata: Value,
    /// Timestamp when memory was created
    pub created_at: DateTime<Utc>,
    /// Timestamp when memory was last updated
    pub updated_at: DateTime<Utc>,
}

/// Request to create a new memory
#[derive(Debug, Deserialize, ToSchema)]
pub struct CreateMemoryRequest {
    /// The content/text to remember
    pub content: String,
    /// Optional context/session identifier
    pub context_id: Option<Uuid>,
    /// Optional additional metadata as JSON
    pub metadata: Option<Value>,
}

/// Request to recall/search memories
#[derive(Debug, Deserialize, ToSchema)]
pub struct RecallRequest {
    /// Search query text
    pub query: String,
    /// Maximum number of results (default: 10, max: 100)
    #[serde(default)]
    pub limit: Option<i32>,
}
