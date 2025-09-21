"""
Redis Queue API Endpoints - SPEC-033
RESTful API for background task management and monitoring
"""

from typing import Any

import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from redis_queue import (
    RedisQueueManager,
    enqueue_cleanup_task,
    enqueue_memory_processing,
    enqueue_notification,
    enqueue_relevance_calculation,
    get_queue_manager,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/queue", tags=["background-tasks"])


# Request/Response models
class TaskRequest(BaseModel):
    task_type: str
    parameters: dict[str, Any]


class TaskResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    id: str
    status: str
    created_at: str | None
    started_at: str | None
    ended_at: str | None
    result: dict[str, Any] | None
    error: str | None


class QueueStatsResponse(BaseModel):
    queues: dict[str, dict[str, int]]
    total_jobs: int
    healthy: bool


@router.post("/tasks", response_model=TaskResponse)
async def enqueue_task(
    task_request: TaskRequest,
    current_user: User = Depends(get_current_user),
    queue_manager: RedisQueueManager = Depends(get_queue_manager),
):
    """Enqueue a background task"""
    try:
        task_type = task_request.task_type
        params = task_request.parameters

        job_id = None

        # Route to appropriate task based on type
        if task_type == "memory_processing":
            memory_id = params.get("memory_id")
            text = params.get("text")
            metadata = params.get("metadata", {})

            if not memory_id or not text:
                raise HTTPException(
                    status_code=400,
                    detail="memory_id and text are required for memory processing",
                )

            job_id = enqueue_memory_processing(memory_id, text, metadata)

        elif task_type == "relevance_calculation":
            user_id = params.get("user_id", current_user.user_id)
            context_id = params.get("context_id")

            job_id = enqueue_relevance_calculation(user_id, context_id)

        elif task_type == "notification":
            user_id = params.get("user_id", current_user.user_id)
            notification_type = params.get("notification_type")
            data = params.get("data", {})

            if not notification_type:
                raise HTTPException(
                    status_code=400, detail="notification_type is required"
                )

            job_id = enqueue_notification(user_id, notification_type, data)

        elif task_type == "cleanup":
            # Only allow admins to run cleanup tasks
            if not current_user.is_admin:
                raise HTTPException(
                    status_code=403, detail="Admin access required for cleanup tasks"
                )

            days_old = params.get("days_old", 90)
            job_id = enqueue_cleanup_task(days_old)

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown task type: {task_type}"
            )

        if not job_id:
            raise HTTPException(status_code=500, detail="Failed to enqueue task")

        logger.info(
            "Task enqueued successfully",
            task_type=task_type,
            job_id=job_id,
            user_id=current_user.user_id,
        )

        return TaskResponse(
            job_id=job_id,
            status="enqueued",
            message=f"Task {task_type} enqueued successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to enqueue task", task_type=task_request.task_type, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    queue_manager: RedisQueueManager = Depends(get_queue_manager),
):
    """Get status of a background job"""
    try:
        job_info = queue_manager.get_job_status(job_id)

        if "error" in job_info:
            raise HTTPException(status_code=404, detail=job_info["error"])

        return JobStatusResponse(
            id=job_info["id"],
            status=job_info["status"],
            created_at=job_info["created_at"],
            started_at=job_info["started_at"],
            ended_at=job_info["ended_at"],
            result=job_info["result"],
            error=job_info["exc_info"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    current_user: User = Depends(get_current_user),
    queue_manager: RedisQueueManager = Depends(get_queue_manager),
):
    """Get queue statistics"""
    try:
        stats = queue_manager.get_queue_stats()

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        # Calculate total jobs across all queues
        total_jobs = sum(
            queue_stats["length"]
            + queue_stats["failed_job_count"]
            + queue_stats["scheduled_job_count"]
            + queue_stats["started_job_count"]
            + queue_stats["deferred_job_count"]
            for queue_stats in stats.values()
        )

        return QueueStatsResponse(
            queues=stats, total_jobs=total_jobs, healthy=queue_manager.is_connected
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get queue stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/{memory_id}/process")
async def process_memory_async(
    memory_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
    current_user: User = Depends(get_current_user),
):
    """Enqueue memory processing task (convenience endpoint)"""
    try:
        job_id = enqueue_memory_processing(memory_id, text, metadata or {})

        if not job_id:
            raise HTTPException(
                status_code=500, detail="Failed to enqueue memory processing"
            )

        return {
            "job_id": job_id,
            "memory_id": memory_id,
            "status": "processing",
            "message": "Memory processing started in background",
        }

    except Exception as e:
        logger.error("Failed to process memory", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relevance/calculate")
async def calculate_relevance_async(
    context_id: str | None = None, current_user: User = Depends(get_current_user)
):
    """Enqueue relevance calculation task (convenience endpoint)"""
    try:
        job_id = enqueue_relevance_calculation(current_user.user_id, context_id)

        if not job_id:
            raise HTTPException(
                status_code=500, detail="Failed to enqueue relevance calculation"
            )

        return {
            "job_id": job_id,
            "user_id": current_user.user_id,
            "context_id": context_id,
            "status": "calculating",
            "message": "Relevance calculation started in background",
        }

    except Exception as e:
        logger.error(
            "Failed to calculate relevance", user_id=current_user.user_id, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def queue_health(queue_manager: RedisQueueManager = Depends(get_queue_manager)):
    """Health check for Redis Queue system"""
    try:
        stats = queue_manager.get_queue_stats()

        if "error" in stats:
            return {"status": "unhealthy", "error": stats["error"], "connected": False}

        # Check for any failed jobs
        total_failed = sum(
            queue_stats["failed_job_count"] for queue_stats in stats.values()
        )

        # Check for stuck jobs (high started count might indicate issues)
        total_started = sum(
            queue_stats["started_job_count"] for queue_stats in stats.values()
        )

        status = "healthy"
        if total_failed > 10:  # Threshold for concern
            status = "degraded"
        elif total_started > 20:  # Many jobs stuck processing
            status = "degraded"

        return {
            "status": status,
            "connected": queue_manager.is_connected,
            "queues": len(stats),
            "total_failed_jobs": total_failed,
            "total_started_jobs": total_started,
            "queue_details": stats,
        }

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "connected": False}
