"""
SPEC-061: Property Graph Intelligence Framework

Intelligent graph traversal and reasoning functions that leverage Redis + Apache AGE
for advanced AI capabilities, contextual graph analysis, and memory graph reasoning.

Strategic Components:
- graph_reasoner.py: Injects graph intelligence layer (multi-hop, weighted traversal)
- explain_context() API: Shows "why" a memory was retrieved (traceable paths)
- infer_relevance(): Suggests next-best memories or agents based on proximity
- feedback_loop(): Refines graph traversal using ranking signals
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional

from server.graph.age_client import ApacheAGEClient
from server.redis_client import RedisClient

logger = logging.getLogger(__name__)


@dataclass
class ReasoningPath:
    """Represents a reasoning path through the graph"""

    nodes: list[str] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)
    weights: list[float] = field(default_factory=list)
    total_weight: float = 0.0
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class ContextExplanation:
    """Explanation for why a memory was retrieved"""

    memory_id: str
    retrieval_reason: str
    paths: list[ReasoningPath] = field(default_factory=list)
    relevance_score: float = 0.0
    confidence: float = 0.0
    supporting_evidence: list[str] = field(default_factory=list)


@dataclass
class RelevanceInference:
    """Inference about memory relevance based on graph proximity"""

    suggested_memories: list[str] = field(default_factory=list)
    suggested_agents: list[str] = field(default_factory=list)
    reasoning_scores: dict[str, float] = field(default_factory=dict)
    proximity_metrics: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0


class GraphReasoner:
    """
    SPEC-061: Property Graph Intelligence Framework

    Provides intelligent reasoning over Apache AGE property graph with Redis caching.
    Enables AI-aligned memory graph reasoning and dynamic context injection.
    """

    def __init__(self, age_client: ApacheAGEClient, redis_client: RedisClient):
        self.age_client = age_client
        self.redis_client = redis_client
        self.cache_ttl = 300  # 5 minutes for reasoning results

    async def explain_context(
        self,
        memory_id: str,
        user_id: str,
        context_type: str = "retrieval",
        max_depth: int = 3,
    ) -> ContextExplanation:
        """
        Shows "why" a memory was retrieved with traceable paths.

        Args:
            memory_id: Target memory to explain
            user_id: User requesting explanation
            context_type: Type of context (retrieval, suggestion, inference)
            max_depth: Maximum traversal depth for explanation paths

        Returns:
            ContextExplanation with reasoning paths and evidence
        """
        cache_key = (
            f"context_explanation:{memory_id}:{user_id}:{context_type}:{max_depth}"
        )

        # Check Redis cache first
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for context explanation: {memory_id}")
            data = json.loads(cached_result)
            return ContextExplanation(**data)

        logger.info(f"Computing context explanation for memory: {memory_id}")

        # Find all paths from user to memory
        reasoning_paths = await self._find_reasoning_paths(
            start_node_id=user_id, target_node_id=memory_id, max_depth=max_depth
        )

        # Analyze path significance
        primary_path = self._select_primary_path(reasoning_paths)
        retrieval_reason = self._generate_retrieval_reason(primary_path, context_type)

        # Calculate overall relevance and confidence
        relevance_score = await self._calculate_path_relevance(reasoning_paths)
        confidence = self._calculate_explanation_confidence(reasoning_paths)

        # Gather supporting evidence
        supporting_evidence = await self._gather_supporting_evidence(
            memory_id, reasoning_paths
        )

        explanation = ContextExplanation(
            memory_id=memory_id,
            retrieval_reason=retrieval_reason,
            paths=reasoning_paths,
            relevance_score=relevance_score,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
        )

        # Cache the result
        await self.redis_client.setex(
            cache_key, self.cache_ttl, json.dumps(explanation.__dict__, default=str)
        )

        return explanation

    async def infer_relevance(
        self,
        current_memory_id: str,
        user_id: str,
        context_memories: list[str] = None,
        suggestion_count: int = 5,
    ) -> RelevanceInference:
        """
        Suggests next-best memories or agents based on graph proximity.

        Args:
            current_memory_id: Current memory context
            user_id: User requesting suggestions
            context_memories: Additional context memories
            suggestion_count: Number of suggestions to return

        Returns:
            RelevanceInference with suggested memories and agents
        """
        cache_key = (
            f"relevance_inference:{current_memory_id}:{user_id}:{suggestion_count}"
        )

        # Check Redis cache
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for relevance inference: {current_memory_id}")
            data = json.loads(cached_result)
            return RelevanceInference(**data)

        logger.info(f"Computing relevance inference for memory: {current_memory_id}")

        # Find connected memories through various relationship types
        connected_memories = await self._find_connected_memories_multi_hop(
            current_memory_id, max_depth=2
        )

        # Find relevant agents based on memory patterns
        relevant_agents = await self._find_relevant_agents(current_memory_id, user_id)

        # Calculate proximity metrics
        proximity_metrics = await self._calculate_proximity_metrics(
            current_memory_id, connected_memories + relevant_agents
        )

        # Score and rank suggestions
        memory_scores = await self._score_memory_suggestions(
            connected_memories, proximity_metrics
        )
        agent_scores = await self._score_agent_suggestions(
            relevant_agents, proximity_metrics
        )

        # Select top suggestions
        suggested_memories = self._select_top_suggestions(
            memory_scores, suggestion_count
        )
        suggested_agents = self._select_top_suggestions(
            agent_scores,
            min(suggestion_count, 3),  # Fewer agent suggestions
        )

        # Calculate overall confidence
        confidence = self._calculate_inference_confidence(memory_scores, agent_scores)

        inference = RelevanceInference(
            suggested_memories=suggested_memories,
            suggested_agents=suggested_agents,
            reasoning_scores={**memory_scores, **agent_scores},
            proximity_metrics=proximity_metrics,
            confidence=confidence,
        )

        # Cache the result
        await self.redis_client.setex(
            cache_key, self.cache_ttl, json.dumps(inference.__dict__, default=str)
        )

        return inference

    async def feedback_loop(
        self,
        user_id: str,
        memory_id: str,
        feedback_type: str,
        feedback_score: float,
        context_data: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """
        Refines graph traversal using ranking signals and user feedback.

        Args:
            user_id: User providing feedback
            memory_id: Memory being rated
            feedback_type: Type of feedback (relevance, accuracy, usefulness)
            feedback_score: Numerical feedback score (0.0 to 1.0)
            context_data: Additional context for feedback

        Returns:
            Updated graph weights and traversal parameters
        """
        logger.info(f"Processing feedback loop: {feedback_type} = {feedback_score}")

        # Store feedback in graph as weighted edge
        await self._store_feedback_edge(
            user_id, memory_id, feedback_type, feedback_score, context_data
        )

        # Update graph weights based on feedback
        weight_updates = await self._update_graph_weights(
            user_id, memory_id, feedback_score
        )

        # Adjust traversal parameters
        traversal_updates = await self._adjust_traversal_parameters(
            user_id, feedback_type, feedback_score
        )

        # Invalidate related caches
        await self._invalidate_feedback_caches(user_id, memory_id)

        return {
            "feedback_stored": True,
            "weight_updates": weight_updates,
            "traversal_updates": traversal_updates,
            "cache_invalidations": 5,  # Placeholder count
        }

    async def analyze_memory_network(
        self,
        user_id: str,
        analysis_type: str = "comprehensive",
        time_window: Optional[timedelta] = None,
    ) -> dict[str, Any]:
        """
        Analyzes the user's memory network for insights and patterns.

        Args:
            user_id: User whose network to analyze
            analysis_type: Type of analysis (comprehensive, recent, patterns)
            time_window: Time window for analysis

        Returns:
            Network analysis results with insights and recommendations
        """
        cache_key = f"network_analysis:{user_id}:{analysis_type}"

        # Check cache
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

        logger.info(f"Analyzing memory network for user: {user_id}")

        # Get user's memory network
        network_data = await self.age_client.get_memory_network(user_id)

        # Analyze network structure
        structure_analysis = await self._analyze_network_structure(network_data)

        # Find patterns and clusters
        pattern_analysis = await self._find_network_patterns(network_data, user_id)

        # Generate insights and recommendations
        insights = await self._generate_network_insights(
            structure_analysis, pattern_analysis
        )

        analysis_result = {
            "user_id": user_id,
            "analysis_type": analysis_type,
            "network_structure": structure_analysis,
            "patterns": pattern_analysis,
            "insights": insights,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Cache result
        await self.redis_client.setex(
            cache_key,
            self.cache_ttl * 2,  # Longer cache for network analysis
            json.dumps(analysis_result, default=str),
        )

        return analysis_result

    # Private helper methods

    async def _find_reasoning_paths(
        self, start_node_id: str, target_node_id: str, max_depth: int
    ) -> list[ReasoningPath]:
        """Find all reasoning paths between two nodes"""
        cypher_query = """
        MATCH path = (start)-[*1..%d]-(target)
        WHERE start.id = '%s' AND target.id = '%s'
        RETURN path,
               [r in relationships(path) | r.weight] as weights,
               length(path) as depth
        ORDER BY depth ASC,
                 reduce(total = 0, w in [r in relationships(path) | r.weight] | total + w) DESC
        LIMIT 10
        """ % (
            max_depth,
            start_node_id,
            target_node_id,
        )

        result = await self.age_client.execute_cypher(cypher_query)

        reasoning_paths = []
        for record in result:
            path_data = record["path"]
            weights = record.get("weights", [])

            # Extract nodes and edges from path
            nodes = [node["id"] for node in path_data.get("nodes", [])]
            edges = [edge["type"] for edge in path_data.get("relationships", [])]

            total_weight = sum(weights) if weights else 0.0
            confidence = min(total_weight / len(weights), 1.0) if weights else 0.0

            reasoning_path = ReasoningPath(
                nodes=nodes,
                edges=edges,
                weights=weights,
                total_weight=total_weight,
                confidence=confidence,
                reasoning=self._generate_path_reasoning(nodes, edges),
            )
            reasoning_paths.append(reasoning_path)

        return reasoning_paths

    def _select_primary_path(
        self, paths: list[ReasoningPath]
    ) -> Optional[ReasoningPath]:
        """Select the most significant reasoning path"""
        if not paths:
            return None

        # Score paths by weight and confidence
        scored_paths = [(path, path.total_weight * path.confidence) for path in paths]

        # Return highest scoring path
        return max(scored_paths, key=lambda x: x[1])[0]

    def _generate_retrieval_reason(
        self, path: Optional[ReasoningPath], context_type: str
    ) -> str:
        """Generate human-readable retrieval reason"""
        if not path:
            return f"Memory retrieved through {context_type} context"

        if len(path.nodes) == 2:
            return f"Direct {path.edges[0]} relationship"
        elif len(path.nodes) == 3:
            return f"Connected via {path.edges[0]} → {path.edges[1]}"
        else:
            return f"Multi-hop connection through {len(path.nodes)-1} relationships"

    async def _calculate_path_relevance(self, paths: list[ReasoningPath]) -> float:
        """Calculate overall relevance score from reasoning paths"""
        if not paths:
            return 0.0

        # Weight by path strength and confidence
        total_relevance = sum(path.total_weight * path.confidence for path in paths)

        # Normalize by number of paths
        return min(total_relevance / len(paths), 1.0)

    def _calculate_explanation_confidence(self, paths: list[ReasoningPath]) -> float:
        """Calculate confidence in the explanation"""
        if not paths:
            return 0.0

        # Average confidence across all paths
        avg_confidence = sum(path.confidence for path in paths) / len(paths)

        # Boost confidence if multiple strong paths exist
        strong_paths = [p for p in paths if p.confidence > 0.7]
        boost = min(len(strong_paths) * 0.1, 0.3)

        return min(avg_confidence + boost, 1.0)

    async def _gather_supporting_evidence(
        self, memory_id: str, paths: list[ReasoningPath]
    ) -> list[str]:
        """Gather supporting evidence for the explanation"""
        evidence = []

        # Add path-based evidence
        for path in paths[:3]:  # Top 3 paths
            if path.confidence > 0.5:
                evidence.append(
                    f"Strong {path.reasoning} (confidence: {path.confidence:.2f})"
                )

        # Add temporal evidence
        cypher_query = f"""
        MATCH (m:Memory {{id: '{memory_id}'}})-[r]-(related)
        WHERE r.timestamp IS NOT NULL
        RETURN related.id, r.timestamp, type(r) as rel_type
        ORDER BY r.timestamp DESC LIMIT 5
        """

        result = await self.age_client.execute_cypher(cypher_query)
        for record in result:
            evidence.append(f"Recent {record['rel_type']} with {record['related.id']}")

        return evidence

    async def _find_connected_memories_multi_hop(
        self, memory_id: str, max_depth: int = 2
    ) -> list[str]:
        """Find connected memories through multi-hop traversal"""
        cypher_query = f"""
        MATCH (m:Memory {{id: '{memory_id}'}})-[*1..{max_depth}]-(connected:Memory)
        WHERE connected.id <> '{memory_id}'
        RETURN DISTINCT connected.id as memory_id,
               length(shortestPath((m)-[*]-(connected))) as distance
        ORDER BY distance ASC, connected.created_at DESC
        LIMIT 20
        """

        result = await self.age_client.execute_cypher(cypher_query)
        return [record["memory_id"] for record in result]

    async def _find_relevant_agents(self, memory_id: str, user_id: str) -> list[str]:
        """Find agents relevant to the memory context"""
        cypher_query = f"""
        MATCH (m:Memory {{id: '{memory_id}'}})-[:LINKED_TO]-(macro:Macro)-[:TRIGGERED_BY]-(agent:Agent)
        RETURN DISTINCT agent.id as agent_id
        UNION
        MATCH (u:User {{id: '{user_id}'}})-[:CREATED]-(mem:Memory)-[:LINKED_TO]-(macro:Macro)-[:TRIGGERED_BY]-(agent:Agent)
        RETURN DISTINCT agent.id as agent_id
        LIMIT 10
        """

        result = await self.age_client.execute_cypher(cypher_query)
        return [record["agent_id"] for record in result]

    def _generate_path_reasoning(self, nodes: list[str], edges: list[str]) -> str:
        """Generate reasoning description for a path"""
        if len(nodes) <= 1:
            return "Direct access"
        elif len(nodes) == 2:
            return f"Direct {edges[0]} connection"
        else:
            return f"Path through {' → '.join(edges)}"

    async def _calculate_proximity_metrics(
        self, source_id: str, target_ids: list[str]
    ) -> dict[str, float]:
        """Calculate proximity metrics between source and targets"""
        metrics = {}

        for target_id in target_ids:
            # Simple distance-based proximity for now
            cypher_query = f"""
            MATCH path = shortestPath((source)-[*]-(target))
            WHERE source.id = '{source_id}' AND target.id = '{target_id}'
            RETURN length(path) as distance
            """

            result = await self.age_client.execute_cypher(cypher_query)
            if result:
                distance = result[0].get("distance", float("inf"))
                # Convert distance to proximity (closer = higher score)
                metrics[target_id] = (
                    1.0 / (1.0 + distance) if distance < float("inf") else 0.0
                )
            else:
                metrics[target_id] = 0.0

        return metrics

    async def _score_memory_suggestions(
        self, memory_ids: list[str], proximity_metrics: dict[str, float]
    ) -> dict[str, float]:
        """Score memory suggestions based on various factors"""
        scores = {}

        for memory_id in memory_ids:
            proximity_score = proximity_metrics.get(memory_id, 0.0)

            # Get additional scoring factors
            cypher_query = f"""
            MATCH (m:Memory {{id: '{memory_id}'}})
            OPTIONAL MATCH (m)-[r]-()
            RETURN m.relevance_score as base_score,
                   count(r) as connection_count,
                   m.created_at as created_at
            """

            result = await self.age_client.execute_cypher(cypher_query)
            if result:
                record = result[0]
                base_score = record.get("base_score", 0.5)
                connection_count = record.get("connection_count", 0)

                # Combine factors
                connection_boost = min(connection_count * 0.05, 0.3)
                final_score = (
                    proximity_score * 0.4 + base_score * 0.4 + connection_boost * 0.2
                )

                scores[memory_id] = final_score
            else:
                scores[memory_id] = proximity_score * 0.5

        return scores

    async def _score_agent_suggestions(
        self, agent_ids: list[str], proximity_metrics: dict[str, float]
    ) -> dict[str, float]:
        """Score agent suggestions based on relevance and activity"""
        scores = {}

        for agent_id in agent_ids:
            proximity_score = proximity_metrics.get(agent_id, 0.0)

            # Get agent activity metrics
            cypher_query = f"""
            MATCH (a:Agent {{id: '{agent_id}'}})
            OPTIONAL MATCH (a)<-[:TRIGGERED_BY]-(macro:Macro)
            RETURN count(macro) as activity_count,
                   a.capabilities as capabilities
            """

            result = await self.age_client.execute_cypher(cypher_query)
            if result:
                record = result[0]
                activity_count = record.get("activity_count", 0)

                # Score based on activity and proximity
                activity_score = min(activity_count * 0.1, 0.5)
                final_score = proximity_score * 0.6 + activity_score * 0.4

                scores[agent_id] = final_score
            else:
                scores[agent_id] = proximity_score * 0.3

        return scores

    def _select_top_suggestions(
        self, scores: dict[str, float], count: int
    ) -> list[str]:
        """Select top suggestions based on scores"""
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:count]]

    def _calculate_inference_confidence(
        self, memory_scores: dict[str, float], agent_scores: dict[str, float]
    ) -> float:
        """Calculate confidence in the inference results"""
        all_scores = list(memory_scores.values()) + list(agent_scores.values())

        if not all_scores:
            return 0.0

        # Base confidence on score distribution
        avg_score = sum(all_scores) / len(all_scores)
        max_score = max(all_scores)

        # Higher confidence if we have high-scoring suggestions
        confidence = (avg_score + max_score) / 2.0

        # Boost confidence if we have multiple good suggestions
        good_suggestions = [s for s in all_scores if s > 0.6]
        if len(good_suggestions) >= 3:
            confidence = min(confidence + 0.2, 1.0)

        return confidence

    async def _store_feedback_edge(
        self,
        user_id: str,
        memory_id: str,
        feedback_type: str,
        feedback_score: float,
        context_data: dict[str, Any],
    ) -> None:
        """Store feedback as a weighted edge in the graph"""
        timestamp = datetime.utcnow().isoformat()

        cypher_query = f"""
        MATCH (u:User {{id: '{user_id}'}}), (m:Memory {{id: '{memory_id}'}})
        MERGE (u)-[r:FEEDBACK]->(m)
        SET r.type = '{feedback_type}',
            r.score = {feedback_score},
            r.timestamp = '{timestamp}',
            r.context = '{json.dumps(context_data or {})}'
        RETURN r
        """

        await self.age_client.execute_cypher(cypher_query)

    async def _update_graph_weights(
        self, user_id: str, memory_id: str, feedback_score: float
    ) -> dict[str, int]:
        """Update graph weights based on feedback"""
        # Update weights on related edges
        cypher_query = f"""
        MATCH (u:User {{id: '{user_id}'}})-[r]-(m:Memory {{id: '{memory_id}'}})
        SET r.weight = COALESCE(r.weight, 0.5) + ({feedback_score} - 0.5) * 0.1
        RETURN count(r) as updated_edges
        """

        result = await self.age_client.execute_cypher(cypher_query)
        updated_edges = result[0]["updated_edges"] if result else 0

        return {"updated_edges": updated_edges}

    async def _adjust_traversal_parameters(
        self, user_id: str, feedback_type: str, feedback_score: float
    ) -> dict[str, Any]:
        """Adjust traversal parameters based on feedback"""
        # Store user-specific traversal preferences
        preferences_key = f"traversal_prefs:{user_id}"

        current_prefs = await self.redis_client.get(preferences_key)
        if current_prefs:
            prefs = json.loads(current_prefs)
        else:
            prefs = {
                "depth_preference": 2.0,
                "weight_threshold": 0.5,
                "relevance_boost": 1.0,
            }

        # Adjust based on feedback
        if feedback_type == "relevance":
            if feedback_score > 0.7:
                prefs["relevance_boost"] *= 1.1
            elif feedback_score < 0.3:
                prefs["relevance_boost"] *= 0.9

        # Store updated preferences
        await self.redis_client.setex(
            preferences_key,
            86400,
            json.dumps(prefs),  # 24 hours
        )

        return prefs

    async def _invalidate_feedback_caches(self, user_id: str, memory_id: str) -> None:
        """Invalidate caches affected by feedback"""
        patterns = [
            f"context_explanation:{memory_id}:*",
            f"relevance_inference:{memory_id}:*",
            f"network_analysis:{user_id}:*",
        ]

        for pattern in patterns:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)

    async def _analyze_network_structure(
        self, network_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze the structure of the memory network"""
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        # Basic structural metrics
        node_count = len(nodes)
        edge_count = len(edges)
        density = (
            (2 * edge_count) / (node_count * (node_count - 1)) if node_count > 1 else 0
        )

        # Node type distribution
        node_types = {}
        for node in nodes:
            node_type = node.get("label", "Unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "density": density,
            "node_types": node_types,
            "avg_connections": edge_count / node_count if node_count > 0 else 0,
        }

    async def _find_network_patterns(
        self, network_data: dict[str, Any], user_id: str
    ) -> dict[str, Any]:
        """Find patterns and clusters in the network"""
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        # Count connections per node
        node_connections = {}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            node_connections[source] = node_connections.get(source, 0) + 1
            node_connections[target] = node_connections.get(target, 0) + 1

        # Find hubs (top 10% most connected)
        sorted_nodes = sorted(
            node_connections.items(), key=lambda x: x[1], reverse=True
        )
        hub_count = max(1, len(sorted_nodes) // 10)
        hubs = sorted_nodes[:hub_count]

        return {
            "hubs": [{"node_id": hub[0], "connections": hub[1]} for hub in hubs],
            "connection_distribution": dict(sorted_nodes[:10]),  # Top 10
        }

    async def _generate_network_insights(
        self, structure: dict[str, Any], patterns: dict[str, Any]
    ) -> list[str]:
        """Generate insights and recommendations from network analysis"""
        insights = []

        # Density insights
        density = structure.get("density", 0)
        if density < 0.1:
            insights.append(
                "Low network density suggests opportunities for more memory connections"
            )
        elif density > 0.7:
            insights.append(
                "High network density indicates well-connected memory system"
            )

        # Hub insights
        hubs = patterns.get("hubs", [])
        if hubs:
            top_hub = hubs[0]
            insights.append(
                f"Memory hub '{top_hub['node_id']}' has {top_hub['connections']} connections"
            )

        # Connection insights
        avg_connections = structure.get("avg_connections", 0)
        if avg_connections < 2:
            insights.append(
                "Consider creating more memory relationships for better context"
            )

        return insights


# Factory function for dependency injection
def create_graph_reasoner(
    age_client: ApacheAGEClient, redis_client: RedisClient
) -> GraphReasoner:
    """Create GraphReasoner instance with dependency injection"""
    return GraphReasoner(age_client, redis_client)
