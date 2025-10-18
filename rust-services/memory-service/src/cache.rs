use std::sync::Arc;

use base64::engine::general_purpose::URL_SAFE_NO_PAD;
use base64::Engine;
use redis::aio::ConnectionManager;
use redis::{AsyncCommands, RedisError, RedisResult};
use serde::de::DeserializeOwned;
use serde::Serialize;
use tokio::sync::Mutex;
use tracing::warn;
use uuid::Uuid;

use crate::models::Memory;

#[derive(Clone)]
pub struct MemoryCache {
    connection: Arc<Mutex<ConnectionManager>>,
    ttl_seconds: u64,
}

impl MemoryCache {
    pub async fn new(redis_url: &str, ttl_seconds: u64) -> RedisResult<Self> {
        let ttl = ttl_seconds.max(1);
        let client = redis::Client::open(redis_url)?;
        let connection = ConnectionManager::new(client).await?;

        Ok(Self {
            connection: Arc::new(Mutex::new(connection)),
            ttl_seconds: ttl,
        })
    }

    pub async fn cache_user_memories(&self, user_id: Uuid, memories: &[Memory]) -> RedisResult<()> {
        self.write_json(user_memories_key(user_id), memories).await
    }

    pub async fn get_user_memories(&self, user_id: Uuid) -> RedisResult<Option<Vec<Memory>>> {
        self.read_json(user_memories_key(user_id)).await
    }

    pub async fn cache_recall(
        &self,
        user_id: Uuid,
        query: &str,
        limit: i64,
        memories: &[Memory],
    ) -> RedisResult<()> {
        let key = recall_key(user_id, query, limit);
        self.write_json(key.clone(), memories).await?;
        self.track_recall_key(user_id, key).await
    }

    pub async fn get_recall(
        &self,
        user_id: Uuid,
        query: &str,
        limit: i64,
    ) -> RedisResult<Option<Vec<Memory>>> {
        self.read_json(recall_key(user_id, query, limit)).await
    }

    pub async fn invalidate_user(&self, user_id: Uuid) -> RedisResult<()> {
        let list_key = user_memories_key(user_id);
        let recall_index = recall_index_key(user_id);

        let mut conn = self.connection.lock().await;

        let recall_keys: Vec<String> = match conn.smembers(&recall_index).await {
            Ok(keys) => keys,
            Err(error) => {
                warn!(?error, %recall_index, "failed to load recall cache index");
                Vec::new()
            }
        };

        if !recall_keys.is_empty() {
            if let Err(error) = conn.del::<_, usize>(&recall_keys).await {
                warn!(?error, "failed to drop recall cache entries");
            }
        }

        if let Err(error) = conn.del::<_, usize>(&list_key).await {
            warn!(?error, %list_key, "failed to drop user memory cache");
        }

        if let Err(error) = conn.del::<_, usize>(&recall_index).await {
            warn!(?error, %recall_index, "failed to drop recall index cache");
        }

        Ok(())
    }

    async fn track_recall_key(&self, user_id: Uuid, key: String) -> RedisResult<()> {
        let recall_index = recall_index_key(user_id);
        let mut conn = self.connection.lock().await;
        let _: usize = conn.sadd(&recall_index, &key).await?;
        let _: bool = conn.expire(&recall_index, self.ttl_seconds as i64).await?;
        Ok(())
    }

    async fn write_json<T>(&self, key: String, value: &T) -> RedisResult<()>
    where
        T: Serialize + ?Sized,
    {
        let payload = serde_json::to_vec(value).map_err(|_| {
            RedisError::from((
                redis::ErrorKind::TypeError,
                "failed to serialise value for cache",
            ))
        })?;

        let mut conn = self.connection.lock().await;
        let _: () = conn.set_ex(key, payload, self.ttl_seconds).await?;
        Ok(())
    }

    async fn read_json<T>(&self, key: String) -> RedisResult<Option<T>>
    where
        T: DeserializeOwned,
    {
        let mut conn = self.connection.lock().await;
        let bytes: Option<Vec<u8>> = conn.get(&key).await?;

        if let Some(payload) = bytes {
            match serde_json::from_slice::<T>(&payload) {
                Ok(value) => Ok(Some(value)),
                Err(error) => {
                    warn!(?error, %key, "failed to deserialize cached value");
                    if let Err(delete_error) = conn.del::<_, usize>(&key).await {
                        warn!(?delete_error, %key, "failed to purge corrupt cache entry");
                    }
                    Ok(None)
                }
            }
        } else {
            Ok(None)
        }
    }
}

fn user_memories_key(user_id: Uuid) -> String {
    format!("memories:user:{user_id}:all")
}

fn recall_key(user_id: Uuid, query: &str, limit: i64) -> String {
    let encoded = URL_SAFE_NO_PAD.encode(query.as_bytes());
    format!("memories:user:{user_id}:recall:{limit}:{encoded}")
}

fn recall_index_key(user_id: Uuid) -> String {
    format!("memories:user:{user_id}:recall:index")
}
