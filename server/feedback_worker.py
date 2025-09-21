"""
SPEC-040: Feedback Loop System - Background Worker

Background worker for processing feedback events asynchronously.
Integrates with Redis Queue for scalable feedback processing.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import structlog

from feedback_engine import (
    get_feedback_engine,
    FeedbackEvent,
    FeedbackType,
    FeedbackSentiment
)

logger = structlog.get_logger(__name__)


async def process_feedback_event(event_data: Dict[str, Any]):
    """
    Background task to process a feedback event.
    
    This function is called by the Redis Queue worker to process
    feedback events asynchronously.
    """
    try:
        # Reconstruct feedback event from data
        event = FeedbackEvent(
            event_id=event_data["event_id"],
            user_id=event_data["user_id"],
            memory_id=event_data["memory_id"],
            feedback_type=FeedbackType(event_data["feedback_type"]),
            sentiment=FeedbackSentiment(event_data["sentiment"]),
            value=event_data["value"],
            metadata=event_data["metadata"],
            timestamp=datetime.fromisoformat(event_data["timestamp"]),
            context_id=event_data.get("context_id"),
            query=event_data.get("query"),
            session_id=event_data.get("session_id")
        )
        
        # Get feedback engine and process event
        engine = await get_feedback_engine()
        await engine.process_feedback_event(event)
        
        logger.info(
            "Feedback event processed successfully",
            event_id=event.event_id,
            user_id=event.user_id,
            memory_id=event.memory_id
        )
        
    except Exception as e:
        logger.error(
            "Failed to process feedback event",
            event_data=event_data,
            error=str(e)
        )
        raise


async def batch_process_feedback_events(event_data_list: list):
    """
    Process multiple feedback events in batch for efficiency.
    """
    try:
        engine = await get_feedback_engine()
        
        processed_count = 0
        failed_count = 0
        
        for event_data in event_data_list:
            try:
                # Reconstruct and process event
                event = FeedbackEvent(
                    event_id=event_data["event_id"],
                    user_id=event_data["user_id"],
                    memory_id=event_data["memory_id"],
                    feedback_type=FeedbackType(event_data["feedback_type"]),
                    sentiment=FeedbackSentiment(event_data["sentiment"]),
                    value=event_data["value"],
                    metadata=event_data["metadata"],
                    timestamp=datetime.fromisoformat(event_data["timestamp"]),
                    context_id=event_data.get("context_id"),
                    query=event_data.get("query"),
                    session_id=event_data.get("session_id")
                )
                
                await engine.process_feedback_event(event)
                processed_count += 1
                
            except Exception as e:
                logger.error(
                    "Failed to process individual feedback event in batch",
                    event_id=event_data.get("event_id"),
                    error=str(e)
                )
                failed_count += 1
        
        logger.info(
            "Batch feedback processing completed",
            total_events=len(event_data_list),
            processed=processed_count,
            failed=failed_count
        )
        
    except Exception as e:
        logger.error(
            "Failed to process feedback event batch",
            batch_size=len(event_data_list),
            error=str(e)
        )
        raise


async def cleanup_old_feedback_data(days_old: int = 30):
    """
    Background task to clean up old feedback data.
    
    This helps maintain Redis memory usage by removing
    old feedback events and scores.
    """
    try:
        engine = await get_feedback_engine()
        
        # This would implement cleanup logic
        # For now, just log the cleanup attempt
        logger.info(
            "Feedback data cleanup initiated",
            days_old=days_old
        )
        
        # Implementation would:
        # 1. Scan for old feedback events
        # 2. Remove events older than threshold
        # 3. Update aggregated scores
        # 4. Log cleanup statistics
        
    except Exception as e:
        logger.error(
            "Failed to cleanup old feedback data",
            error=str(e)
        )
        raise


async def recalculate_memory_scores(user_id: int, memory_ids: list = None):
    """
    Background task to recalculate memory feedback scores.
    
    This can be used for:
    - Periodic score recalculation
    - Fixing corrupted scores
    - Applying new scoring algorithms
    """
    try:
        engine = await get_feedback_engine()
        
        logger.info(
            "Memory score recalculation initiated",
            user_id=user_id,
            memory_count=len(memory_ids) if memory_ids else "all"
        )
        
        # Implementation would:
        # 1. Get all feedback events for user/memories
        # 2. Recalculate aggregated scores
        # 3. Update relevance engine scores
        # 4. Log recalculation statistics
        
    except Exception as e:
        logger.error(
            "Failed to recalculate memory scores",
            user_id=user_id,
            error=str(e)
        )
        raise


# Register worker functions with Redis Queue
FEEDBACK_WORKER_FUNCTIONS = {
    "process_feedback_event": process_feedback_event,
    "batch_process_feedback_events": batch_process_feedback_events,
    "cleanup_old_feedback_data": cleanup_old_feedback_data,
    "recalculate_memory_scores": recalculate_memory_scores,
}


def register_feedback_workers(queue_manager):
    """Register feedback worker functions with the queue manager"""
    for func_name, func in FEEDBACK_WORKER_FUNCTIONS.items():
        queue_manager.register_worker(func_name, func)
    
    logger.info(
        "Feedback worker functions registered",
        functions=list(FEEDBACK_WORKER_FUNCTIONS.keys())
    )
