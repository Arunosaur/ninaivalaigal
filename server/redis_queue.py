"""
Redis Queue (RQ) Manager for Async Task Processing - SPEC-033
Handles background tasks, memory processing, and async operations
"""

import os
from datetime import datetime
from typing import Any

import redis
import structlog

try:
    from rq import Job, Queue
except ImportError:
    # Fallback for RQ compatibility issues
    Job = None
    Queue = None

logger = structlog.get_logger(__name__)


class RedisQueueManager:
    """Redis Queue manager for background task processing"""

    def __init__(self):
        self.redis_conn = None
        self.queues = {}
        self.rq_available = Job is not None and Queue is not None
        self._connected = False

    def connect(self):
        """Initialize Redis connection for RQ"""
        if not self.rq_available:
            logger.warning("RQ not available, queue operations will be disabled")
            return False

        try:
            redis_url = os.getenv("REDIS_URL") or os.getenv("NINAIVALAIGAL_REDIS_URL")

            if not redis_url:
                # Fallback to individual components
                host = os.getenv("REDIS_HOST", "localhost")
                port = int(os.getenv("REDIS_PORT", "6379"))
                password = os.getenv("REDIS_PASSWORD", "nina_redis_dev_password")
                db = int(os.getenv("REDIS_DB", "0"))

                self.redis_conn = redis.Redis(
                    host=host,
                    port=port,
                    password=password,
                    db=db,
                    decode_responses=True,
                )
            else:
                self.redis_conn = redis.from_url(redis_url, decode_responses=True)

            # Test connection
            self.redis_conn.ping()
            self._connected = True

            # Initialize default queues
            self.queues = {
                "default": Queue("default", connection=self.redis_conn),
                "memory_processing": Queue(
                    "memory_processing", connection=self.redis_conn
                ),
                "embeddings": Queue("embeddings", connection=self.redis_conn),
                "notifications": Queue("notifications", connection=self.redis_conn),
                "analytics": Queue("analytics", connection=self.redis_conn),
            }

            logger.info(
                "Redis Queue connected successfully", queues=list(self.queues.keys())
            )

        except Exception as e:
            logger.error("Failed to connect to Redis Queue", error=str(e))
            self._connected = False
            raise

    def disconnect(self):
        """Close Redis Queue connection"""
        if self.redis_conn:
            self.redis_conn.close()
            self._connected = False
            logger.info("Redis Queue disconnected")

    @property
    def is_connected(self) -> bool:
        """Check if Redis Queue is connected"""
        return self._connected and self.redis_conn is not None

    def enqueue_task(
        self,
        queue_name: str,
        func,
        *args,
        job_timeout: int = 300,
        result_ttl: int = 3600,
        **kwargs,
    ) -> str | None:
        """Enqueue a background task"""
        if not self.is_connected:
            logger.error("Cannot enqueue task - Redis Queue not connected")
            return None

        try:
            queue = self.queues.get(queue_name, self.queues["default"])
            job = queue.enqueue(
                func, *args, job_timeout=job_timeout, result_ttl=result_ttl, **kwargs
            )

            logger.info(
                "Task enqueued",
                queue=queue_name,
                job_id=job.id,
                function=func.__name__ if hasattr(func, "__name__") else str(func),
            )

            return job.id

        except Exception as e:
            logger.error("Failed to enqueue task", queue=queue_name, error=str(e))
            return None

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        """Get job status and result"""
        if not self.is_connected:
            return {"error": "Redis Queue not connected"}

        try:
            job = Job.fetch(job_id, connection=self.redis_conn)

            return {
                "id": job.id,
                "status": job.get_status(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result,
                "exc_info": job.exc_info,
                "meta": job.meta,
            }

        except Exception as e:
            logger.error("Failed to get job status", job_id=job_id, error=str(e))
            return {"error": str(e)}

    def get_queue_stats(self) -> dict[str, Any]:
        """Get statistics for all queues"""
        if not self.is_connected:
            return {"error": "Redis Queue not connected"}

        try:
            stats = {}

            for name, queue in self.queues.items():
                stats[name] = {
                    "length": len(queue),
                    "failed_job_count": queue.failed_job_registry.count,
                    "scheduled_job_count": queue.scheduled_job_registry.count,
                    "started_job_count": queue.started_job_registry.count,
                    "deferred_job_count": queue.deferred_job_registry.count,
                }

            return stats

        except Exception as e:
            logger.error("Failed to get queue stats", error=str(e))
            return {"error": str(e)}


# Background task functions for common operations
def process_memory_embedding(
    memory_id: str, text: str, metadata: dict[str, Any] = None
):
    """Background task: Process memory embedding"""
    logger.info("Processing memory embedding", memory_id=memory_id)

    try:
        # Simulate embedding processing
        import time

        time.sleep(2)  # Simulate processing time

        # In real implementation, this would:
        # 1. Generate embeddings using AI model
        # 2. Store embeddings in vector database
        # 3. Update memory metadata
        # 4. Trigger relevance score calculation

        result = {
            "memory_id": memory_id,
            "embedding_dimensions": 1536,  # Example for OpenAI embeddings
            "processed_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        logger.info(
            "Memory embedding processed successfully",
            memory_id=memory_id,
            result=result,
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to process memory embedding", memory_id=memory_id, error=str(e)
        )
        raise


def calculate_memory_relevance_scores(user_id: str, context_id: str = None):
    """Background task: Calculate relevance scores for memories"""
    logger.info(
        "Calculating memory relevance scores", user_id=user_id, context_id=context_id
    )

    try:
        # Simulate relevance calculation
        import time

        time.sleep(3)  # Simulate processing time

        # In real implementation, this would:
        # 1. Fetch user's memories
        # 2. Calculate similarity scores
        # 3. Apply temporal decay
        # 4. Store scores in Redis cache
        # 5. Update memory rankings

        result = {
            "user_id": user_id,
            "context_id": context_id,
            "memories_processed": 150,  # Example count
            "scores_updated": 150,
            "processing_time_seconds": 3.2,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info(
            "Memory relevance scores calculated", user_id=user_id, result=result
        )

        return result

    except Exception as e:
        logger.error(
            "Failed to calculate relevance scores", user_id=user_id, error=str(e)
        )
        raise


def send_notification(user_id: str, notification_type: str, data: dict[str, Any]):
    """Background task: Send user notification"""
    logger.info("Sending notification", user_id=user_id, type=notification_type)

    try:
        # Simulate notification sending
        import time

        time.sleep(1)  # Simulate processing time

        # In real implementation, this would:
        # 1. Format notification message
        # 2. Send via email/SMS/push notification
        # 3. Log notification history
        # 4. Update user preferences

        result = {
            "user_id": user_id,
            "notification_type": notification_type,
            "sent_at": datetime.utcnow().isoformat(),
            "data": data,
        }

        logger.info("Notification sent successfully", user_id=user_id, result=result)

        return result

    except Exception as e:
        logger.error("Failed to send notification", user_id=user_id, error=str(e))
        raise


def cleanup_expired_memories(days_old: int = 90):
    """Background task: Cleanup expired or orphaned memories"""
    logger.info("Starting memory cleanup", days_old=days_old)

    try:
        # Simulate cleanup process
        import time

        time.sleep(5)  # Simulate processing time

        # In real implementation, this would:
        # 1. Find memories older than threshold
        # 2. Check for orphaned tokens
        # 3. Archive or delete expired data
        # 4. Update statistics
        # 5. Clear related cache entries

        result = {
            "memories_checked": 1000,
            "memories_archived": 50,
            "memories_deleted": 10,
            "cache_entries_cleared": 75,
            "processing_time_seconds": 5.1,
            "processed_at": datetime.utcnow().isoformat(),
        }

        logger.info("Memory cleanup completed", result=result)

        return result

    except Exception as e:
        logger.error("Failed to cleanup memories", error=str(e))
        raise


# Global queue manager instance
queue_manager = RedisQueueManager()


def get_queue_manager() -> RedisQueueManager:
    """Dependency injection for queue manager"""
    if not queue_manager.is_connected:
        queue_manager.connect()
    return queue_manager


# Convenience functions for common tasks
def enqueue_memory_processing(
    memory_id: str, text: str, metadata: dict[str, Any] = None
) -> str | None:
    """Enqueue memory processing task"""
    return queue_manager.enqueue_task(
        "memory_processing",
        process_memory_embedding,
        memory_id,
        text,
        metadata,
        job_timeout=600,  # 10 minutes
    )


def enqueue_relevance_calculation(user_id: str, context_id: str = None) -> str | None:
    """Enqueue relevance score calculation"""
    return queue_manager.enqueue_task(
        "analytics",
        calculate_memory_relevance_scores,
        user_id,
        context_id,
        job_timeout=900,  # 15 minutes
    )


def enqueue_notification(
    user_id: str, notification_type: str, data: dict[str, Any]
) -> str | None:
    """Enqueue notification sending"""
    return queue_manager.enqueue_task(
        "notifications",
        send_notification,
        user_id,
        notification_type,
        data,
        job_timeout=60,  # 1 minute
    )


def enqueue_cleanup_task(days_old: int = 90) -> str | None:
    """Enqueue memory cleanup task"""
    return queue_manager.enqueue_task(
        "default",
        cleanup_expired_memories,
        days_old,
        job_timeout=1800,  # 30 minutes
    )
