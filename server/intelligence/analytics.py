"""
Graph Analytics Engine
Real-time graph intelligence and insights generation
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import (
    KnowledgeGap,
    SuggestedConnection,
    TeamContext,
    TeamInsights,
    TrendingTopic,
)

logger = logging.getLogger(__name__)


class GraphAnalyticsEngine:
    """
    Real-time graph analytics for knowledge insights and trend detection

    Features:
    - Knowledge gap detection and analysis
    - Trending topic identification
    - Automated connection suggestions
    - Team intelligence insights
    - Real-time analytics dashboard data
    """

    def __init__(self, config: Dict):
        """Initialize instance."""
        self.config = config
        self.analytics_cache = {}
        self.trend_history = defaultdict(list)
        self.knowledge_graph = {}
        self.team_analytics = {}

    async def detect_knowledge_gaps(
        self,
        team_context: TeamContext,
        analysis_window: timedelta = timedelta(days=30),
        confidence_threshold: float = 0.7,
    ) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps in team's domain using graph analysis

        Args:
            team_context: Team context for gap analysis
            analysis_window: Time window for analysis
            confidence_threshold: Minimum confidence for gap detection

        Returns:
            List of identified knowledge gaps with suggestions
        """
        try:
            # Analyze team's knowledge coverage
            knowledge_coverage = await self._analyze_team_knowledge_coverage(team_context, analysis_window)

            # Identify gaps based on query patterns and failed searches
            query_gaps = await self._analyze_query_patterns(team_context, analysis_window)

            # Compare with industry/organizational knowledge standards
            standard_gaps = await self._compare_with_knowledge_standards(team_context, knowledge_coverage)

            # Analyze collaboration patterns to identify missing expertise
            collaboration_gaps = await self._analyze_collaboration_gaps(team_context, analysis_window)

            # Combine and score all identified gaps
            all_gaps = query_gaps + standard_gaps + collaboration_gaps
            knowledge_gaps = []

            for gap_data in all_gaps:
                if gap_data["confidence"] >= confidence_threshold:
                    # Find potential sources for filling the gap
                    suggested_sources = await self._find_gap_sources(gap_data["topic_area"], team_context)

                    # Identify potential experts
                    potential_experts = await self._identify_topic_experts(
                        gap_data["topic_area"], team_context.organization
                    )

                    gap = KnowledgeGap(
                        gap_id=f"gap_{team_context.team_id}_{hash(gap_data['topic_area'])}",
                        team_id=team_context.team_id,
                        topic_area=gap_data["topic_area"],
                        confidence=gap_data["confidence"],
                        suggested_sources=suggested_sources,
                        urgency_score=gap_data.get("urgency", 0.5),
                        related_queries=gap_data.get("related_queries", []),
                        potential_experts=potential_experts,
                    )

                    knowledge_gaps.append(gap)

            # Sort by urgency and confidence
            knowledge_gaps.sort(key=lambda g: (g.urgency_score * g.confidence), reverse=True)

            logger.info(f"Detected {len(knowledge_gaps)} knowledge gaps for team {team_context.team_id}")

            return knowledge_gaps

        except Exception as e:
            logger.error(f"Knowledge gap detection failed: {e}")
            return []

    async def identify_trending_topics(
        self,
        scope: str = "organization",
        time_window: str = "24h",
        min_growth_rate: float = 0.2,
    ) -> List[TrendingTopic]:
        """
        Identify trending topics based on memory access and creation patterns

        Args:
            scope: Analysis scope ('team', 'department', 'organization')
            time_window: Time window for trend analysis ('1h', '24h', '7d', '30d')
            min_growth_rate: Minimum growth rate to consider as trending

        Returns:
            List of trending topics with growth metrics
        """
        try:
            # Parse time window
            window_delta = self._parse_time_window(time_window)
            start_time = datetime.utcnow() - window_delta

            # Get memory access and creation data
            access_data = await self._get_memory_access_data(scope, start_time)
            creation_data = await self._get_memory_creation_data(scope, start_time)

            # Extract topics from memory data
            topic_activity = await self._extract_topic_activity(access_data, creation_data)

            # Calculate trend scores and growth rates
            trending_topics = []

            for topic, activity_data in topic_activity.items():
                # Calculate growth rate compared to previous period
                growth_rate = await self._calculate_topic_growth_rate(topic, activity_data, window_delta)

                if growth_rate >= min_growth_rate:
                    # Calculate trend score based on multiple factors
                    trend_score = self._calculate_trend_score(activity_data, growth_rate, window_delta)

                    # Get related memories and teams
                    related_memories = activity_data.get("memory_ids", [])
                    teams_involved = activity_data.get("teams", [])

                    # Find peak activity timestamp
                    peak_timestamp = self._find_peak_activity_time(activity_data)

                    trending_topic = TrendingTopic(
                        topic=topic,
                        trend_score=trend_score,
                        growth_rate=growth_rate,
                        related_memories=related_memories[:10],  # Limit to top 10
                        teams_involved=teams_involved,
                        time_window=time_window,
                        peak_timestamp=peak_timestamp,
                    )

                    trending_topics.append(trending_topic)

            # Sort by trend score
            trending_topics.sort(key=lambda t: t.trend_score, reverse=True)

            # Update trend history for future analysis
            self._update_trend_history(trending_topics, time_window)

            logger.info(f"Identified {len(trending_topics)} trending topics in {time_window}")

            return trending_topics[:20]  # Return top 20 trends

        except Exception as e:
            logger.error(f"Trending topic identification failed: {e}")
            return []

    async def suggest_memory_connections(
        self, memory_id: str, context: Optional[Dict] = None, max_suggestions: int = 10
    ) -> List[SuggestedConnection]:
        """
        Suggest connections between memories based on graph analysis

        Args:
            memory_id: Source memory ID for connection suggestions
            context: Optional context for connection relevance
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested connections with reasoning
        """
        try:
            # Get memory data and existing connections
            memory_data = await self._get_memory_data(memory_id)
            existing_connections = await self._get_existing_connections(memory_id)

            # Find candidate memories for connections
            candidates = await self._find_connection_candidates(memory_data, existing_connections, context)

            suggestions = []

            for candidate in candidates:
                # Calculate connection strength and type
                connection_analysis = await self._analyze_potential_connection(memory_data, candidate, context)

                if connection_analysis["confidence"] >= 0.6:
                    suggestion = SuggestedConnection(
                        source_memory=memory_id,
                        target_memory=candidate["id"],
                        connection_type=connection_analysis["type"],
                        confidence=connection_analysis["confidence"],
                        reasoning=connection_analysis["reasoning"],
                        potential_value=connection_analysis["value"],
                    )

                    suggestions.append(suggestion)

            # Sort by potential value and confidence
            suggestions.sort(key=lambda s: s.potential_value * s.confidence, reverse=True)

            return suggestions[:max_suggestions]

        except Exception as e:
            logger.error(f"Connection suggestion failed: {e}")
            return []

    async def generate_team_insights(
        self, team_id: str, analysis_period: timedelta = timedelta(days=30)
    ) -> TeamInsights:
        """
        Generate comprehensive intelligence insights for a team

        Args:
            team_id: Team identifier
            analysis_period: Period for insight analysis

        Returns:
            Comprehensive team insights with recommendations
        """
        try:
            datetime.utcnow() - analysis_period

            # Get team context
            team_context = await self._get_team_context(team_id)

            # Analyze knowledge coverage across different domains
            knowledge_coverage = await self._analyze_comprehensive_knowledge_coverage(team_context, analysis_period)

            # Analyze collaboration patterns
            collaboration_patterns = await self._analyze_team_collaboration_patterns(team_context, analysis_period)

            # Get trending topics for the team
            trending_topics = await self.identify_trending_topics(scope=f"team:{team_id}", time_window="30d")

            # Detect knowledge gaps
            knowledge_gaps = await self.detect_knowledge_gaps(team_context, analysis_period)

            # Calculate productivity metrics
            productivity_metrics = await self._calculate_team_productivity_metrics(team_context, analysis_period)

            # Generate actionable recommendations
            recommendations = await self._generate_team_recommendations(
                team_context,
                knowledge_coverage,
                collaboration_patterns,
                trending_topics,
                knowledge_gaps,
                productivity_metrics,
            )

            insights = TeamInsights(
                team_id=team_id,
                knowledge_coverage=knowledge_coverage,
                collaboration_patterns=collaboration_patterns,
                trending_topics=trending_topics[:5],  # Top 5 trends
                knowledge_gaps=knowledge_gaps[:5],  # Top 5 gaps
                productivity_metrics=productivity_metrics,
                recommendations=recommendations,
            )

            # Cache insights for dashboard
            self.team_analytics[team_id] = insights

            logger.info(f"Generated insights for team {team_id}")

            return insights

        except Exception as e:
            logger.error(f"Team insight generation failed: {e}")
            return TeamInsights(
                team_id=team_id,
                knowledge_coverage={},
                collaboration_patterns={},
                trending_topics=[],
                knowledge_gaps=[],
                productivity_metrics={},
                recommendations=[f"Error generating insights: {str(e)}"],
            )

    async def get_real_time_analytics_data(
        self, dashboard_type: str = "overview", filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get real-time analytics data for dashboard display

        Args:
            dashboard_type: Type of dashboard ('overview', 'team', 'trends', 'gaps')
            filters: Optional filters for data selection

        Returns:
            Real-time analytics data formatted for dashboard
        """
        try:
            datetime.utcnow()

            if dashboard_type == "overview":
                return await self._get_overview_analytics(filters)
            elif dashboard_type == "team":
                team_id = filters.get("team_id") if filters else None
                return await self._get_team_analytics(team_id)
            elif dashboard_type == "trends":
                return await self._get_trending_analytics(filters)
            elif dashboard_type == "gaps":
                return await self._get_knowledge_gap_analytics(filters)
            else:
                return {"error": f"Unknown dashboard type: {dashboard_type}"}

        except Exception as e:
            logger.error(f"Real-time analytics data retrieval failed: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def _analyze_team_knowledge_coverage(
        self, team_context: TeamContext, analysis_window: timedelta
    ) -> Dict[str, float]:
        """Analyze team's knowledge coverage across different domains"""
        # This would analyze the team's memories, expertise areas, and activity
        # to determine coverage across different knowledge domains

        coverage = {}

        # Analyze based on team specializations
        for specialization in team_context.specializations:
            # Calculate coverage score for this specialization
            coverage[specialization] = await self._calculate_domain_coverage(
                team_context.team_id, specialization, analysis_window
            )

        # Add general coverage areas
        general_areas = ["technical", "process", "business", "communication"]
        for area in general_areas:
            if area not in coverage:
                coverage[area] = await self._calculate_domain_coverage(team_context.team_id, area, analysis_window)

        return coverage

    async def _analyze_query_patterns(self, team_context: TeamContext, analysis_window: timedelta) -> List[Dict]:
        """Analyze query patterns to identify knowledge gaps"""
        gaps = []

        # This would analyze failed searches, repeated queries, and
        # queries with low satisfaction scores to identify gaps

        # Simulated gap detection based on query patterns
        common_failed_topics = [
            "deployment_procedures",
            "debugging_techniques",
            "api_documentation",
            "testing_strategies",
        ]

        for topic in common_failed_topics:
            gap_data = {
                "topic_area": topic,
                "confidence": 0.8,
                "urgency": 0.7,
                "related_queries": [f"How to {topic.replace('_', ' ')}?"],
                "source": "query_analysis",
            }
            gaps.append(gap_data)

        return gaps

    def _parse_time_window(self, time_window: str) -> timedelta:
        """Parse time window string to timedelta"""
        if time_window.endswith("h"):
            hours = int(time_window[:-1])
            return timedelta(hours=hours)
        elif time_window.endswith("d"):
            days = int(time_window[:-1])
            return timedelta(days=days)
        elif time_window.endswith("w"):
            weeks = int(time_window[:-1])
            return timedelta(weeks=weeks)
        else:
            return timedelta(hours=24)  # Default to 24 hours

    def _calculate_trend_score(self, activity_data: Dict, growth_rate: float, window_delta: timedelta) -> float:
        """Calculate trend score based on activity and growth"""
        base_score = growth_rate

        # Boost score based on absolute activity volume
        activity_volume = activity_data.get("total_activity", 0)
        volume_boost = min(activity_volume / 100, 0.5)  # Cap at 0.5

        # Boost score based on team diversity
        team_count = len(activity_data.get("teams", []))
        diversity_boost = min(team_count / 10, 0.3)  # Cap at 0.3

        # Recency boost - more recent activity scores higher
        recency_boost = 0.2 if window_delta <= timedelta(hours=24) else 0.1

        trend_score = base_score + volume_boost + diversity_boost + recency_boost

        return min(trend_score, 1.0)  # Cap at 1.0

    async def _generate_team_recommendations(
        self,
        team_context: TeamContext,
        knowledge_coverage: Dict[str, float],
        collaboration_patterns: Dict[str, Any],
        trending_topics: List[TrendingTopic],
        knowledge_gaps: List[KnowledgeGap],
        productivity_metrics: Dict[str, float],
    ) -> List[str]:
        """Generate actionable recommendations for the team"""
        recommendations = []

        # Knowledge coverage recommendations
        low_coverage_areas = [area for area, score in knowledge_coverage.items() if score < 0.4]
        if low_coverage_areas:
            recommendations.append(f"Consider building expertise in: {', '.join(low_coverage_areas[:3])}")

        # Knowledge gap recommendations
        if knowledge_gaps:
            top_gap = knowledge_gaps[0]
            recommendations.append(
                f"Priority knowledge gap: {top_gap.topic_area} - " f"consider training or expert consultation"
            )

        # Trending topic recommendations
        if trending_topics:
            top_trend = trending_topics[0]
            recommendations.append(
                f"Trending topic opportunity: {top_trend.topic} - "
                f"consider creating content or expertise in this area"
            )

        # Collaboration recommendations
        collab_score = collaboration_patterns.get("external_collaboration_score", 0.5)
        if collab_score < 0.3:
            recommendations.append("Consider increasing collaboration with other teams to share knowledge")

        # Productivity recommendations
        knowledge_reuse = productivity_metrics.get("knowledge_reuse_rate", 0.5)
        if knowledge_reuse < 0.4:
            recommendations.append("Improve knowledge documentation and sharing to increase reuse")

        return recommendations[:5]  # Return top 5 recommendations
