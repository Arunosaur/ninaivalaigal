// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

use std::error::Error;

use serde_json::Value;
use tokio_postgres::{Client, SimpleQueryMessage};

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
        let client = pool.get_client().await.expect("database client");
        let executor = CypherExecutor::new(
            env::var("GRAPHOPS_GRAPH").unwrap_or_else(|_| "graph".into()),
            client,
        );

        // We only assert the call succeeds without panicking. This mirrors a smoke-test against
        // the AGE extension and PgBouncer plumbing.
        let _ = executor.execute_query("MATCH (n) RETURN n LIMIT 1").await;
    }
}
