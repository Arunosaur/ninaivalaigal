"""
SPEC-040: Feedback Loop System - Core Engine

Implements a comprehensive feedback loop mechanism to continuously improve
memory relevance and accuracy using implicit and explicit user feedback.

Key Features:
- Implicit feedback tracking (dwell time, click-through, navigation patterns)
- Explicit feedback collection (thumbs up/down, quality notes)
- Memory score adjustment with decay model
- Redis-backed event processing
- Integration with SPEC-031 relevance engine
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import structlog
from redis_client import get_redis_client
from redis_queue import get_queue_manager
from relevance_engine import get_relevance_engine

logger = structlog.get_logger(__name__)


class FeedbackType(Enum):
    """Types of feedback events"""

    IMPLICIT_DWELL = "implicit_dwell"
    IMPLICIT_CLICK = "implicit_click"
    IMPLICIT_NAVIGATION = "implicit_navigation"
    EXPLICIT_THUMBS_UP = "explicit_thumbs_up"
    EXPLICIT_THUMBS_DOWN = "explicit_thumbs_down"
    EXPLICIT_QUALITY_NOTE = "explicit_quality_note"


class FeedbackSentiment(Enum):
    """Feedback sentiment values"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class FeedbackEvent:
    """Feedback event data structure"""

    event_id: str
    user_id: int
    memory_id: str
    feedback_type: FeedbackType
    sentiment: FeedbackSentiment
    value: float  # Normalized feedback value (0.0 to 1.0)
    metadata: dict[str, Any]
    timestamp: datetime
    context_id: str | None = None
    query: str | None = None
    session_id: str | None = None


@dataclass
class MemoryFeedbackScore:
    """Aggregated feedback score for a memory"""

    memory_id: str
    user_id: int
    total_score: float
    positive_count: int
    negative_count: int
    implicit_score: float
    explicit_score: float
    last_updated: datetime
    decay_factor: float = 0.95  # Daily decay factor


class FeedbackEngine:
    """Core feedback loop engine for memory relevance improvement"""

    def __init__(self):
        self.redis_client = None
        self.queue_manager = None
        self.relevance_engine = None
        self.feedback_ttl = 86400 * 30  # 30 days TTL for feedback data

        # Feedback scoring weights
        self.implicit_weights = {
            FeedbackType.IMPLICIT_DWELL: 0.3,
            FeedbackType.IMPLICIT_CLICK: 0.5,
            FeedbackType.IMPLICIT_NAVIGATION: 0.2,
        }

        self.explicit_weights = {
            FeedbackType.EXPLICIT_THUMBS_UP: 1.0,
            FeedbackType.EXPLICIT_THUMBS_DOWN: -1.0,
            FeedbackType.EXPLICIT_QUALITY_NOTE: 0.8,
        }

    async def initialize(self):
        """Initialize Redis connections and dependencies"""
        try:
            self.redis_client = await get_redis_client()
            self.queue_manager = get_queue_manager()
            self.relevance_engine = get_relevance_engine()
            logger.info("Feedback engine initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize feedback engine", error=str(e))
            raise

    async def record_implicit_feedback(
        self,
        user_id: int,
        memory_id: str,
        feedback_type: FeedbackType,
        value: float,
        metadata: dict[str, Any],
        context_id: str | None = None,
        query: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Record implicit feedback event (dwell time, clicks, navigation)"""

        # Normalize implicit feedback value
        normalized_value = self._normalize_implicit_value(feedback_type, value)

        # Determine sentiment based on value
        sentiment = self._calculate_sentiment(feedback_type, normalized_value)

        # Create feedback event
        event = FeedbackEvent(
            event_id=f"fb_{int(time.time() * 1000)}_{user_id}_{memory_id}",
            user_id=user_id,
            memory_id=memory_id,
            feedback_type=feedback_type,
            sentiment=sentiment,
            value=normalized_value,
            metadata=metadata,
            timestamp=datetime.utcnow(),
            context_id=context_id,
            query=query,
            session_id=session_id,
        )

        # Store event and queue for processing
        await self._store_feedback_event(event)
        await self._queue_feedback_processing(event)

        logger.info(
            "Implicit feedback recorded",
            event_id=event.event_id,
            user_id=user_id,
            memory_id=memory_id,
            feedback_type=feedback_type.value,
            value=normalized_value,
        )

        return event.event_id

    async def record_explicit_feedback(
        self,
        user_id: int,
        memory_id: str,
        feedback_type: FeedbackType,
        sentiment: FeedbackSentiment,
        notes: str | None = None,
        context_id: str | None = None,
        query: str | None = None,
        session_id: str | None = None,
    ) -> str:
        """Record explicit feedback event (thumbs up/down, quality notes)"""

        # Calculate explicit feedback value
        value = self._calculate_explicit_value(feedback_type, sentiment)

        metadata = {"notes": notes} if notes else {}

        # Create feedback event
        event = FeedbackEvent(
            event_id=f"fb_{int(time.time() * 1000)}_{user_id}_{memory_id}",
            user_id=user_id,
            memory_id=memory_id,
            feedback_type=feedback_type,
            sentiment=sentiment,
            value=value,
            metadata=metadata,
            timestamp=datetime.utcnow(),
            context_id=context_id,
            query=query,
            session_id=session_id,
        )

        # Store event and queue for processing
        await self._store_feedback_event(event)
        await self._queue_feedback_processing(event)

        logger.info(
            "Explicit feedback recorded",
            event_id=event.event_id,
            user_id=user_id,
            memory_id=memory_id,
            feedback_type=feedback_type.value,
            sentiment=sentiment.value,
        )

        return event.event_id

    async def get_memory_feedback_score(
        self, user_id: int, memory_id: str
    ) -> MemoryFeedbackScore | None:
        """Get aggregated feedback score for a memory"""

        key = f"feedback:score:{user_id}:{memory_id}"

        try:
            score_data = await self.redis_client.get(key)
            if not score_data:
                return None

            data = json.loads(score_data)
            return MemoryFeedbackScore(
                memory_id=data["memory_id"],
                user_id=data["user_id"],
                total_score=data["total_score"],
                positive_count=data["positive_count"],
                negative_count=data["negative_count"],
                implicit_score=data["implicit_score"],
                explicit_score=data["explicit_score"],
                last_updated=datetime.fromisoformat(data["last_updated"]),
                decay_factor=data.get("decay_factor", 0.95),
            )
        except Exception as e:
            logger.error(
                "Failed to get memory feedback score",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            return None

    async def process_feedback_event(self, event: FeedbackEvent):
        """Process a feedback event and update memory scores"""

        try:
            # Get current feedback score
            current_score = await self.get_memory_feedback_score(
                event.user_id, event.memory_id
            )

            if current_score is None:
                # Create new feedback score
                current_score = MemoryFeedbackScore(
                    memory_id=event.memory_id,
                    user_id=event.user_id,
                    total_score=0.0,
                    positive_count=0,
                    negative_count=0,
                    implicit_score=0.0,
                    explicit_score=0.0,
                    last_updated=datetime.utcnow(),
                )

            # Apply time decay to existing scores
            current_score = self._apply_time_decay(current_score)

            # Update scores based on feedback type
            if event.feedback_type in self.implicit_weights:
                weight = self.implicit_weights[event.feedback_type]
                current_score.implicit_score += event.value * weight
            else:
                weight = self.explicit_weights.get(event.feedback_type, 0.5)
                current_score.explicit_score += event.value * weight

            # Update counters
            if event.sentiment == FeedbackSentiment.POSITIVE:
                current_score.positive_count += 1
            elif event.sentiment == FeedbackSentiment.NEGATIVE:
                current_score.negative_count += 1

            # Calculate total score
            current_score.total_score = (
                current_score.implicit_score + current_score.explicit_score
            )
            current_score.last_updated = datetime.utcnow()

            # Store updated score
            await self._store_feedback_score(current_score)

            # Update relevance engine with new feedback score
            await self._update_relevance_score(event, current_score)

            logger.info(
                "Feedback event processed",
                event_id=event.event_id,
                memory_id=event.memory_id,
                total_score=current_score.total_score,
            )

        except Exception as e:
            logger.error(
                "Failed to process feedback event",
                event_id=event.event_id,
                error=str(e),
            )
            raise

    def _normalize_implicit_value(
        self, feedback_type: FeedbackType, value: float
    ) -> float:
        """Normalize implicit feedback values to 0.0-1.0 range"""

        if feedback_type == FeedbackType.IMPLICIT_DWELL:
            # Dwell time in seconds, normalize to 0-1 (max 60 seconds)
            return min(value / 60.0, 1.0)
        elif feedback_type == FeedbackType.IMPLICIT_CLICK:
            # Click-through rate, already 0-1
            return min(max(value, 0.0), 1.0)
        elif feedback_type == FeedbackType.IMPLICIT_NAVIGATION:
            # Navigation score, normalize to 0-1
            return min(max(value, 0.0), 1.0)

        return 0.5  # Default neutral value

    def _calculate_sentiment(
        self, feedback_type: FeedbackType, value: float
    ) -> FeedbackSentiment:
        """Calculate sentiment based on feedback type and value"""

        if feedback_type in [FeedbackType.IMPLICIT_DWELL, FeedbackType.IMPLICIT_CLICK]:
            if value > 0.7:
                return FeedbackSentiment.POSITIVE
            elif value < 0.3:
                return FeedbackSentiment.NEGATIVE
            else:
                return FeedbackSentiment.NEUTRAL

        return FeedbackSentiment.NEUTRAL

    def _calculate_explicit_value(
        self, feedback_type: FeedbackType, sentiment: FeedbackSentiment
    ) -> float:
        """Calculate explicit feedback value"""

        if sentiment == FeedbackSentiment.POSITIVE:
            return 1.0
        elif sentiment == FeedbackSentiment.NEGATIVE:
            return 0.0
        else:
            return 0.5

    def _apply_time_decay(self, score: MemoryFeedbackScore) -> MemoryFeedbackScore:
        """Apply time-based decay to feedback scores"""

        days_since_update = (datetime.utcnow() - score.last_updated).days
        if days_since_update > 0:
            decay = score.decay_factor**days_since_update
            score.implicit_score *= decay
            score.explicit_score *= decay
            score.total_score *= decay

        return score

    async def _store_feedback_event(self, event: FeedbackEvent):
        """Store feedback event in Redis"""

        key = f"feedback:event:{event.event_id}"
        data = asdict(event)
        data["timestamp"] = event.timestamp.isoformat()
        data["feedback_type"] = event.feedback_type.value
        data["sentiment"] = event.sentiment.value

        await self.redis_client.setex(
            key, self.feedback_ttl, json.dumps(data, default=str)
        )

    async def _store_feedback_score(self, score: MemoryFeedbackScore):
        """Store feedback score in Redis"""

        key = f"feedback:score:{score.user_id}:{score.memory_id}"
        data = asdict(score)
        data["last_updated"] = score.last_updated.isoformat()

        await self.redis_client.setex(
            key, self.feedback_ttl, json.dumps(data, default=str)
        )

    async def _queue_feedback_processing(self, event: FeedbackEvent):
        """Queue feedback event for background processing"""

        try:
            self.queue_manager.enqueue(
                "process_feedback_event", event_data=asdict(event)
            )
        except Exception as e:
            logger.error(
                "Failed to queue feedback processing",
                event_id=event.event_id,
                error=str(e),
            )

    async def _update_relevance_score(
        self, event: FeedbackEvent, feedback_score: MemoryFeedbackScore
    ):
        """Update relevance engine with feedback-adjusted scores"""

        try:
            # Apply feedback boost/penalty to relevance score
            feedback_multiplier = 1.0 + (
                feedback_score.total_score * 0.2
            )  # 20% max adjustment
            feedback_multiplier = max(
                0.5, min(1.5, feedback_multiplier)
            )  # Clamp to 0.5-1.5x

            await self.relevance_engine.update_memory_feedback_score(
                user_id=event.user_id,
                memory_id=event.memory_id,
                feedback_multiplier=feedback_multiplier,
                feedback_data={
                    "total_score": feedback_score.total_score,
                    "positive_count": feedback_score.positive_count,
                    "negative_count": feedback_score.negative_count,
                    "last_feedback": event.timestamp.isoformat(),
                },
            )

        except Exception as e:
            logger.error(
                "Failed to update relevance score with feedback",
                memory_id=event.memory_id,
                error=str(e),
            )


# Global feedback engine instance
_feedback_engine: FeedbackEngine | None = None


async def get_feedback_engine() -> FeedbackEngine:
    """Get the global feedback engine instance"""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackEngine()
        await _feedback_engine.initialize()
    return _feedback_engine


def reset_feedback_engine():
    """Reset the global feedback engine instance (useful for testing)"""
    global _feedback_engine
    _feedback_engine = None
