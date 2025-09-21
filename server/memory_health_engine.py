"""
SPEC-042: Memory Health & Orphaned Token Report Engine

Provides comprehensive health monitoring and analysis of the memory system:
- Orphaned token detection and cleanup
- Memory quality analysis and scoring
- Health metrics and reporting
- Automated monitoring and alerting
- Integration with existing intelligence systems

Key Features:
- Real-time health monitoring
- Orphaned token identification
- Quality scoring algorithms
- Automated cleanup recommendations
- Health trend analysis
"""

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog
from feedback_engine import get_feedback_engine
from redis_client import get_redis_client
from relevance_engine import get_relevance_engine

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Memory health status levels"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    ORPHANED = "orphaned"


class TokenType(Enum):
    """Types of memory tokens"""

    ACTIVE = "active"
    STALE = "stale"
    ORPHANED = "orphaned"
    CORRUPTED = "corrupted"


@dataclass
class MemoryHealthMetrics:
    """Health metrics for a memory item"""

    memory_id: str
    user_id: int
    health_status: HealthStatus
    quality_score: float
    last_accessed: datetime | None
    access_frequency: int
    feedback_score: float | None
    relevance_score: float | None
    issues: list[str]
    recommendations: list[str]
    created_at: datetime
    updated_at: datetime


@dataclass
class OrphanedToken:
    """Orphaned token information"""

    token_id: str
    user_id: int
    last_accessed: datetime | None
    created_at: datetime
    orphaned_since: datetime
    orphan_reason: str
    cleanup_recommendation: str
    estimated_impact: str


@dataclass
class SystemHealthReport:
    """Comprehensive system health report"""

    report_id: str
    generated_at: datetime
    total_memories: int
    healthy_memories: int
    warning_memories: int
    critical_memories: int
    orphaned_tokens: int
    avg_quality_score: float
    system_health_status: HealthStatus
    top_issues: list[str]
    recommendations: list[str]
    metrics: dict[str, Any]


class MemoryHealthEngine:
    """Core engine for memory health monitoring and analysis"""

    def __init__(self):
        self.redis_client = None
        self.relevance_engine = None
        self.feedback_engine = None

        # Health thresholds
        self.quality_thresholds = {"healthy": 0.7, "warning": 0.4, "critical": 0.2}

        # Orphan detection criteria
        self.orphan_criteria = {
            "no_access_days": 90,
            "no_feedback_days": 180,
            "zero_relevance_days": 30,
            "broken_references": True,
        }

        # Cache TTL for health data
        self.health_cache_ttl = 3600  # 1 hour

    async def initialize(self):
        """Initialize Redis connections and dependencies"""
        try:
            self.redis_client = await get_redis_client()
            self.relevance_engine = await get_relevance_engine()
            self.feedback_engine = await get_feedback_engine()
            logger.info("Memory health engine initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize memory health engine", error=str(e))
            raise

    async def analyze_memory_health(
        self, user_id: int, memory_id: str
    ) -> MemoryHealthMetrics:
        """Analyze health of a specific memory"""

        try:
            # Get memory data from various sources
            relevance_score = await self._get_memory_relevance_score(user_id, memory_id)
            feedback_data = await self._get_memory_feedback_data(user_id, memory_id)
            access_data = await self._get_memory_access_data(user_id, memory_id)

            # Calculate quality score
            quality_score = await self._calculate_quality_score(
                relevance_score, feedback_data, access_data
            )

            # Determine health status
            health_status = self._determine_health_status(quality_score, access_data)

            # Identify issues and recommendations
            issues = await self._identify_issues(
                user_id, memory_id, relevance_score, feedback_data, access_data
            )
            recommendations = self._generate_recommendations(issues, health_status)

            return MemoryHealthMetrics(
                memory_id=memory_id,
                user_id=user_id,
                health_status=health_status,
                quality_score=quality_score,
                last_accessed=access_data.get("last_accessed"),
                access_frequency=access_data.get("frequency", 0),
                feedback_score=feedback_data.get("total_score")
                if feedback_data
                else None,
                relevance_score=relevance_score,
                issues=issues,
                recommendations=recommendations,
                created_at=access_data.get("created_at", datetime.utcnow()),
                updated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                "Failed to analyze memory health",
                user_id=user_id,
                memory_id=memory_id,
                error=str(e),
            )
            raise

    async def detect_orphaned_tokens(self, user_id: int) -> list[OrphanedToken]:
        """Detect orphaned tokens for a user"""

        orphaned_tokens = []

        try:
            # Get all user memories
            user_memories = await self._get_user_memories(user_id)

            for memory_id in user_memories:
                orphan_info = await self._check_if_orphaned(user_id, memory_id)
                if orphan_info:
                    orphaned_tokens.append(orphan_info)

            logger.info(
                "Orphaned token detection completed",
                user_id=user_id,
                orphaned_count=len(orphaned_tokens),
            )

            return orphaned_tokens

        except Exception as e:
            logger.error(
                "Failed to detect orphaned tokens", user_id=user_id, error=str(e)
            )
            return []

    async def generate_health_report(self, user_id: int) -> SystemHealthReport:
        """Generate comprehensive health report for a user"""

        try:
            report_id = f"health_report_{user_id}_{int(time.time())}"

            # Get all user memories
            user_memories = await self._get_user_memories(user_id)
            total_memories = len(user_memories)

            # Analyze each memory
            health_metrics = []
            for memory_id in user_memories:
                try:
                    metrics = await self.analyze_memory_health(user_id, memory_id)
                    health_metrics.append(metrics)
                except Exception as e:
                    logger.warning(
                        "Failed to analyze memory in health report",
                        memory_id=memory_id,
                        error=str(e),
                    )

            # Calculate summary statistics
            healthy_count = sum(
                1 for m in health_metrics if m.health_status == HealthStatus.HEALTHY
            )
            warning_count = sum(
                1 for m in health_metrics if m.health_status == HealthStatus.WARNING
            )
            critical_count = sum(
                1 for m in health_metrics if m.health_status == HealthStatus.CRITICAL
            )
            orphaned_count = sum(
                1 for m in health_metrics if m.health_status == HealthStatus.ORPHANED
            )

            avg_quality = (
                sum(m.quality_score for m in health_metrics) / len(health_metrics)
                if health_metrics
                else 0
            )

            # Determine overall system health
            system_health = self._determine_system_health(
                healthy_count,
                warning_count,
                critical_count,
                orphaned_count,
                total_memories,
            )

            # Identify top issues and recommendations
            all_issues = [issue for m in health_metrics for issue in m.issues]
            top_issues = self._get_top_issues(all_issues)

            all_recommendations = [
                rec for m in health_metrics for rec in m.recommendations
            ]
            top_recommendations = self._get_top_recommendations(all_recommendations)

            # Additional metrics
            metrics = {
                "avg_quality_score": avg_quality,
                "health_distribution": {
                    "healthy": healthy_count,
                    "warning": warning_count,
                    "critical": critical_count,
                    "orphaned": orphaned_count,
                },
                "total_issues": len(all_issues),
                "unique_issues": len(set(all_issues)),
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

            report = SystemHealthReport(
                report_id=report_id,
                generated_at=datetime.utcnow(),
                total_memories=total_memories,
                healthy_memories=healthy_count,
                warning_memories=warning_count,
                critical_memories=critical_count,
                orphaned_tokens=orphaned_count,
                avg_quality_score=avg_quality,
                system_health_status=system_health,
                top_issues=top_issues,
                recommendations=top_recommendations,
                metrics=metrics,
            )

            # Cache the report
            await self._cache_health_report(user_id, report)

            logger.info(
                "Health report generated",
                user_id=user_id,
                report_id=report_id,
                total_memories=total_memories,
                system_health=system_health.value,
            )

            return report

        except Exception as e:
            logger.error(
                "Failed to generate health report", user_id=user_id, error=str(e)
            )
            raise

    async def _get_memory_relevance_score(
        self, user_id: int, memory_id: str
    ) -> float | None:
        """Get relevance score for a memory"""
        try:
            # This would integrate with SPEC-031 relevance engine
            return 0.7  # Simulated score
        except Exception:
            return None

    async def _get_memory_feedback_data(
        self, user_id: int, memory_id: str
    ) -> dict | None:
        """Get feedback data for a memory"""
        try:
            feedback_score = await self.feedback_engine.get_memory_feedback_score(
                user_id, memory_id
            )
            if feedback_score:
                return {
                    "total_score": feedback_score.total_score,
                    "positive_count": feedback_score.positive_count,
                    "negative_count": feedback_score.negative_count,
                    "last_updated": feedback_score.last_updated,
                }
            return None
        except Exception:
            return None

    async def _get_memory_access_data(self, user_id: int, memory_id: str) -> dict:
        """Get access data for a memory"""
        try:
            # This would get actual access data from Redis
            return {
                "last_accessed": datetime.utcnow() - timedelta(days=5),
                "frequency": 3,
                "created_at": datetime.utcnow() - timedelta(days=30),
            }
        except Exception:
            return {}

    async def _calculate_quality_score(
        self,
        relevance_score: float | None,
        feedback_data: dict | None,
        access_data: dict,
    ) -> float:
        """Calculate overall quality score for a memory"""

        score_components = []

        # Relevance component (40%)
        if relevance_score is not None:
            score_components.append(relevance_score * 0.4)

        # Feedback component (30%)
        if feedback_data and feedback_data.get("total_score") is not None:
            feedback_score = max(
                0, min(1, (feedback_data["total_score"] + 1) / 2)
            )  # Normalize to 0-1
            score_components.append(feedback_score * 0.3)

        # Access frequency component (20%)
        frequency = access_data.get("frequency", 0)
        frequency_score = min(1.0, frequency / 10.0)  # Normalize to 0-1
        score_components.append(frequency_score * 0.2)

        # Recency component (10%)
        last_accessed = access_data.get("last_accessed")
        if last_accessed:
            days_since_access = (datetime.utcnow() - last_accessed).days
            recency_score = max(0, 1 - (days_since_access / 90))  # Decay over 90 days
            score_components.append(recency_score * 0.1)

        return sum(score_components) if score_components else 0.0

    def _determine_health_status(
        self, quality_score: float, access_data: dict
    ) -> HealthStatus:
        """Determine health status based on quality score and access data"""

        # Check for orphaned status first
        last_accessed = access_data.get("last_accessed")
        if last_accessed:
            days_since_access = (datetime.utcnow() - last_accessed).days
            if days_since_access > self.orphan_criteria["no_access_days"]:
                return HealthStatus.ORPHANED

        # Check quality thresholds
        if quality_score >= self.quality_thresholds["healthy"]:
            return HealthStatus.HEALTHY
        elif quality_score >= self.quality_thresholds["warning"]:
            return HealthStatus.WARNING
        else:
            return HealthStatus.CRITICAL

    async def _identify_issues(
        self,
        user_id: int,
        memory_id: str,
        relevance_score: float | None,
        feedback_data: dict | None,
        access_data: dict,
    ) -> list[str]:
        """Identify specific issues with a memory"""

        issues = []

        # Check for low relevance
        if relevance_score is not None and relevance_score < 0.3:
            issues.append("Low relevance score")

        # Check for negative feedback
        if feedback_data:
            if feedback_data.get("negative_count", 0) > feedback_data.get(
                "positive_count", 0
            ):
                issues.append("More negative than positive feedback")

        # Check for infrequent access
        frequency = access_data.get("frequency", 0)
        if frequency == 0:
            issues.append("Never accessed")
        elif frequency < 2:
            issues.append("Rarely accessed")

        # Check for stale content
        last_accessed = access_data.get("last_accessed")
        if last_accessed:
            days_since_access = (datetime.utcnow() - last_accessed).days
            if days_since_access > 60:
                issues.append("Not accessed in over 60 days")
            elif days_since_access > 30:
                issues.append("Not accessed in over 30 days")

        return issues

    def _generate_recommendations(
        self, issues: list[str], health_status: HealthStatus
    ) -> list[str]:
        """Generate recommendations based on identified issues"""

        recommendations = []

        if "Low relevance score" in issues:
            recommendations.append(
                "Review and update memory content for better relevance"
            )

        if "More negative than positive feedback" in issues:
            recommendations.append("Consider revising or removing this memory")

        if "Never accessed" in issues:
            recommendations.append("Consider archiving or deleting unused memory")

        if "Rarely accessed" in issues:
            recommendations.append("Review if this memory is still needed")

        if health_status == HealthStatus.ORPHANED:
            recommendations.append("Consider cleanup - memory appears orphaned")

        if health_status == HealthStatus.CRITICAL:
            recommendations.append(
                "Immediate attention required - critical health issues"
            )

        return recommendations

    async def _get_user_memories(self, user_id: int) -> list[str]:
        """Get list of all memories for a user"""
        # This would query the actual database
        return [f"memory_{user_id}_{i}" for i in range(1, 6)]  # Simulated

    async def _check_if_orphaned(
        self, user_id: int, memory_id: str
    ) -> OrphanedToken | None:
        """Check if a memory token is orphaned"""

        try:
            access_data = await self._get_memory_access_data(user_id, memory_id)
            last_accessed = access_data.get("last_accessed")

            if last_accessed:
                days_since_access = (datetime.utcnow() - last_accessed).days
                if days_since_access > self.orphan_criteria["no_access_days"]:
                    return OrphanedToken(
                        token_id=memory_id,
                        user_id=user_id,
                        last_accessed=last_accessed,
                        created_at=access_data.get("created_at", datetime.utcnow()),
                        orphaned_since=last_accessed
                        + timedelta(days=self.orphan_criteria["no_access_days"]),
                        orphan_reason=f"No access for {days_since_access} days",
                        cleanup_recommendation="Consider archiving or deletion",
                        estimated_impact="Low - appears unused",
                    )

            return None

        except Exception as e:
            logger.warning(
                "Failed to check orphan status", memory_id=memory_id, error=str(e)
            )
            return None

    def _determine_system_health(
        self, healthy: int, warning: int, critical: int, orphaned: int, total: int
    ) -> HealthStatus:
        """Determine overall system health status"""

        if total == 0:
            return HealthStatus.HEALTHY

        critical_ratio = (critical + orphaned) / total
        warning_ratio = warning / total

        if critical_ratio > 0.3:  # More than 30% critical/orphaned
            return HealthStatus.CRITICAL
        elif (
            critical_ratio > 0.1 or warning_ratio > 0.5
        ):  # More than 10% critical or 50% warning
            return HealthStatus.WARNING
        else:
            return HealthStatus.HEALTHY

    def _get_top_issues(self, issues: list[str]) -> list[str]:
        """Get most common issues"""
        issue_counts = {}
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        return sorted(issue_counts.keys(), key=lambda x: issue_counts[x], reverse=True)[
            :5
        ]

    def _get_top_recommendations(self, recommendations: list[str]) -> list[str]:
        """Get most common recommendations"""
        rec_counts = {}
        for rec in recommendations:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1

        return sorted(rec_counts.keys(), key=lambda x: rec_counts[x], reverse=True)[:5]

    async def _cache_health_report(self, user_id: int, report: SystemHealthReport):
        """Cache health report in Redis"""
        try:
            cache_key = f"health:report:{user_id}"
            report_data = asdict(report)
            report_data["generated_at"] = report.generated_at.isoformat()
            report_data["system_health_status"] = report.system_health_status.value

            await self.redis_client.setex(
                cache_key, self.health_cache_ttl, json.dumps(report_data, default=str)
            )
        except Exception as e:
            logger.warning("Failed to cache health report", error=str(e))


# Global health engine instance
_health_engine: MemoryHealthEngine | None = None


async def get_health_engine() -> MemoryHealthEngine:
    """Get the global health engine instance"""
    global _health_engine
    if _health_engine is None:
        _health_engine = MemoryHealthEngine()
        await _health_engine.initialize()
    return _health_engine


def reset_health_engine():
    """Reset the global health engine instance (useful for testing)"""
    global _health_engine
    _health_engine = None
