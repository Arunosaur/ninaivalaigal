// SPDX-License-Identifier: Proprietary
// Copyright (c) 2025 Medhasys LLC
//
// This file contains proprietary code owned by Medhasys LLC.
// Unauthorized copying, modification, or distribution is prohibited.
// See LICENSE file in the server/ directory for details.

use std::str::FromStr;

use tokio_postgres::config::Config;
use tokio_postgres::{Client, NoTls};

/// Lightweight connection factory that relies on PgBouncer for pooling.
///
/// We deliberately keep this struct cloneable so callers can pass it into async tasks
/// and obtain short-lived clients on demand. PgBouncer sits in front of Postgres and
/// handles connection reuse, so we only need to validate the DSN and spawn the
/// background connection task per client.
#[derive(Clone, Debug)]
pub struct DbPool {
    config: Config,
}

impl DbPool {
    /// Create a new pool definition from a PostgreSQL connection string.
    ///
    /// The connection string should point to the PgBouncer endpoint (usually transaction
    /// pooling mode). We still keep a local clone of the parsed configuration so we can
    /// request fresh logical connections per query executor.
    pub fn new(database_url: &str) -> Result<Self, Box<dyn std::error::Error + Send + Sync>> {
        let mut config = Config::from_str(database_url)?;

        // Ensure we have an application name in PgBouncer/pg_stat_activity for observability.
        config.application_name("graphops-service");

        Ok(Self { config })
    }

    /// Acquire a new asynchronous Postgres client.
    ///
    /// The returned client is backed by the PgBouncer connection pool; callers should keep
    /// it scoped to a single request or task. The background connection driver is spawned
    /// onto the Tokio runtime to satisfy the tokio-postgres contract.
    pub async fn get_client(&self) -> Result<Client, tokio_postgres::Error> {
        let (client, connection) = self.config.clone().connect(NoTls).await?;

        tokio::spawn(async move {
            if let Err(error) = connection.await {
                tracing::error!(?error, "database connection terminated unexpectedly");
            }
        });

        // Initialize Apache AGE extension for graph queries
        client.simple_query("LOAD 'age';").await?;
        client
            .simple_query("SET search_path = ag_catalog, \"$user\", public;")
            .await?;

        Ok(client)
    }
}

#[cfg(test)]
mod tests {
    use super::DbPool;
    use std::env;

    #[tokio::test]
    async fn db_connection_test() -> Result<(), tokio_postgres::Error> {
        // Load .env file if present (silently ignore if missing)
        let _ = dotenvy::dotenv();

        let database_url = match env::var("DATABASE_URL") {
            Ok(url) => url,
            Err(_) => {
                eprintln!("DATABASE_URL not set – skipping db_connection_test");
                return Ok(());
            }
        };

        let pool = DbPool::new(&database_url).expect("valid DATABASE_URL");
        let client = pool.get_client().await?;

        // Simple probe to confirm the connection is alive. PgBouncer will recycle the backend
        // connection once this client is dropped.
        let _ = client.simple_query("SELECT 1;").await?;

        Ok(())
    }
}
