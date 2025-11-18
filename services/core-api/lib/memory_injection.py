#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-036: Memory Injection Rules
Smart memory injection, context rules, and AI integration
"""

import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from memory_injection_validation import (
    MemoryInjectionRuleValidator,
    RuleConflictError,
    RuleExecutionError,
    RuleValidationError,
)
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class InjectionTrigger(str, Enum):
    """Types of injection triggers"""

    CONTEXT_MATCH = "context_match"
    KEYWORD_PRESENCE = "keyword_presence"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    USER_PATTERN = "user_pattern"
    TIME_BASED = "time_based"
    LOCATION_BASED = "location_based"
    ACTIVITY_BASED = "activity_based"


class InjectionStrategy(str, Enum):
    """Memory injection strategies"""

    IMMEDIATE = "immediate"
    CONTEXTUAL = "contextual"
    PROACTIVE = "proactive"
    REACTIVE = "reactive"
    BACKGROUND = "background"


class InjectionPriority(str, Enum):
    """Priority levels for memory injection"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"


class InjectionRule(BaseModel):
    """Individual memory injection rule"""

    rule_id: str
    name: str
    description: str
    trigger: InjectionTrigger
    strategy: InjectionStrategy
    priority: InjectionPriority
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class InjectionContext(BaseModel):
    """Context for memory injection analysis"""

    user_id: str
    session_id: Optional[str] = None
    current_activity: Optional[str] = None
    location_context: Dict[str, Any] = {}
    temporal_context: Dict[str, Any] = {}
    semantic_context: Dict[str, Any] = {}
    user_state: Dict[str, Any] = {}
    environment: Dict[str, Any] = {}


class InjectionCandidate(BaseModel):
    """Memory candidate for injection"""

    memory_id: str
    relevance_score: float
    injection_reason: str
    rule_id: str
    confidence: float
    urgency: float
    context_match: Dict[str, Any]
    suggested_timing: str
    metadata: Dict[str, Any] = {}


class MemoryInjectionEngine:
    """
    Advanced memory injection engine that uses AI and context analysis
    to intelligently inject relevant memories at optimal times.
    """

    def __init__(
        self,
        db_manager,
        redis_client=None,
        feedback_system=None,
        suggestions_system=None,
    ):
        """Initialize instance."""
        self.db = db_manager
        self.redis = redis_client
        self.feedback_system = feedback_system
        self.suggestions_system = suggestions_system

        # Injection rules cache
        self.active_rules = {}
        self.rule_performance = {}

        # Context analysis weights
        self.context_weights = {
            "semantic_similarity": 0.3,
            "temporal_relevance": 0.2,
            "user_pattern_match": 0.25,
            "activity_context": 0.15,
            "location_context": 0.1,
        }

    async def analyze_injection_opportunities(
        self, context: InjectionContext, max_candidates: int = 10
    ) -> List[InjectionCandidate]:
        """Analyze current context and identify memory injection opportunities."""
        try:
            start_time = time.time()

            # Get active injection rules for user
            active_rules = await self._get_active_rules(context.user_id)

            candidates = []

            # Analyze each rule against current context
            for rule in active_rules:
                rule_candidates = await self._evaluate_rule(rule, context)
                candidates.extend(rule_candidates)

            # Score and rank candidates
            scored_candidates = await self._score_injection_candidates(candidates, context)

            # Filter by relevance threshold and limit
            filtered_candidates = [c for c in scored_candidates if c.relevance_score >= 0.3][:max_candidates]

            # Cache results for performance
            if self.redis:
                await self._cache_injection_analysis(context, filtered_candidates)

            processing_time = (time.time() - start_time) * 1000

            logger.info(
                "Memory injection analysis completed",
                user_id=context.user_id,
                candidates_found=len(filtered_candidates),
                rules_evaluated=len(active_rules),
                processing_time_ms=processing_time,
            )

            return filtered_candidates

        except Exception as e:
            logger.error("Failed to analyze injection opportunities", error=str(e))
            raise

    async def inject_memories(
        self,
        context: InjectionContext,
        strategy: InjectionStrategy = InjectionStrategy.CONTEXTUAL,
        max_injections: int = 5,
    ) -> List[Dict[str, Any]]:
        """Execute memory injection based on analysis and strategy with error handling."""
        try:
            # Validate context
            context_dict = context.dict()
            is_valid, error = MemoryInjectionRuleValidator.validate_rule_execution_context(context_dict)
            if not is_valid:
                logger.warning("Invalid execution context", user_id=context.user_id, error=error)
                raise RuleExecutionError(f"Invalid execution context: {error}", rule_id=None)

            # Get injection candidates
            candidates = await self.analyze_injection_opportunities(context, max_candidates=max_injections * 2)

            # Filter by strategy
            strategy_candidates = await self._filter_by_strategy(candidates, strategy)

            # Execute injections with error handling
            injected_memories = []
            failed_injections = []
            for candidate in strategy_candidates[:max_injections]:
                try:
                    injection_result = await self._execute_injection(candidate, context)
                    if injection_result:
                        injected_memories.append(injection_result)
                except Exception as e:
                    logger.warning(
                        "Failed to execute injection for candidate",
                        memory_id=candidate.memory_id,
                        rule_id=candidate.rule_id,
                        error=str(e),
                    )
                    failed_injections.append({"candidate": candidate.memory_id, "error": str(e)})
                    # Continue with other injections instead of failing entirely

            # Track injection performance
            try:
                await self._track_injection_performance(injected_memories, context)
            except Exception as e:
                logger.warning("Failed to track injection performance", error=str(e))
                # Don't fail the entire operation if tracking fails

            logger.info(
                "Memory injection executed",
                user_id=context.user_id,
                strategy=strategy.value,
                injections_made=len(injected_memories),
                failed_count=len(failed_injections),
            )

            # If all injections failed, raise an error
            if len(injected_memories) == 0 and len(strategy_candidates) > 0:
                error_msg = f"All {len(strategy_candidates)} injection attempts failed"
                if failed_injections:
                    error_msg += f". First error: {failed_injections[0]['error']}"
                raise RuleExecutionError(error_msg, rule_id=None)

            return injected_memories

        except RuleExecutionError:
            # Re-raise execution errors as-is
            raise
        except Exception as e:
            logger.error("Failed to inject memories", error=str(e), user_id=context.user_id)
            raise RuleExecutionError(f"Failed to inject memories: {str(e)}", rule_id=None)

    async def create_injection_rule(self, user_id: str, rule_data: Dict[str, Any]) -> InjectionRule:
        """Create a new memory injection rule with comprehensive validation."""
        try:
            # Validate rule data
            validation_errors = MemoryInjectionRuleValidator.validate_rule_data(rule_data)
            if validation_errors:
                error_message = "Rule validation failed:\n" + "\n".join(f"  - {err}" for err in validation_errors)
                logger.warning("Rule validation failed", user_id=user_id, errors=validation_errors)
                raise RuleValidationError(error_message)

            rule_id = f"rule_{int(time.time())}_{user_id[:8]}"

            rule = InjectionRule(
                rule_id=rule_id,
                name=rule_data["name"],
                description=rule_data.get("description", ""),
                trigger=InjectionTrigger(rule_data["trigger"]),
                strategy=InjectionStrategy(rule_data["strategy"]),
                priority=InjectionPriority(rule_data["priority"]),
                conditions=rule_data.get("conditions", {}),
                actions=rule_data.get("actions", {}),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Check for rule conflicts with existing rules
            existing_rules = await self._get_active_rules(user_id)
            conflicts = MemoryInjectionRuleValidator.detect_rule_conflicts(rule, existing_rules)
            if conflicts:
                conflicting_rule_ids = [c[0].rule_id for c in conflicts]
                conflict_messages = [c[1] for c in conflicts]
                error_message = "Rule conflicts detected:\n" + "\n".join(f"  - {msg}" for msg in conflict_messages)
                logger.warning(
                    "Rule conflicts detected",
                    user_id=user_id,
                    rule_id=rule_id,
                    conflicting_rules=conflicting_rule_ids,
                )
                raise RuleConflictError(error_message, conflicting_rule_ids)

            # Store rule in database
            await self._store_injection_rule(user_id, rule)

            # Update cache
            if user_id not in self.active_rules:
                self.active_rules[user_id] = []
            self.active_rules[user_id].append(rule)

            logger.info(
                "Injection rule created",
                user_id=user_id,
                rule_id=rule_id,
                trigger=rule.trigger.value,
            )

            return rule

        except (RuleValidationError, RuleConflictError):
            # Re-raise validation/conflict errors as-is
            raise
        except Exception as e:
            logger.error("Failed to create injection rule", error=str(e), user_id=user_id)
            raise RuleExecutionError(f"Failed to create injection rule: {str(e)}", rule_id=None)

    async def get_injection_analytics(self, user_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Get analytics about memory injection performance."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            # Get injection statistics
            injection_stats = await self._get_injection_statistics(user_id, cutoff_date)

            # Get rule performance
            rule_performance = await self._get_rule_performance(user_id, cutoff_date)

            # Get user feedback on injections
            injection_feedback = await self._get_injection_feedback(user_id, cutoff_date)

            analytics = {
                "total_injections": injection_stats.get("total_injections", 0),
                "successful_injections": injection_stats.get("successful_injections", 0),
                "success_rate": injection_stats.get("success_rate", 0.0),
                "average_relevance_score": injection_stats.get("avg_relevance", 0.0),
                "rule_performance": rule_performance,
                "user_feedback": injection_feedback,
                "top_triggers": injection_stats.get("top_triggers", []),
                "analysis_period_days": days_back,
            }

            return analytics

        except Exception as e:
            logger.error("Failed to get injection analytics", error=str(e))
            raise

    # Private helper methods

    async def _get_active_rules(self, user_id: str) -> List[InjectionRule]:
        """Get active injection rules for user."""
        try:
            # Check cache first
            if user_id in self.active_rules:
                return self.active_rules[user_id]

            # Load from database
            query = """
                SELECT rule_id, name, description, trigger_type, strategy, priority,
                       conditions, actions, created_at, updated_at
                FROM memory_injection_rules
                WHERE user_id = $1 AND is_active = TRUE
                ORDER BY priority DESC, created_at DESC
            """

            results = await self.db.fetch_all(query, user_id)

            rules = []
            for row in results:
                rule = InjectionRule(
                    rule_id=row[0],
                    name=row[1],
                    description=row[2],
                    trigger=InjectionTrigger(row[3]),
                    strategy=InjectionStrategy(row[4]),
                    priority=InjectionPriority(row[5]),
                    conditions=row[6],
                    actions=row[7],
                    created_at=row[8],
                    updated_at=row[9],
                )
                rules.append(rule)

            # Cache rules
            self.active_rules[user_id] = rules

            return rules

        except Exception as e:
            logger.error("Failed to get active rules", error=str(e))
            return []

    async def _evaluate_rule(self, rule: InjectionRule, context: InjectionContext) -> List[InjectionCandidate]:
        """Evaluate a rule against current context with error handling."""
        try:
            candidates = []

            # Check if rule conditions are met
            if not await self._check_rule_conditions(rule, context):
                return candidates

            # Get potential memories based on rule trigger
            try:
                if rule.trigger == InjectionTrigger.CONTEXT_MATCH:
                    memories = await self._find_context_matching_memories(rule, context)
                elif rule.trigger == InjectionTrigger.KEYWORD_PRESENCE:
                    memories = await self._find_keyword_matching_memories(rule, context)
                elif rule.trigger == InjectionTrigger.SEMANTIC_SIMILARITY:
                    memories = await self._find_semantically_similar_memories(rule, context)
                elif rule.trigger == InjectionTrigger.USER_PATTERN:
                    memories = await self._find_pattern_matching_memories(rule, context)
                elif rule.trigger == InjectionTrigger.TIME_BASED:
                    memories = await self._find_time_based_memories(rule, context)
                else:
                    logger.warning("Unknown trigger type", rule_id=rule.rule_id, trigger=rule.trigger.value)
                    memories = []
            except Exception as e:
                logger.error(
                    "Failed to find memories for rule",
                    rule_id=rule.rule_id,
                    trigger=rule.trigger.value,
                    error=str(e),
                )
                # Return empty list on error, don't fail entire injection
                memories = []

            # Create candidates from found memories
            for memory_data in memories:
                try:
                    candidate = InjectionCandidate(
                        memory_id=memory_data["id"],
                        relevance_score=memory_data.get("relevance_score", 0.5),
                        injection_reason=f"Rule: {rule.name} ({rule.trigger.value})",
                        rule_id=rule.rule_id,
                        confidence=memory_data.get("confidence", 0.7),
                        urgency=self._calculate_urgency(rule, memory_data),
                        context_match=memory_data.get("context_match", {}),
                        suggested_timing=rule.strategy.value,
                        metadata={"rule_trigger": rule.trigger.value},
                    )
                    candidates.append(candidate)
                except Exception as e:
                    logger.warning(
                        "Failed to create candidate from memory",
                        rule_id=rule.rule_id,
                        memory_id=memory_data.get("id"),
                        error=str(e),
                    )
                    # Skip this memory, continue with others
                    continue

            return candidates

        except Exception as e:
            logger.error("Failed to evaluate rule", rule_id=rule.rule_id, error=str(e))
            # Return empty list on error to prevent breaking entire injection process
            return []

    async def _score_injection_candidates(
        self, candidates: List[InjectionCandidate], context: InjectionContext
    ) -> List[InjectionCandidate]:
        """Score and rank injection candidates."""
        try:
            for candidate in candidates:
                # Base score from relevance
                score = candidate.relevance_score * 0.4

                # Add confidence factor
                score += candidate.confidence * 0.2

                # Add urgency factor
                score += candidate.urgency * 0.2

                # Add context match quality
                context_quality = await self._assess_context_quality(candidate, context)
                score += context_quality * 0.2

                # Update candidate score
                candidate.relevance_score = min(1.0, score)

            # Sort by score
            candidates.sort(key=lambda x: x.relevance_score, reverse=True)

            return candidates

        except Exception as e:
            logger.error("Failed to score injection candidates", error=str(e))
            return candidates

    async def _execute_injection(
        self, candidate: InjectionCandidate, context: InjectionContext
    ) -> Optional[Dict[str, Any]]:
        """Execute memory injection for a candidate."""
        try:
            # Get memory details
            memory = await self._get_memory_details(candidate.memory_id)
            if not memory:
                return None

            # Create injection record
            injection_record = {
                "injection_id": f"inj_{int(time.time())}_{candidate.memory_id[:8]}",
                "memory_id": candidate.memory_id,
                "user_id": context.user_id,
                "rule_id": candidate.rule_id,
                "relevance_score": candidate.relevance_score,
                "injection_reason": candidate.injection_reason,
                "context_snapshot": context.dict(),
                "injected_at": datetime.utcnow(),
                "memory_content": memory.get("content", ""),
                "memory_metadata": memory.get("metadata", {}),
            }

            # Store injection record
            await self._store_injection_record(injection_record)

            # Track for analytics
            await self._track_injection_event(candidate, context)

            return injection_record

        except Exception as e:
            logger.error(
                "Failed to execute injection",
                memory_id=candidate.memory_id,
                error=str(e),
            )
            return None

    async def _check_rule_conditions(self, rule: InjectionRule, context: InjectionContext) -> bool:
        """Check if rule conditions are satisfied."""
        try:
            conditions = rule.conditions

            # Check activity conditions
            if "required_activity" in conditions:
                if context.current_activity != conditions["required_activity"]:
                    return False

            # Check time conditions
            if "time_range" in conditions:
                current_hour = datetime.utcnow().hour
                time_range = conditions["time_range"]
                if not (time_range["start"] <= current_hour <= time_range["end"]):
                    return False

            # Check location conditions
            if "location_context" in conditions:
                required_location = conditions["location_context"]
                if not self._match_location_context(context.location_context, required_location):
                    return False

            # Check user state conditions
            if "user_state" in conditions:
                required_state = conditions["user_state"]
                if not self._match_user_state(context.user_state, required_state):
                    return False

            return True

        except Exception as e:
            logger.error("Failed to check rule conditions", error=str(e))
            return False

    def _calculate_urgency(self, rule: InjectionRule, memory_data: Dict[str, Any]) -> float:
        """Calculate urgency score for memory injection."""
        urgency = 0.5  # Base urgency

        # Priority-based urgency
        priority_weights = {
            InjectionPriority.CRITICAL: 1.0,
            InjectionPriority.HIGH: 0.8,
            InjectionPriority.MEDIUM: 0.6,
            InjectionPriority.LOW: 0.4,
            InjectionPriority.BACKGROUND: 0.2,
        }
        urgency += priority_weights.get(rule.priority, 0.5) * 0.3

        # Time-based urgency
        if "time_sensitivity" in memory_data:
            urgency += memory_data["time_sensitivity"] * 0.2

        return min(1.0, urgency)

    # Database query methods (simplified implementations)

    async def _find_context_matching_memories(
        self, rule: InjectionRule, context: InjectionContext
    ) -> List[Dict[str, Any]]:
        """Find memories matching current context."""
        # Simplified implementation - would use sophisticated context matching
        query = """
            SELECT id, content, metadata, created_at,
                   0.7 as relevance_score, 0.8 as confidence
            FROM memories
            WHERE user_id = $1
            ORDER BY created_at DESC
            LIMIT 5
        """

        try:
            results = await self.db.fetch_all(query, context.user_id)
            return [dict(row) for row in results] if results else []
        except Exception:
            return []
