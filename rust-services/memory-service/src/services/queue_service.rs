//! Queue Service - Core logic for Redis queue operations
//! US#93/US#95: Memory Router Rationalization - SPEC-131

use chrono::Utc;
use redis::aio::ConnectionManager;
use redis::{AsyncCommands, Client, RedisResult};
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{debug, warn};
use uuid::Uuid;

use crate::api::queue::{JobStatusResponse, QueueStats, QueueStatsResponse};
use crate::cache::MemoryCache;

/// Service for queue operations
pub struct QueueService {
    #[allow(dead_code)] // Reserved for future caching of queue stats/job data
    cache: MemoryCache,
    connection: Option<Arc<Mutex<ConnectionManager>>>,
}

impl QueueService {
    pub fn new(cache: MemoryCache) -> Self {
        Self {
            cache,
            connection: None,
        }
    }

    /// Get or create Redis connection for queue operations
    async fn get_connection(&mut self) -> RedisResult<Arc<Mutex<ConnectionManager>>> {
        if let Some(ref conn) = self.connection {
            return Ok(Arc::clone(conn));
        }

        let redis_url = std::env::var("REDIS_URL")
            .unwrap_or_else(|_| "redis://localhost:6379".to_string());
        let client = Client::open(redis_url)?;
        let connection = Arc::new(Mutex::new(
            ConnectionManager::new(client).await?,
        ));
        self.connection = Some(Arc::clone(&connection));
        Ok(connection)
    }

    /// Enqueue a task
    pub async fn enqueue_task(
        &mut self,
        user_id: Uuid,
        task_type: &str,
        parameters: &Value,
    ) -> RedisResult<String> {
        debug!(
            user_id = %user_id,
            task_type = %task_type,
            "enqueueing task"
        );

        let job_id = Uuid::new_v4().to_string();
        let job_key = format!("queue:job:{}", job_id);

        let job_data = serde_json::json!({
            "id": job_id,
            "user_id": user_id.to_string(),
            "task_type": task_type,
            "parameters": parameters,
            "status": "queued",
            "created_at": Utc::now().to_rfc3339(),
        });

        // Store job data in Redis
        let conn = self.get_connection().await?;
        let mut conn = conn.lock().await;
        let job_data_str = serde_json::to_string(&job_data)
            .map_err(|e| {
                redis::RedisError::from((
                    redis::ErrorKind::TypeError,
                    "JSON serialization failed",
                    e.to_string(),
                ))
            })?;
        let _: () = conn.set_ex(&job_key, job_data_str, 86400).await?; // 24h TTL

        // Add to appropriate queue
        let queue_key = format!("queue:{}", task_type);
        let _: usize = conn.lpush(&queue_key, &job_id).await?;

        debug!(job_id = %job_id, "task enqueued");
        Ok(job_id)
    }

    /// Get job status
    pub async fn get_job_status(&mut self, job_id: &str) -> RedisResult<Option<JobStatusResponse>> {
        let job_key = format!("queue:job:{}", job_id);
        let conn = self.get_connection().await?;
        let mut conn = conn.lock().await;

        let job_data: Option<String> = conn.get(&job_key).await?;

        match job_data {
            Some(data) => {
                let job: Value = serde_json::from_str(&data)
                    .map_err(|e| {
                        redis::RedisError::from((
                            redis::ErrorKind::TypeError,
                            "JSON deserialization failed",
                            e.to_string(),
                        ))
                    })?;

                Ok(Some(JobStatusResponse {
                    id: job["id"].as_str().unwrap_or(job_id).to_string(),
                    status: job["status"].as_str().unwrap_or("unknown").to_string(),
                    created_at: job["created_at"].as_str().map(|s| s.to_string()),
                    started_at: job["started_at"].as_str().map(|s| s.to_string()),
                    ended_at: job["ended_at"].as_str().map(|s| s.to_string()),
                    result: job.get("result").cloned(),
                    error: job["error"].as_str().map(|s| s.to_string()),
                }))
            }
            None => Ok(None),
        }
    }

    /// Get queue statistics
    pub async fn get_queue_stats(&mut self) -> RedisResult<QueueStatsResponse> {
        let conn = self.get_connection().await?;
        let mut conn = conn.lock().await;

        let queue_types = vec![
            "default",
            "memory_processing",
            "embeddings",
            "notifications",
            "analytics",
        ];

        let mut queues = HashMap::new();
        let mut total_jobs = 0;

        for queue_type in queue_types {
            let queue_key = format!("queue:{}", queue_type);
            let length: usize = conn.llen(&queue_key).await.unwrap_or(0);

            // For a full implementation, we'd track failed/scheduled/started jobs
            // This is a simplified version
            let stats = QueueStats {
                length,
                failed_job_count: 0,
                scheduled_job_count: 0,
                started_job_count: 0,
                deferred_job_count: 0,
            };

            total_jobs += length;
            queues.insert(queue_type.to_string(), stats);
        }

        Ok(QueueStatsResponse {
            queues,
            total_jobs,
            healthy: true,
        })
    }

    /// Health check for queue system
    pub async fn health_check(&mut self) -> RedisResult<Value> {
        match self.get_queue_stats().await {
            Ok(stats) => {
                let total_failed: usize = stats
                    .queues
                    .values()
                    .map(|q| q.failed_job_count)
                    .sum();

                let total_started: usize = stats
                    .queues
                    .values()
                    .map(|q| q.started_job_count)
                    .sum();

                let status = if total_failed > 10 {
                    "degraded"
                } else if total_started > 20 {
                    "degraded"
                } else {
                    "healthy"
                };

                Ok(serde_json::json!({
                    "status": status,
                    "connected": true,
                    "queues": stats.queues.len(),
                    "total_failed_jobs": total_failed,
                    "total_started_jobs": total_started,
                    "queue_details": stats.queues,
                }))
            }
            Err(e) => {
                warn!(?e, "queue health check failed");
                Ok(serde_json::json!({
                    "status": "unhealthy",
                    "error": e.to_string(),
                    "connected": false,
                }))
            }
        }
    }
}
