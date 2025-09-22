"""
Graph Database Performance Optimization
Integrates Apache AGE graph database optimizations with Redis caching
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class GraphQueryCache:
    """
    Specialized caching for graph database queries with Apache AGE.

    Features:
    - Cypher query result caching
    - Graph traversal path caching
    - Relationship query optimization
    - Memory network analysis caching
    """

    def __init__(
        self,
        redis_client,
        default_ttl: int = 300,  # 5 minutes default
        cache_prefix: str = "graph_cache",
    ):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self.cache_prefix = cache_prefix

        # Graph-specific TTL configuration
        self.graph_ttls: Dict[str, int] = {
            "node_lookup": 600,  # Node lookups - 10 minutes
            "relationship_query": 300,  # Relationship queries - 5 minutes
            "path_traversal": 180,  # Path traversals - 3 minutes
            "memory_network": 120,  # Memory network analysis - 2 minutes
            "context_explanation": 300,  # Context explanations - 5 minutes
            "relevance_inference": 300,  # Relevance inferences - 5 minutes
            "graph_analytics": 600,  # Graph analytics - 10 minutes
        }

        # Cache invalidation patterns for graph operations
        self.graph_invalidation_patterns: Dict[str, List[str]] = {
            "memory_created": [
                "memory_network",
                "path_traversal",
                "relevance_inference",
            ],
            "memory_updated": [
                "memory_network",
                "context_explanation",
                "relevance_inference",
            ],
            "memory_deleted": [
                "memory_network",
                "path_traversal",
                "context_explanation",
            ],
            "relationship_created": [
                "path_traversal",
                "relevance_inference",
                "graph_analytics",
            ],
            "relationship_updated": ["path_traversal", "relevance_inference"],
            "relationship_deleted": [
                "path_traversal",
                "relevance_inference",
                "graph_analytics",
            ],
            "user_feedback": ["context_explanation", "relevance_inference"],
        }

    def generate_graph_cache_key(
        self,
        query_type: str,
        cypher_query: str,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """Generate cache key for graph queries."""
        key_components = [query_type, cypher_query]

        # Add sorted parameters
        if params:
            key_components.append(json.dumps(params, sort_keys=True))

        # Add user context for user-specific queries
        if user_id:
            key_components.append(f"user:{user_id}")

        # Create hash for consistent key length
        key_string = "|".join(str(comp) for comp in key_components)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]

        return f"{self.cache_prefix}:{query_type}:{key_hash}"

    async def get_cached_graph_result(self, cache_key: str) -> Optional[Any]:
        """Retrieve cached graph query result."""
        try:
            start_time = time.time()
            cached_data = await self.redis.get(cache_key)

            if cached_data:
                result = json.loads(cached_data)
                duration = time.time() - start_time

                logger.debug(
                    "Graph cache hit",
                    cache_key=cache_key,
                    duration_ms=round(duration * 1000, 2),
                )

                return result["data"]

            return None

        except Exception as e:
            logger.warning(
                "Graph cache retrieval failed", cache_key=cache_key, error=str(e)
            )
            return None

    async def cache_graph_result(
        self,
        cache_key: str,
        result: Any,
        ttl: int,
        query_metadata: Optional[Dict] = None,
    ) -> None:
        """Store graph query result in cache."""
        try:
            cache_data = {
                "data": result,
                "cached_at": time.time(),
                "ttl": ttl,
                "metadata": query_metadata or {},
                "result_type": "graph_query",
            }

            await self.redis.setex(cache_key, ttl, json.dumps(cache_data, default=str))

            logger.debug(
                "Graph result cached",
                cache_key=cache_key,
                ttl=ttl,
                result_size=len(str(result)) if result else 0,
            )

        except Exception as e:
            logger.warning(
                "Graph cache storage failed", cache_key=cache_key, error=str(e)
            )

    async def execute_cached_graph_query(
        self,
        query_type: str,
        cypher_query: str,
        graph_executor: callable,
        params: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """Execute graph query with caching."""
        params = params or {}
        cache_key = self.generate_graph_cache_key(
            query_type, cypher_query, params, user_id
        )
        ttl = ttl or self.graph_ttls.get(query_type, self.default_ttl)

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = await self.get_cached_graph_result(cache_key)
            if cached_result is not None:
                return cached_result

        # Execute graph query
        start_time = time.time()
        try:
            result = await graph_executor(cypher_query, params)
            execution_time = time.time() - start_time

            # Cache the result
            query_metadata = {
                "query_type": query_type,
                "execution_time_ms": round(execution_time * 1000, 2),
                "cypher_query": (
                    cypher_query[:200] + "..."
                    if len(cypher_query) > 200
                    else cypher_query
                ),
                "params_count": len(params),
            }

            await self.cache_graph_result(cache_key, result, ttl, query_metadata)

            logger.info(
                "Graph query executed and cached",
                query_type=query_type,
                execution_time_ms=round(execution_time * 1000, 2),
                cache_key=cache_key,
                result_count=len(result) if isinstance(result, list) else 1,
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "Graph query execution failed",
                query_type=query_type,
                execution_time_ms=round(execution_time * 1000, 2),
                cypher_query=cypher_query[:100],
                error=str(e),
            )
            raise

    async def invalidate_graph_cache_by_operation(self, operation: str) -> int:
        """Invalidate graph cache based on data operations."""
        patterns = self.graph_invalidation_patterns.get(operation, [])
        total_deleted = 0

        for pattern in patterns:
            cache_pattern = f"{self.cache_prefix}:*{pattern}*"
            try:
                keys = await self.redis.keys(cache_pattern)
                if keys:
                    deleted = await self.redis.delete(*keys)
                    total_deleted += deleted
                    logger.debug(
                        "Graph cache invalidated",
                        operation=operation,
                        pattern=pattern,
                        keys_deleted=deleted,
                    )
            except Exception as e:
                logger.warning(
                    "Graph cache invalidation failed",
                    operation=operation,
                    pattern=pattern,
                    error=str(e),
                )

        if total_deleted > 0:
            logger.info(
                "Graph cache invalidated by operation",
                operation=operation,
                total_deleted=total_deleted,
            )

        return total_deleted


class GraphPerformanceOptimizer:
    """
    Comprehensive graph database performance optimizer.

    Integrates with SPEC-061 Graph Intelligence Framework and SPEC-062 GraphOps Stack.
    """

    def __init__(self, redis_client, graph_db_client=None):
        self.redis = redis_client
        self.graph_db = graph_db_client
        self.query_cache = GraphQueryCache(redis_client)

        # Performance metrics
        self.metrics = {
            "graph_queries_executed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_query_time_ms": 0,
            "total_query_time": 0,
        }

    async def optimized_node_lookup(
        self,
        node_type: str,
        properties: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Optimized node lookup with caching."""
        cypher_query = f"""
        MATCH (n:{node_type})
        WHERE {' AND '.join([f'n.{k} = ${k}' for k in properties.keys()])}
        RETURN n
        """

        async def executor(query, params):
            # This would integrate with your actual graph DB client
            # For now, we'll simulate the execution
            self.metrics["graph_queries_executed"] += 1
            return await self._execute_graph_query(query, params)

        result = await self.query_cache.execute_cached_graph_query(
            query_type="node_lookup",
            cypher_query=cypher_query,
            graph_executor=executor,
            params=properties,
            user_id=user_id,
        )

        self._update_cache_metrics(True if result else False)
        return result

    async def optimized_relationship_query(
        self,
        start_node_id: str,
        relationship_type: str,
        end_node_type: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Optimized relationship traversal with caching."""
        cypher_query = f"""
        MATCH (start)-[r:{relationship_type}]->(end{':' + end_node_type if end_node_type else ''})
        WHERE start.id = $start_node_id
        RETURN start, r, end
        """

        params = {"start_node_id": start_node_id}

        async def executor(query, params):
            self.metrics["graph_queries_executed"] += 1
            return await self._execute_graph_query(query, params)

        result = await self.query_cache.execute_cached_graph_query(
            query_type="relationship_query",
            cypher_query=cypher_query,
            graph_executor=executor,
            params=params,
            user_id=user_id,
        )

        self._update_cache_metrics(True if result else False)
        return result

    async def optimized_path_traversal(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 5,
        user_id: Optional[str] = None,
    ) -> List[Dict]:
        """Optimized path finding with caching."""
        cypher_query = f"""
        MATCH path = shortestPath((start)-[*1..{max_depth}]-(end))
        WHERE start.id = $start_node_id AND end.id = $end_node_id
        RETURN path, length(path) as path_length
        ORDER BY path_length
        LIMIT 10
        """

        params = {
            "start_node_id": start_node_id,
            "end_node_id": end_node_id,
        }

        async def executor(query, params):
            self.metrics["graph_queries_executed"] += 1
            return await self._execute_graph_query(query, params)

        result = await self.query_cache.execute_cached_graph_query(
            query_type="path_traversal",
            cypher_query=cypher_query,
            graph_executor=executor,
            params=params,
            user_id=user_id,
        )

        self._update_cache_metrics(True if result else False)
        return result

    async def optimized_memory_network_analysis(
        self,
        user_id: str,
        context_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Optimized memory network analysis with caching."""
        cypher_query = """
        MATCH (u:User {id: $user_id})-[:CREATED]->(m:Memory)
        OPTIONAL MATCH (m)-[r:SIMILAR_TO|REFERENCES|LINKED_TO]-(related:Memory)
        OPTIONAL MATCH (m)-[:BELONGS_TO]->(c:Context)
        WHERE $context_id IS NULL OR c.id = $context_id
        RETURN m, collect(DISTINCT related) as related_memories,
               collect(DISTINCT r) as relationships,
               c.name as context_name,
               count(DISTINCT related) as connection_count
        ORDER BY connection_count DESC
        LIMIT 50
        """

        params = {
            "user_id": user_id,
            "context_id": context_id,
        }

        async def executor(query, params):
            self.metrics["graph_queries_executed"] += 1
            raw_result = await self._execute_graph_query(query, params)

            # Process results into network analysis format
            analysis = {
                "total_memories": len(raw_result),
                "highly_connected_memories": [
                    item for item in raw_result if item.get("connection_count", 0) > 3
                ],
                "network_density": self._calculate_network_density(raw_result),
                "context_distribution": self._analyze_context_distribution(raw_result),
                "connection_patterns": self._analyze_connection_patterns(raw_result),
            }

            return analysis

        result = await self.query_cache.execute_cached_graph_query(
            query_type="memory_network",
            cypher_query=cypher_query,
            graph_executor=executor,
            params=params,
            user_id=user_id,
        )

        self._update_cache_metrics(True if result else False)
        return result

    async def invalidate_cache_on_graph_operation(self, operation: str) -> int:
        """Invalidate relevant caches when graph data changes."""
        return await self.query_cache.invalidate_graph_cache_by_operation(operation)

    async def get_graph_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive graph performance statistics."""
        cache_stats = await self.query_cache.redis.info("memory")

        # Calculate cache hit rate
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = self.metrics["cache_hits"] / max(1, total_requests)

        return {
            "query_metrics": self.metrics,
            "cache_performance": {
                "hit_rate": cache_hit_rate,
                "total_requests": total_requests,
            },
            "redis_memory": {
                "used_memory_human": cache_stats.get("used_memory_human", "0B"),
                "used_memory_peak_human": cache_stats.get(
                    "used_memory_peak_human", "0B"
                ),
            },
            "optimization_recommendations": self._get_optimization_recommendations(),
        }

    def _update_cache_metrics(self, cache_hit: bool):
        """Update cache performance metrics."""
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

    async def _execute_graph_query(self, cypher_query: str, params: Dict) -> List[Dict]:
        """Execute graph query against Apache AGE database."""
        start_time = time.time()

        try:
            # This is where you'd integrate with your actual Apache AGE client
            # For now, we'll simulate the execution
            if self.graph_db:
                result = await self.graph_db.execute(cypher_query, params)
            else:
                # Simulate query execution
                await asyncio.sleep(0.01)  # Simulate 10ms query time
                result = []

            execution_time = time.time() - start_time
            self.metrics["total_query_time"] += execution_time

            # Update average query time
            if self.metrics["graph_queries_executed"] > 0:
                self.metrics["avg_query_time_ms"] = (
                    self.metrics["total_query_time"]
                    / self.metrics["graph_queries_executed"]
                    * 1000
                )

            return result

        except Exception as e:
            logger.error("Graph query execution failed", error=str(e))
            raise

    def _calculate_network_density(self, network_data: List[Dict]) -> float:
        """Calculate network density from graph analysis results."""
        if not network_data:
            return 0.0

        total_connections = sum(
            item.get("connection_count", 0) for item in network_data
        )
        max_possible_connections = len(network_data) * (len(network_data) - 1)

        return total_connections / max(1, max_possible_connections)

    def _analyze_context_distribution(self, network_data: List[Dict]) -> Dict[str, int]:
        """Analyze distribution of memories across contexts."""
        context_counts = {}

        for item in network_data:
            context_name = item.get("context_name", "unknown")
            context_counts[context_name] = context_counts.get(context_name, 0) + 1

        return context_counts

    def _analyze_connection_patterns(self, network_data: List[Dict]) -> Dict[str, Any]:
        """Analyze connection patterns in the memory network."""
        if not network_data:
            return {}

        connection_counts = [item.get("connection_count", 0) for item in network_data]

        return {
            "avg_connections": sum(connection_counts) / len(connection_counts),
            "max_connections": max(connection_counts) if connection_counts else 0,
            "highly_connected_nodes": len([c for c in connection_counts if c > 5]),
            "isolated_nodes": len([c for c in connection_counts if c == 0]),
        }

    def _get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """Generate optimization recommendations based on performance metrics."""
        recommendations = []

        # Analyze cache performance
        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        if total_requests > 0:
            cache_hit_rate = self.metrics["cache_hits"] / total_requests

            if cache_hit_rate < 0.7:
                recommendations.append(
                    {
                        "category": "caching",
                        "priority": "high",
                        "recommendation": "Increase graph query cache TTL or review cache key strategies",
                        "current_hit_rate": f"{cache_hit_rate:.2%}",
                    }
                )

        # Analyze query performance
        if self.metrics["avg_query_time_ms"] > 100:
            recommendations.append(
                {
                    "category": "query_optimization",
                    "priority": "medium",
                    "recommendation": "Optimize Cypher queries or add graph database indexes",
                    "current_avg_time": f"{self.metrics['avg_query_time_ms']:.1f}ms",
                }
            )

        return recommendations


# Integration with existing performance system
async def initialize_graph_performance_optimization(redis_client, graph_db_client=None):
    """Initialize graph performance optimization."""
    optimizer = GraphPerformanceOptimizer(redis_client, graph_db_client)

    logger.info(
        "Graph performance optimization initialized",
        features=[
            "graph_query_caching",
            "relationship_optimization",
            "path_traversal_caching",
            "memory_network_analysis",
        ],
    )

    return optimizer
