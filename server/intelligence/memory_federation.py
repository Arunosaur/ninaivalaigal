"""
Memory Federation Engine
Cross-team memory sharing with intelligent privacy and relevance scoring
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from .models import (
    FederatedMemory,
    FederationMetrics,
    FederationResult,
    PrivacyLevel,
    SharingRule,
    TeamContext,
)

logger = logging.getLogger(__name__)


class MemoryFederationEngine:
    """
    Intelligent cross-team memory sharing with privacy-aware federation

    Features:
    - Smart relevance scoring for cross-team knowledge discovery
    - Privacy-preserving content filtering
    - Automated sharing policy enforcement
    - Real-time federation metrics and analytics
    """

    def __init__(self, config: Dict):
        """Initialize instance."""
        self.config = config
        self.sharing_rules: Dict[str, List[SharingRule]] = {}
        self.team_contexts: Dict[str, TeamContext] = {}
        self.federation_cache: Dict[str, List[FederatedMemory]] = {}
        self.metrics = FederationMetrics(
            total_federations=0,
            successful_shares=0,
            privacy_blocks=0,
            average_sharing_score=0.0,
            cross_team_discoveries=0,
            federation_latency_ms=0.0,
            user_satisfaction=0.0,
            knowledge_reuse_rate=0.0,
        )

    async def federate_memories(
        self,
        source_team: str,
        target_teams: List[str],
        memory_batch: List[Dict],
        sharing_context: Optional[Dict] = None,
    ) -> FederationResult:
        """
        Federate memories from source team to target teams with intelligent filtering

        Args:
            source_team: Source team identifier
            target_teams: List of target team identifiers
            memory_batch: Batch of memories to federate
            sharing_context: Additional context for sharing decisions

        Returns:
            FederationResult with federated memories and metadata
        """
        start_time = datetime.utcnow()

        try:
            # Get team contexts
            source_context = await self._get_team_context(source_team)
            target_contexts = {team: await self._get_team_context(team) for team in target_teams}

            # Apply sharing rules and privacy filters
            federated_memories = []
            filtered_count = 0
            privacy_violations = []

            for memory in memory_batch:
                # Check sharing eligibility
                if not await self._is_shareable(memory, source_context, target_contexts):
                    filtered_count += 1
                    continue

                # Calculate sharing scores for each target team
                for target_team in target_teams:
                    target_context = target_contexts[target_team]

                    sharing_score = await self._calculate_sharing_score(
                        memory, source_context, target_context, sharing_context
                    )

                    if sharing_score >= self.config.get("min_sharing_score", 0.6):
                        # Apply privacy filtering
                        filtered_memory = await self._apply_privacy_filters(memory, source_context, target_context)

                        if filtered_memory:
                            federated_memory = FederatedMemory(
                                memory_id=memory["id"],
                                original_team=source_team,
                                shared_with=[target_team],
                                sharing_score=sharing_score,
                                privacy_filtered=filtered_memory != memory,
                                federation_timestamp=datetime.utcnow(),
                            )
                            federated_memories.append(federated_memory)
                        else:
                            privacy_violations.append(f"Memory {memory['id']} blocked for team {target_team}")
                    else:
                        filtered_count += 1

            # Update metrics
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_federation_metrics(len(federated_memories), filtered_count, processing_time)

            return FederationResult(
                success=True,
                federated_memories=federated_memories,
                filtered_count=filtered_count,
                sharing_policies_applied=[rule.rule_id for rule in self._get_applicable_rules(source_team)],
                privacy_violations=privacy_violations,
                processing_time_ms=processing_time,
            )

        except Exception as e:
            logger.error(f"Federation failed: {e}")
            return FederationResult(
                success=False,
                federated_memories=[],
                filtered_count=len(memory_batch),
                sharing_policies_applied=[],
                privacy_violations=[f"Federation error: {str(e)}"],
            )

    async def discover_shareable_knowledge(
        self,
        team_context: TeamContext,
        query_context: Optional[Dict] = None,
        limit: int = 50,
    ) -> List[FederatedMemory]:
        """
        Discover shareable knowledge from other teams based on team context and needs

        Args:
            team_context: Context of the requesting team
            query_context: Specific query or need context
            limit: Maximum number of memories to return

        Returns:
            List of relevant federated memories from other teams
        """
        try:
            # Get potential source teams based on collaboration history and specializations
            source_teams = await self._identify_relevant_teams(team_context, query_context)

            discovered_memories = []

            for source_team in source_teams:
                # Check if federation is allowed
                if not await self._can_access_team_knowledge(team_context.team_id, source_team):
                    continue

                # Get cached federated memories or fetch new ones
                cache_key = f"{source_team}:{team_context.team_id}"
                if cache_key in self.federation_cache:
                    team_memories = self.federation_cache[cache_key]
                else:
                    team_memories = await self._fetch_team_memories(source_team, team_context)
                    self.federation_cache[cache_key] = team_memories

                # Score and filter memories based on query context
                for memory in team_memories:
                    relevance_score = await self._calculate_query_relevance(memory, team_context, query_context)

                    if relevance_score >= self.config.get("min_discovery_score", 0.5):
                        memory.sharing_score = relevance_score
                        discovered_memories.append(memory)

            # Sort by relevance and return top results
            discovered_memories.sort(key=lambda m: m.sharing_score, reverse=True)
            return discovered_memories[:limit]

        except Exception as e:
            logger.error(f"Knowledge discovery failed: {e}")
            return []

    async def _calculate_sharing_score(
        self,
        memory: Dict,
        source_context: TeamContext,
        target_context: TeamContext,
        sharing_context: Optional[Dict] = None,
    ) -> float:
        """Calculate intelligent sharing score based on multiple factors"""

        score_components = {}

        # 1. Content relevance to target team specializations
        content_relevance = await self._calculate_content_relevance(memory, target_context.specializations)
        score_components["content_relevance"] = content_relevance * 0.3

        # 2. Historical collaboration strength
        collaboration_score = source_context.collaboration_history.get(target_context.team_id, 0.0)
        score_components["collaboration"] = collaboration_score * 0.2

        # 3. Organizational proximity (department, access level)
        org_proximity = self._calculate_organizational_proximity(source_context, target_context)
        score_components["org_proximity"] = org_proximity * 0.2

        # 4. Memory freshness and quality
        freshness_score = self._calculate_memory_freshness(memory)
        quality_score = memory.get("quality_score", 0.5)
        score_components["quality"] = (freshness_score * 0.5 + quality_score * 0.5) * 0.15

        # 5. Sharing context boost (if specific need/query provided)
        if sharing_context:
            context_boost = await self._calculate_context_boost(memory, sharing_context)
            score_components["context_boost"] = context_boost * 0.15

        # Calculate weighted final score
        final_score = sum(score_components.values())

        # Log scoring breakdown for transparency
        logger.debug(f"Sharing score for memory {memory.get('id')}: {score_components}")

        return min(final_score, 1.0)  # Cap at 1.0

    async def _apply_privacy_filters(
        self, memory: Dict, source_context: TeamContext, target_context: TeamContext
    ) -> Optional[Dict]:
        """Apply privacy filters to memory content based on sharing policies"""

        # Get memory privacy level
        privacy_level = PrivacyLevel(memory.get("privacy_level", "internal"))

        # Check if target team can access this privacy level
        if not self._can_access_privacy_level(target_context, privacy_level):
            return None

        # Apply content filtering based on sharing rules
        filtered_memory = memory.copy()

        # Remove sensitive fields based on privacy level
        if privacy_level == PrivacyLevel.CONFIDENTIAL:
            # Only share metadata for confidential content
            filtered_memory = {
                "id": memory["id"],
                "title": memory.get("title", ""),
                "summary": memory.get("summary", "")[:100] + "...",
                "tags": memory.get("tags", []),
                "created_at": memory.get("created_at"),
                "team": source_context.team_name,
            }
        elif privacy_level == PrivacyLevel.RESTRICTED:
            # Remove specific sensitive fields
            sensitive_fields = [
                "personal_data",
                "credentials",
                "api_keys",
                "internal_urls",
            ]
            for field in sensitive_fields:
                filtered_memory.pop(field, None)

        # Apply team-specific filtering rules
        team_rules = self._get_team_sharing_rules(source_context.team_id, target_context.team_id)
        for rule in team_rules:
            filtered_memory = self._apply_content_filters(filtered_memory, rule.content_filters)

        return filtered_memory

    async def _get_team_context(self, team_id: str) -> TeamContext:
        """Get or create team context with caching"""
        if team_id in self.team_contexts:
            return self.team_contexts[team_id]

        # Fetch team context from database or create default
        # This would integrate with your team management system
        context = TeamContext(
            team_id=team_id,
            team_name=f"Team {team_id}",
            department="Engineering",  # Default - should be fetched
            organization="Ninaivalaigal",
            access_level=3,  # Default access level
            specializations=[],  # Should be populated from team profile
            collaboration_history={},  # Should be calculated from interaction history
        )

        self.team_contexts[team_id] = context
        return context

    def _update_federation_metrics(self, successful: int, filtered: int, processing_time: float):
        """Update federation performance metrics"""
        self.metrics.total_federations += successful + filtered
        self.metrics.successful_shares += successful
        self.metrics.privacy_blocks += filtered

        # Update average processing time (exponential moving average)
        alpha = 0.1
        self.metrics.federation_latency_ms = alpha * processing_time + (1 - alpha) * self.metrics.federation_latency_ms

        # Update average sharing score
        if self.metrics.total_federations > 0:
            self.metrics.average_sharing_score = self.metrics.successful_shares / self.metrics.total_federations

    async def get_federation_metrics(self) -> FederationMetrics:
        """Get current federation performance metrics"""
        return self.metrics

    async def _calculate_content_relevance(self, memory: Dict, specializations: List[str]) -> float:
        """Calculate how relevant memory content is to team specializations"""
        if not specializations:
            return 0.5  # Default relevance if no specializations defined

        memory_tags = memory.get("tags", [])
        memory_content = memory.get("content", "") + " " + memory.get("title", "")

        relevance_score = 0.0

        # Tag-based relevance
        tag_matches = len(set(memory_tags) & set(specializations))
        if memory_tags:
            relevance_score += (tag_matches / len(memory_tags)) * 0.6

        # Content-based relevance (simple keyword matching - could be enhanced with NLP)
        content_matches = sum(1 for spec in specializations if spec.lower() in memory_content.lower())
        if specializations:
            relevance_score += (content_matches / len(specializations)) * 0.4

        return min(relevance_score, 1.0)

    def _calculate_organizational_proximity(self, source: TeamContext, target: TeamContext) -> float:
        """Calculate organizational proximity between teams"""
        proximity_score = 0.0

        # Same organization
        if source.organization == target.organization:
            proximity_score += 0.4

        # Same department
        if source.department == target.department:
            proximity_score += 0.3

        # Similar access levels
        access_diff = abs(source.access_level - target.access_level)
        access_similarity = max(0, 1 - (access_diff / 5))  # Normalize to 0-1
        proximity_score += access_similarity * 0.3

        return min(proximity_score, 1.0)

    def _calculate_memory_freshness(self, memory: Dict) -> float:
        """Calculate memory freshness score based on creation/update time"""
        created_at = memory.get("created_at")
        if not created_at:
            return 0.5  # Default if no timestamp

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        age_days = (datetime.utcnow() - created_at).days

        # Exponential decay: fresh memories score higher
        freshness = max(0, 1 - (age_days / 365))  # Decay over 1 year
        return freshness
