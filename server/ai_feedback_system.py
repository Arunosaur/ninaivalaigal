"""
SPEC-040: Feedback Loop for AI Context
AI feedback loops, context improvement, and learning system
"""

import json
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback that can be collected"""

    MEMORY_RELEVANCE = "memory_relevance"
    CONTEXT_QUALITY = "context_quality"
    SUGGESTION_ACCURACY = "suggestion_accuracy"
    RESPONSE_HELPFULNESS = "response_helpfulness"
    MEMORY_INJECTION = "memory_injection"


class FeedbackValue(str, Enum):
    """Feedback values (positive/negative/neutral)"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FeedbackEvent(BaseModel):
    """Individual feedback event"""

    event_id: str
    user_id: str
    feedback_type: FeedbackType
    feedback_value: FeedbackValue
    context: Dict[str, Any]
    timestamp: datetime
    memory_ids: Optional[List[str]] = None
    session_id: Optional[str] = None
    confidence_score: Optional[float] = None


class LearningPattern(BaseModel):
    """Learned pattern from feedback analysis"""

    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    evidence_count: int
    last_updated: datetime
    parameters: Dict[str, Any]


class ContextImprovement(BaseModel):
    """Context improvement suggestion"""

    improvement_id: str
    improvement_type: str
    description: str
    priority: str  # high, medium, low
    estimated_impact: float
    implementation_status: str
    created_at: datetime


class AIFeedbackSystem:
    """
    Advanced AI feedback system that learns from user interactions
    to continuously improve context quality and memory relevance.
    """

    def __init__(self, db_manager, redis_client=None):
        self.db = db_manager
        self.redis = redis_client
        self.learning_patterns = {}
        self.improvement_queue = []

    async def collect_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        feedback_value: FeedbackValue,
        context: Dict[str, Any],
        memory_ids: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
    ) -> str:
        """
        Collect feedback from user interactions.
        """
        try:
            event_id = f"fb_{int(time.time() * 1000)}_{user_id[:8]}"

            feedback_event = FeedbackEvent(
                event_id=event_id,
                user_id=user_id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                context=context,
                timestamp=datetime.utcnow(),
                memory_ids=memory_ids,
                session_id=session_id,
                confidence_score=confidence_score,
            )

            # Store feedback in database
            await self._store_feedback_event(feedback_event)

            # Cache recent feedback for real-time learning
            if self.redis:
                await self._cache_feedback(feedback_event)

            # Trigger learning analysis if enough feedback collected
            await self._trigger_learning_analysis(user_id, feedback_type)

            logger.info(
                "Feedback collected",
                event_id=event_id,
                user_id=user_id,
                feedback_type=feedback_type.value,
                feedback_value=feedback_value.value,
            )

            return event_id

        except Exception as e:
            logger.error("Failed to collect feedback", error=str(e))
            raise

    async def analyze_feedback_patterns(
        self,
        user_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        days_back: int = 30,
    ) -> List[LearningPattern]:
        """
        Analyze feedback patterns to identify learning opportunities.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get feedback data for analysis
            feedback_data = await self._get_feedback_data(
                user_id=user_id, feedback_type=feedback_type, since_date=cutoff_date
            )

            patterns = []

            # Pattern 1: Memory relevance patterns
            if not feedback_type or feedback_type == FeedbackType.MEMORY_RELEVANCE:
                relevance_patterns = await self._analyze_memory_relevance_patterns(
                    feedback_data
                )
                patterns.extend(relevance_patterns)

            # Pattern 2: Context quality patterns
            if not feedback_type or feedback_type == FeedbackType.CONTEXT_QUALITY:
                context_patterns = await self._analyze_context_quality_patterns(
                    feedback_data
                )
                patterns.extend(context_patterns)

            # Pattern 3: Temporal patterns
            temporal_patterns = await self._analyze_temporal_patterns(feedback_data)
            patterns.extend(temporal_patterns)

            # Pattern 4: User behavior patterns
            if user_id:
                behavior_patterns = await self._analyze_user_behavior_patterns(
                    user_id, feedback_data
                )
                patterns.extend(behavior_patterns)

            # Store patterns for future use
            for pattern in patterns:
                self.learning_patterns[pattern.pattern_id] = pattern
                await self._store_learning_pattern(pattern)

            logger.info(
                "Feedback patterns analyzed",
                patterns_found=len(patterns),
                user_id=user_id,
                feedback_type=feedback_type.value if feedback_type else "all",
            )

            return patterns

        except Exception as e:
            logger.error("Failed to analyze feedback patterns", error=str(e))
            raise

    async def generate_context_improvements(
        self, patterns: List[LearningPattern]
    ) -> List[ContextImprovement]:
        """
        Generate actionable context improvements based on learned patterns.
        """
        try:
            improvements = []

            for pattern in patterns:
                if pattern.confidence < 0.7:  # Skip low-confidence patterns
                    continue

                improvement = await self._pattern_to_improvement(pattern)
                if improvement:
                    improvements.append(improvement)

            # Prioritize improvements by impact
            improvements.sort(key=lambda x: x.estimated_impact, reverse=True)

            # Store improvements
            for improvement in improvements:
                await self._store_context_improvement(improvement)
                self.improvement_queue.append(improvement)

            logger.info(
                "Context improvements generated",
                improvements_count=len(improvements),
                high_priority=len([i for i in improvements if i.priority == "high"]),
            )

            return improvements

        except Exception as e:
            logger.error("Failed to generate context improvements", error=str(e))
            raise

    async def apply_learning_adjustments(
        self, user_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply learned adjustments to improve context quality.
        """
        try:
            adjusted_context = context.copy()

            # Get user-specific learning patterns
            user_patterns = await self._get_user_learning_patterns(user_id)

            # Apply memory relevance adjustments
            if "memory_relevance" in user_patterns:
                adjusted_context = await self._apply_relevance_adjustments(
                    adjusted_context, user_patterns["memory_relevance"]
                )

            # Apply context quality adjustments
            if "context_quality" in user_patterns:
                adjusted_context = await self._apply_quality_adjustments(
                    adjusted_context, user_patterns["context_quality"]
                )

            # Apply temporal adjustments
            if "temporal_preferences" in user_patterns:
                adjusted_context = await self._apply_temporal_adjustments(
                    adjusted_context, user_patterns["temporal_preferences"]
                )

            logger.debug(
                "Learning adjustments applied",
                user_id=user_id,
                adjustments_made=len(user_patterns),
            )

            return adjusted_context

        except Exception as e:
            logger.error("Failed to apply learning adjustments", error=str(e))
            return context  # Return original context on error

    async def get_feedback_insights(
        self, user_id: Optional[str] = None, days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get insights from collected feedback for analytics.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get feedback statistics
            stats = await self._get_feedback_statistics(user_id, cutoff_date)

            # Get improvement metrics
            improvements = await self._get_improvement_metrics(user_id, cutoff_date)

            # Get learning effectiveness
            effectiveness = await self._calculate_learning_effectiveness(
                user_id, cutoff_date
            )

            insights = {
                "feedback_statistics": stats,
                "improvement_metrics": improvements,
                "learning_effectiveness": effectiveness,
                "active_patterns": len(self.learning_patterns),
                "pending_improvements": len(self.improvement_queue),
                "analysis_period_days": days_back,
            }

            return insights

        except Exception as e:
            logger.error("Failed to get feedback insights", error=str(e))
            raise

    # Private helper methods

    async def _store_feedback_event(self, event: FeedbackEvent) -> None:
        """Store feedback event in database."""
        query = """
            INSERT INTO ai_feedback_events
            (event_id, user_id, feedback_type, feedback_value, context,
             timestamp, memory_ids, session_id, confidence_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """

        await self.db.execute(
            query,
            event.event_id,
            event.user_id,
            event.feedback_type.value,
            event.feedback_value.value,
            json.dumps(event.context),
            event.timestamp,
            event.memory_ids,
            event.session_id,
            event.confidence_score,
        )

    async def _cache_feedback(self, event: FeedbackEvent) -> None:
        """Cache recent feedback for real-time learning."""
        if not self.redis:
            return

        key = f"feedback:recent:{event.user_id}"
        value = json.dumps(
            {
                "event_id": event.event_id,
                "feedback_type": event.feedback_type.value,
                "feedback_value": event.feedback_value.value,
                "timestamp": event.timestamp.isoformat(),
                "context": event.context,
            }
        )

        # Store with 1-hour expiry
        await self.redis.lpush(key, value)
        await self.redis.ltrim(key, 0, 99)  # Keep last 100 events
        await self.redis.expire(key, 3600)

    async def _trigger_learning_analysis(
        self, user_id: str, feedback_type: FeedbackType
    ) -> None:
        """Trigger learning analysis if conditions are met."""
        # Check if enough feedback collected for analysis
        recent_count = await self._get_recent_feedback_count(user_id, feedback_type)

        if recent_count >= 10:  # Threshold for analysis
            # Schedule background analysis
            await self._schedule_analysis(user_id, feedback_type)

    async def _analyze_memory_relevance_patterns(
        self, feedback_data: List[Dict[str, Any]]
    ) -> List[LearningPattern]:
        """Analyze patterns in memory relevance feedback."""
        patterns = []

        # Group by memory characteristics
        relevance_data = [
            f
            for f in feedback_data
            if f.get("feedback_type") == FeedbackType.MEMORY_RELEVANCE.value
        ]

        if len(relevance_data) < 5:
            return patterns

        # Pattern: Memory age preference
        age_pattern = await self._analyze_memory_age_preference(relevance_data)
        if age_pattern:
            patterns.append(age_pattern)

        # Pattern: Content type preference
        content_pattern = await self._analyze_content_type_preference(relevance_data)
        if content_pattern:
            patterns.append(content_pattern)

        return patterns

    async def _analyze_context_quality_patterns(
        self, feedback_data: List[Dict[str, Any]]
    ) -> List[LearningPattern]:
        """Analyze patterns in context quality feedback."""
        patterns = []

        quality_data = [
            f
            for f in feedback_data
            if f.get("feedback_type") == FeedbackType.CONTEXT_QUALITY.value
        ]

        if len(quality_data) < 5:
            return patterns

        # Pattern: Context length preference
        length_pattern = await self._analyze_context_length_preference(quality_data)
        if length_pattern:
            patterns.append(length_pattern)

        return patterns

    async def _analyze_temporal_patterns(
        self, feedback_data: List[Dict[str, Any]]
    ) -> List[LearningPattern]:
        """Analyze temporal patterns in feedback."""
        patterns = []

        # Pattern: Time-of-day preferences
        time_pattern = await self._analyze_time_preferences(feedback_data)
        if time_pattern:
            patterns.append(time_pattern)

        return patterns

    async def _analyze_user_behavior_patterns(
        self, user_id: str, feedback_data: List[Dict[str, Any]]
    ) -> List[LearningPattern]:
        """Analyze user-specific behavior patterns."""
        patterns = []

        user_data = [f for f in feedback_data if f.get("user_id") == user_id]

        if len(user_data) < 10:
            return patterns

        # Pattern: User feedback consistency
        consistency_pattern = await self._analyze_feedback_consistency(user_data)
        if consistency_pattern:
            patterns.append(consistency_pattern)

        return patterns

    async def _pattern_to_improvement(
        self, pattern: LearningPattern
    ) -> Optional[ContextImprovement]:
        """Convert a learning pattern to a context improvement."""
        improvement_id = f"imp_{int(time.time())}_{pattern.pattern_id[-8:]}"

        if pattern.pattern_type == "memory_age_preference":
            return ContextImprovement(
                improvement_id=improvement_id,
                improvement_type="memory_ranking",
                description=f"Adjust memory ranking to prefer {pattern.parameters.get('preferred_age', 'recent')} memories",
                priority="high" if pattern.confidence > 0.8 else "medium",
                estimated_impact=pattern.confidence * 0.3,
                implementation_status="pending",
                created_at=datetime.utcnow(),
            )

        elif pattern.pattern_type == "context_length_preference":
            return ContextImprovement(
                improvement_id=improvement_id,
                improvement_type="context_sizing",
                description=f"Optimize context length to {pattern.parameters.get('preferred_length', 'medium')} size",
                priority="medium",
                estimated_impact=pattern.confidence * 0.2,
                implementation_status="pending",
                created_at=datetime.utcnow(),
            )

        return None

    async def _get_feedback_data(
        self,
        user_id: Optional[str] = None,
        feedback_type: Optional[FeedbackType] = None,
        since_date: datetime = None,
    ) -> List[Dict[str, Any]]:
        """Get feedback data for analysis."""
        query = "SELECT * FROM ai_feedback_events WHERE 1=1"
        params = []

        if user_id:
            query += f" AND user_id = ${len(params) + 1}"
            params.append(user_id)

        if feedback_type:
            query += f" AND feedback_type = ${len(params) + 1}"
            params.append(feedback_type.value)

        if since_date:
            query += f" AND timestamp >= ${len(params) + 1}"
            params.append(since_date)

        query += " ORDER BY timestamp DESC"

        results = await self.db.fetch_all(query, *params)

        return [dict(row) for row in results] if results else []
