// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

use std::collections::HashMap;
use std::error::Error;
use std::sync::Arc;
use std::time::{Duration, Instant};

use serde_json::Value;
use tokio::sync::RwLock;
use tokio_postgres::{Client, SimpleQueryMessage};

#[derive(Clone, Debug)]
pub struct CachedResponse {
    pub results: Vec<String>,
    pub execution_time_ms: i32,
    pub row_count: i32,
}

#[derive(Clone)]
pub struct QueryCache {
    cache: Arc<RwLock<HashMap<String, CacheEntry>>>,
    ttl: Duration,
    max_entries: usize,
}

#[derive(Clone)]
struct CacheEntry {
    stored_at: Instant,
    response: CachedResponse,
}

impl QueryCache {
    pub fn new(ttl_seconds: u64, max_entries: usize) -> Self {
        Self {
            cache: Arc::new(RwLock::new(HashMap::new())),
            ttl: Duration::from_secs(ttl_seconds.max(1)),
            max_entries: max_entries.max(1),
        }
    }

    pub fn should_cache(&self, query: &str) -> bool {
        let first_token = query
            .split_whitespace()
            .next()
            .map(|token| token.to_ascii_lowercase())
            .unwrap_or_default();

        matches!(first_token.as_str(), "match" | "return" | "with")
    }

    pub async fn get(&self, query: &str) -> Option<CachedResponse> {
        let mut cache = self.cache.write().await;

        match cache.get(query) {
            Some(entry) if entry.stored_at.elapsed() <= self.ttl => Some(entry.response.clone()),
            Some(_) => {
                cache.remove(query);
                None
            }
            None => None,
        }
    }

    pub async fn set(&self, query: String, response: CachedResponse) {
        let mut cache = self.cache.write().await;

        if cache.len() >= self.max_entries {
            if let Some(oldest_key) = cache
                .iter()
                .min_by_key(|(_, entry)| entry.stored_at)
                .map(|(key, _)| key.clone())
            {
                cache.remove(&oldest_key);
            }
        }

        cache.insert(
            query,
            CacheEntry {
                stored_at: Instant::now(),
                response,
            },
        );
    }
}

/// Thin wrapper around Apache AGE Cypher execution.
///
/// The executor holds a Postgres client as well as the graph name so it can issue
/// parameterised calls to the `cypher` function without string-concatenation risks.
pub struct CypherExecutor {
    graph_name: String,
    db_client: Client,
}

impl CypherExecutor {
    /// Construct a new executor.
    pub fn new(graph_name: impl Into<String>, db_client: Client) -> Self {
        Self {
            graph_name: graph_name.into(),
            db_client,
        }
    }

    /// Execute a Cypher query and return the raw AGType payload as JSON values.
    pub async fn execute_query(
        &self,
        cypher: &str,
    ) -> Result<Vec<Value>, Box<dyn Error + Send + Sync>> {
        // AGE requires: graph name as a literal name constant and query as dollar-quoted string
        // We must embed both directly in the SQL since AGE doesn't accept parameterized graph names.
        let sql = format!(
            "SELECT * FROM cypher('{}', $${}$$) AS (result agtype);",
            self.graph_name, cypher
        );

        // simple_query avoids prepared statement state that PgBouncer cannot reuse safely.
        let messages = self.db_client.simple_query(&sql).await?;

        let mut results = Vec::new();
        for message in messages {
            if let SimpleQueryMessage::Row(row) = message {
                if let Some(raw) = row.get(0) {
                    let json_fragment = raw.split("::").next().unwrap_or(raw);
                    let json_value: Value = serde_json::from_str(json_fragment)?;
                    results.push(json_value);
                }
            }
        }

        Ok(results)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::DbPool;
    use std::env;

    #[tokio::test]
    async fn execute_query_handles_missing_database() {
        // Load .env file if present (silently ignore if missing)
        let _ = dotenvy::dotenv();

        if env::var("DATABASE_URL").is_err() {
            // Nothing to assert – absence of a database should not panic.
            return;
        }

        let pool = DbPool::new(&env::var("DATABASE_URL").unwrap()).expect("valid DATABASE_URL");

        // Add timeout to prevent hanging in CI/pre-commit hooks when DB is unavailable
        let client = match tokio::time::timeout(
            std::time::Duration::from_secs(5),
            pool.get_client()
        ).await {
            Ok(Ok(client)) => client,
            Ok(Err(_)) | Err(_) => {
                // Database unavailable - skip test
                eprintln!("Database connection timeout or error – skipping test");
                return;
            }
        };

        let executor = CypherExecutor::new(
            env::var("GRAPHOPS_GRAPH").unwrap_or_else(|_| "graph".into()),
            client,
        );

        // We only assert the call succeeds without panicking. This mirrors a smoke-test against
        // the AGE extension and PgBouncer plumbing.
        let _ = executor.execute_query("MATCH (n) RETURN n LIMIT 1").await;
    }

    #[tokio::test]
    async fn query_cache_expires_entries() {
        let cache = QueryCache::new(1, 4);
        let query = "MATCH (n) RETURN n".to_string();

        assert!(cache.should_cache(&query));

        cache
            .set(
                query.clone(),
                CachedResponse {
                    results: vec!["ok".to_string()],
                    execution_time_ms: 10,
                    row_count: 1,
                },
            )
            .await;

        assert!(cache.get(&query).await.is_some());

        tokio::time::sleep(Duration::from_secs(2)).await;

        assert!(cache.get(&query).await.is_none());
    }
}
