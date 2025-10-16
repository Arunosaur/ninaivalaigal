use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sqlx::FromRow;
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, FromRow, Clone)]
pub struct Memory {
    pub id: Uuid,
    pub user_id: Uuid,
    pub content: String,
    pub context_id: Option<Uuid>,
    pub metadata: Value,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Deserialize)]
pub struct CreateMemoryRequest {
    pub content: String,
    pub context_id: Option<Uuid>,
    pub metadata: Option<Value>,
}

#[derive(Debug, Deserialize)]
pub struct RecallRequest {
    pub query: String,
    #[serde(default)]
    pub limit: Option<i32>,
}
