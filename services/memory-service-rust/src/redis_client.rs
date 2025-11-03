use anyhow::Result;
use redis::aio::ConnectionManager;
use redis::Client;
use tracing::info;

pub async fn create_connection(redis_url: &str) -> Result<ConnectionManager> {
    info!("Connecting to Redis at {}...", redis_url);

    let client = Client::open(redis_url)?;
    let manager = ConnectionManager::new(client).await?;

    // Test connection
    let mut conn = manager.clone();
    redis::cmd("PING").query_async::<_, String>(&mut conn).await?;

    info!("Redis connection established successfully");
    Ok(manager)
}

/// Cache-aside pattern helper
pub async fn get_or_fetch<F, T>(
    conn: &mut ConnectionManager,
    key: &str,
    ttl: usize,
    fetch_fn: F,
) -> Result<T>
where
    F: std::future::Future<Output = Result<T>>,
    T: serde::de::DeserializeOwned + serde::Serialize,
{
    // Try cache first
    if let Ok(cached) = redis::cmd("GET")
        .arg(key)
        .query_async::<_, String>(conn)
        .await
    {
        if let Ok(value) = serde_json::from_str(&cached) {
            tracing::debug!("Cache hit for key: {}", key);
            return Ok(value);
        }
    }

    tracing::debug!("Cache miss for key: {}", key);

    // Fetch from source
    let value = fetch_fn.await?;

    // Store in cache
    let json = serde_json::to_string(&value)?;
    redis::cmd("SETEX")
        .arg(key)
        .arg(ttl)
        .arg(json)
        .query_async::<_, ()>(conn)
        .await?;

    Ok(value)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    #[ignore] // Requires running Redis
    async fn test_create_connection() {
        let redis_url = std::env::var("REDIS_URL")
            .unwrap_or_else(|_| "redis://localhost:6379".to_string());

        let result = create_connection(&redis_url).await;
        assert!(result.is_ok());
    }
}
