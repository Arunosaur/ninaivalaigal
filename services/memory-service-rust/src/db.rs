use anyhow::Result;
use sqlx::postgres::PgPoolOptions;
use sqlx::PgPool;
use tracing::info;

pub async fn create_pool(database_url: &str) -> Result<PgPool> {
    info!("Connecting to database via PgBouncer Session Mode...");
    info!("Database URL: postgresql://***:***@***:***/***");

    // PgBouncer Session Mode now configured to ignore extra_float_digits parameter
    // We can use the connection string directly - PgBouncer will handle it
    let pool = PgPoolOptions::new()
        .max_connections(20)
        .min_connections(5)
        .acquire_timeout(std::time::Duration::from_secs(3))
        .connect(database_url)
        .await?;

    info!("Database pool created successfully via PgBouncer Session Mode");
    Ok(pool)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires running database
    async fn test_create_pool() {
        let database_url = std::env::var("DATABASE_URL")
            .unwrap_or_else(|_| {
                "postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev"
                    .to_string()
            });

        let result = create_pool(&database_url).await;
        assert!(result.is_ok());
    }
}
