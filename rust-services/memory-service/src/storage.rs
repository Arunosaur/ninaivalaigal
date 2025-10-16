use sqlx::postgres::{PgConnectOptions, PgPoolOptions};
use sqlx::{PgPool, Result as SqlxResult};
use std::str::FromStr;
use uuid::Uuid;

use crate::models::{CreateMemoryRequest, Memory};

#[derive(Clone)]
pub struct MemoryStorage {
    pool: PgPool,
}

impl MemoryStorage {
    pub async fn new(database_url: &str) -> SqlxResult<Self> {
        let options = PgConnectOptions::from_str(database_url)?.application_name("memory-service");

        let pool = PgPoolOptions::new()
            .max_connections(8)
            .connect_with(options)
            .await?;

        let storage = Self { pool };
        storage.initialise().await?;

        Ok(storage)
    }

    pub async fn create_memory(
        &self,
        user_id: Uuid,
        request: CreateMemoryRequest,
    ) -> SqlxResult<Memory> {
        let CreateMemoryRequest {
            content,
            context_id,
            metadata,
        } = request;

        let metadata = metadata.unwrap_or_else(|| serde_json::json!({}));

        sqlx::query_as::<_, Memory>(
            r#"
            INSERT INTO memory.memories (id, user_id, content, context_id, metadata)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING *
            "#,
        )
        .bind(Uuid::new_v4())
        .bind(user_id)
        .bind(content)
        .bind(context_id)
        .bind(metadata)
        .fetch_one(&self.pool)
        .await
    }

    pub async fn get_memories(&self, user_id: Uuid) -> SqlxResult<Vec<Memory>> {
        sqlx::query_as::<_, Memory>(
            r#"
            SELECT *
            FROM memory.memories
            WHERE user_id = $1
            ORDER BY created_at DESC
            "#,
        )
        .bind(user_id)
        .fetch_all(&self.pool)
        .await
    }

    pub async fn recall_memories(
        &self,
        user_id: Uuid,
        query: &str,
        limit: i64,
    ) -> SqlxResult<Vec<Memory>> {
        let pattern = format!("%{}%", query);

        sqlx::query_as::<_, Memory>(
            r#"
            SELECT *
            FROM memory.memories
            WHERE user_id = $1
              AND (
                    content ILIKE $2
                    OR metadata::text ILIKE $2
                )
            ORDER BY created_at DESC
            LIMIT $3
            "#,
        )
        .bind(user_id)
        .bind(pattern)
        .bind(limit)
        .fetch_all(&self.pool)
        .await
    }

    pub async fn delete_memory(&self, id: Uuid, user_id: Uuid) -> SqlxResult<u64> {
        let result = sqlx::query(
            r#"
            DELETE FROM memory.memories
            WHERE id = $1 AND user_id = $2
            "#,
        )
        .bind(id)
        .bind(user_id)
        .execute(&self.pool)
        .await?;

        Ok(result.rows_affected())
    }

    async fn initialise(&self) -> SqlxResult<()> {
        sqlx::query(
            r#"
            CREATE SCHEMA IF NOT EXISTS memory;
            "#,
        )
        .execute(&self.pool)
        .await?;

        sqlx::query(
            r#"
            CREATE TABLE IF NOT EXISTS memory.memories (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                content TEXT NOT NULL,
                context_id UUID NULL,
                metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            "#,
        )
        .execute(&self.pool)
        .await?;

        sqlx::query(
            r#"
            CREATE INDEX IF NOT EXISTS idx_memory_memories_user_id
                ON memory.memories (user_id);
            "#,
        )
        .execute(&self.pool)
        .await?;

        Ok(())
    }
}
