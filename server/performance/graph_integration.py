"""
Graph Database Performance Integration
Integrates graph performance optimizations with existing SPEC-061 Graph Intelligence Framework
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import structlog

from .graph_optimizer import GraphPerformanceOptimizer

logger = structlog.get_logger(__name__)


class GraphIntelligencePerformanceWrapper:
    """
    Performance wrapper for SPEC-061 Graph Intelligence Framework.

    Enhances the existing GraphReasoner with caching and optimization.
    """

    def __init__(self, graph_reasoner, redis_client):
        self.graph_reasoner = graph_reasoner
        self.optimizer = GraphPerformanceOptimizer(redis_client)

        # Performance tracking for graph intelligence operations
        self.intelligence_metrics = {
            "context_explanations": 0,
            "relevance_inferences": 0,
            "feedback_loops": 0,
            "network_analyses": 0,
            "avg_explanation_time_ms": 0,
            "avg_inference_time_ms": 0,
        }

    async def optimized_explain_context(
        self,
        user_id: str,
        memory_id: str,
        context_id: str,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Optimized context explanation with caching.

        Enhances SPEC-061 explain_context() with performance optimization.
        """
        start_time = time.time()

        try:
            # Use optimized path traversal for context explanation
            explanation_paths = await self.optimizer.optimized_path_traversal(
                start_node_id=memory_id,
                end_node_id=context_id,
                max_depth=max_depth,
                user_id=user_id,
            )

            # Get related memories through optimized relationship queries
            related_memories = await self.optimizer.optimized_relationship_query(
                start_node_id=memory_id,
                relationship_type="SIMILAR_TO|REFERENCES|LINKED_TO",
                user_id=user_id,
            )

            # Build comprehensive explanation
            explanation = {
                "memory_id": memory_id,
                "context_id": context_id,
                "reasoning_paths": explanation_paths,
                "related_memories": related_memories[:10],  # Limit for performance
                "explanation_strength": self._calculate_explanation_strength(
                    explanation_paths
                ),
                "confidence_score": self._calculate_confidence_score(
                    explanation_paths, related_memories
                ),
                "generated_at": time.time(),
            }

            # Update metrics
            execution_time = time.time() - start_time
            self.intelligence_metrics["context_explanations"] += 1
            self._update_avg_time("explanation", execution_time)

            # Invalidate related caches when explanation is generated
            await self.optimizer.invalidate_cache_on_graph_operation(
                "context_explanation_generated"
            )

            logger.info(
                "Context explanation generated",
                user_id=user_id,
                memory_id=memory_id,
                context_id=context_id,
                execution_time_ms=round(execution_time * 1000, 2),
                paths_found=len(explanation_paths),
                related_memories_found=len(related_memories),
            )

            return explanation

        except Exception as e:
            logger.error(
                "Context explanation failed",
                user_id=user_id,
                memory_id=memory_id,
                context_id=context_id,
                error=str(e),
            )
            raise

    async def optimized_infer_relevance(
        self,
        user_id: str,
        current_memory_id: str,
        candidate_memory_ids: List[str],
        context_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Optimized relevance inference with graph proximity caching.

        Enhances SPEC-061 infer_relevance() with performance optimization.
        """
        start_time = time.time()

        try:
            relevance_scores = []

            # Process candidates in batches for better performance
            batch_size = 10
            for i in range(0, len(candidate_memory_ids), batch_size):
                batch = candidate_memory_ids[i : i + batch_size]

                # Use optimized path traversal for each candidate
                batch_tasks = [
                    self.optimizer.optimized_path_traversal(
                        start_node_id=current_memory_id,
                        end_node_id=candidate_id,
                        max_depth=4,
                        user_id=user_id,
                    )
                    for candidate_id in batch
                ]

                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                # Calculate relevance scores for batch
                for candidate_id, paths in zip(batch, batch_results):
                    if isinstance(paths, Exception):
                        logger.warning(
                            "Path traversal failed for candidate",
                            candidate_id=candidate_id,
                            error=str(paths),
                        )
                        continue

                    relevance_score = self._calculate_relevance_score(
                        paths, candidate_id
                    )

                    relevance_scores.append(
                        {
                            "memory_id": candidate_id,
                            "relevance_score": relevance_score,
                            "path_count": len(paths) if paths else 0,
                            "shortest_path_length": (
                                min([p.get("path_length", float("inf")) for p in paths])
                                if paths
                                else float("inf")
                            ),
                            "reasoning_paths": paths[
                                :3
                            ],  # Keep top 3 paths for explanation
                        }
                    )

            # Sort by relevance score
            relevance_scores.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Update metrics
            execution_time = time.time() - start_time
            self.intelligence_metrics["relevance_inferences"] += 1
            self._update_avg_time("inference", execution_time)

            logger.info(
                "Relevance inference completed",
                user_id=user_id,
                current_memory_id=current_memory_id,
                candidates_processed=len(candidate_memory_ids),
                execution_time_ms=round(execution_time * 1000, 2),
                top_score=(
                    relevance_scores[0]["relevance_score"] if relevance_scores else 0
                ),
            )

            return relevance_scores

        except Exception as e:
            logger.error(
                "Relevance inference failed",
                user_id=user_id,
                current_memory_id=current_memory_id,
                candidates_count=len(candidate_memory_ids),
                error=str(e),
            )
            raise

    async def optimized_analyze_memory_network(
        self,
        user_id: str,
        context_id: Optional[str] = None,
        include_analytics: bool = True,
    ) -> Dict[str, Any]:
        """
        Optimized memory network analysis with comprehensive caching.

        Enhances SPEC-061 analyze_memory_network() with performance optimization.
        """
        start_time = time.time()

        try:
            # Use optimized memory network analysis
            network_analysis = await self.optimizer.optimized_memory_network_analysis(
                user_id=user_id,
                context_id=context_id,
            )

            # Add advanced analytics if requested
            if include_analytics:
                network_analysis["advanced_analytics"] = (
                    await self._generate_advanced_analytics(user_id, network_analysis)
                )

            # Update metrics
            execution_time = time.time() - start_time
            self.intelligence_metrics["network_analyses"] += 1

            logger.info(
                "Memory network analysis completed",
                user_id=user_id,
                context_id=context_id,
                execution_time_ms=round(execution_time * 1000, 2),
                total_memories=network_analysis.get("total_memories", 0),
                network_density=network_analysis.get("network_density", 0),
            )

            return network_analysis

        except Exception as e:
            logger.error(
                "Memory network analysis failed",
                user_id=user_id,
                context_id=context_id,
                error=str(e),
            )
            raise

    async def optimized_feedback_loop(
        self,
        user_id: str,
        memory_id: str,
        feedback_type: str,
        feedback_value: float,
        context_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Optimized feedback loop with intelligent cache invalidation.

        Enhances SPEC-061 feedback_loop() with performance optimization.
        """
        start_time = time.time()

        try:
            # Store feedback in graph database
            feedback_result = await self._store_feedback_optimized(
                user_id, memory_id, feedback_type, feedback_value, context_id
            )

            # Intelligently invalidate related caches
            await self._invalidate_feedback_related_caches(
                user_id, memory_id, context_id
            )

            # Update metrics
            execution_time = time.time() - start_time
            self.intelligence_metrics["feedback_loops"] += 1

            logger.info(
                "Feedback loop processed",
                user_id=user_id,
                memory_id=memory_id,
                feedback_type=feedback_type,
                feedback_value=feedback_value,
                execution_time_ms=round(execution_time * 1000, 2),
            )

            return feedback_result

        except Exception as e:
            logger.error(
                "Feedback loop failed",
                user_id=user_id,
                memory_id=memory_id,
                feedback_type=feedback_type,
                error=str(e),
            )
            raise

    async def get_graph_intelligence_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics for graph intelligence operations."""
        optimizer_stats = await self.optimizer.get_graph_performance_stats()

        return {
            "intelligence_metrics": self.intelligence_metrics,
            "graph_optimizer_stats": optimizer_stats,
            "performance_summary": {
                "total_intelligence_operations": sum(
                    [
                        self.intelligence_metrics["context_explanations"],
                        self.intelligence_metrics["relevance_inferences"],
                        self.intelligence_metrics["feedback_loops"],
                        self.intelligence_metrics["network_analyses"],
                    ]
                ),
                "avg_explanation_time_ms": self.intelligence_metrics[
                    "avg_explanation_time_ms"
                ],
                "avg_inference_time_ms": self.intelligence_metrics[
                    "avg_inference_time_ms"
                ],
            },
            "optimization_impact": {
                "cache_hit_rate": optimizer_stats["cache_performance"]["hit_rate"],
                "query_optimization_enabled": True,
                "batch_processing_enabled": True,
                "intelligent_invalidation_enabled": True,
            },
        }

    def _calculate_explanation_strength(self, paths: List[Dict]) -> float:
        """Calculate explanation strength based on path analysis."""
        if not paths:
            return 0.0

        # Shorter paths indicate stronger explanations
        path_lengths = [p.get("path_length", float("inf")) for p in paths]
        avg_path_length = sum(path_lengths) / len(path_lengths)

        # More paths indicate stronger explanations
        path_count_factor = min(len(paths) / 5.0, 1.0)  # Normalize to max of 5 paths

        # Combine factors (shorter paths and more paths = stronger explanation)
        strength = path_count_factor * (1.0 / max(avg_path_length, 1.0))

        return min(strength, 1.0)  # Cap at 1.0

    def _calculate_confidence_score(
        self, paths: List[Dict], related_memories: List[Dict]
    ) -> float:
        """Calculate confidence score based on paths and related memories."""
        if not paths and not related_memories:
            return 0.0

        path_confidence = len(paths) * 0.1  # Each path adds 10% confidence
        memory_confidence = len(related_memories) * 0.05  # Each related memory adds 5%

        return min(path_confidence + memory_confidence, 1.0)  # Cap at 100%

    def _calculate_relevance_score(self, paths: List[Dict], candidate_id: str) -> float:
        """Calculate relevance score based on graph proximity."""
        if not paths:
            return 0.0

        # Score based on shortest path and number of paths
        shortest_path = min([p.get("path_length", float("inf")) for p in paths])
        path_count = len(paths)

        # Relevance decreases with path length, increases with path count
        distance_score = 1.0 / max(shortest_path, 1.0)
        diversity_score = min(path_count / 10.0, 1.0)  # Normalize to max of 10 paths

        return (distance_score + diversity_score) / 2.0

    async def _generate_advanced_analytics(
        self, user_id: str, network_analysis: Dict
    ) -> Dict:
        """Generate advanced analytics for memory network."""
        return {
            "clustering_coefficient": await self._calculate_clustering_coefficient(
                user_id
            ),
            "centrality_measures": await self._calculate_centrality_measures(user_id),
            "community_detection": await self._detect_communities(user_id),
            "temporal_patterns": await self._analyze_temporal_patterns(user_id),
        }

    async def _store_feedback_optimized(
        self,
        user_id: str,
        memory_id: str,
        feedback_type: str,
        feedback_value: float,
        context_id: Optional[str],
    ) -> Dict:
        """Store feedback with optimized graph operations."""
        # This would integrate with your actual graph database
        # For now, we'll simulate the storage
        return {
            "feedback_stored": True,
            "user_id": user_id,
            "memory_id": memory_id,
            "feedback_type": feedback_type,
            "feedback_value": feedback_value,
            "context_id": context_id,
            "timestamp": time.time(),
        }

    async def _invalidate_feedback_related_caches(
        self, user_id: str, memory_id: str, context_id: Optional[str]
    ):
        """Intelligently invalidate caches related to feedback."""
        # Invalidate caches that would be affected by this feedback
        await self.optimizer.invalidate_cache_on_graph_operation("user_feedback")

        # Additional targeted invalidation based on memory and context
        if context_id:
            await self.optimizer.invalidate_cache_on_graph_operation("context_updated")

    def _update_avg_time(self, operation_type: str, execution_time: float):
        """Update average execution time for operation type."""
        time_key = f"avg_{operation_type}_time_ms"
        count_key = f"{operation_type}s"

        if (
            time_key in self.intelligence_metrics
            and count_key in self.intelligence_metrics
        ):
            current_avg = self.intelligence_metrics[time_key]
            current_count = self.intelligence_metrics[count_key]

            # Calculate new average
            total_time = (current_avg * (current_count - 1)) + (execution_time * 1000)
            self.intelligence_metrics[time_key] = total_time / current_count

    # Placeholder methods for advanced analytics (would be implemented based on specific requirements)
    async def _calculate_clustering_coefficient(self, user_id: str) -> float:
        return 0.75  # Placeholder

    async def _calculate_centrality_measures(self, user_id: str) -> Dict:
        return {"betweenness": 0.5, "closeness": 0.6, "degree": 0.8}  # Placeholder

    async def _detect_communities(self, user_id: str) -> List[Dict]:
        return [{"community_id": "c1", "size": 10, "density": 0.8}]  # Placeholder

    async def _analyze_temporal_patterns(self, user_id: str) -> Dict:
        return {
            "peak_hours": [9, 14, 20],
            "activity_trend": "increasing",
        }  # Placeholder


# Factory function for integration
async def create_optimized_graph_intelligence(graph_reasoner, redis_client):
    """Create optimized graph intelligence wrapper."""
    wrapper = GraphIntelligencePerformanceWrapper(graph_reasoner, redis_client)

    logger.info(
        "Optimized graph intelligence created",
        features=[
            "cached_context_explanations",
            "optimized_relevance_inference",
            "batch_processed_network_analysis",
            "intelligent_cache_invalidation",
        ],
    )

    return wrapper
