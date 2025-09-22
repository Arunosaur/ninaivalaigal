"""
Apache AGE Graph Client - SPEC-060 Implementation
Property graph operations with Redis-backed performance optimization
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import asyncpg
import structlog

from server.redis_client import RelevanceScoreCache, get_relevance_cache

logger = structlog.get_logger(__name__)


@dataclass
class GraphNode:
    """Represents a node in the property graph"""

    id: str
    label: str
    properties: dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class GraphEdge:
    """Represents an edge in the property graph"""

    id: str
    source_id: str
    target_id: str
    relationship: str
    properties: dict[str, Any]
    weight: float = 1.0
    created_at: Optional[datetime] = None


class ApacheAGEClient:
    """
    Apache AGE client with Redis-backed caching for SPEC-060 implementation
    Provides property graph operations with performance optimization
    """

    def __init__(self, database_url: str, graph_name: str = "ninaivalaigal_graph"):
        self.database_url = database_url
        self.graph_name = graph_name
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.relevance_cache: Optional[RelevanceScoreCache] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Apache AGE client and Redis cache"""
        try:
            # Initialize database connection pool
            self.connection_pool = await asyncpg.create_pool(
                self.database_url, min_size=5, max_size=20, command_timeout=30
            )

            # Initialize Redis cache for graph operations
            self.relevance_cache = await get_relevance_cache()

            # Create AGE extension and graph if not exists
            await self._setup_age_extension()
            await self._create_graph()

            self._initialized = True
            logger.info(
                "Apache AGE client initialized",
                graph_name=self.graph_name,
                redis_cache_enabled=self.relevance_cache is not None,
            )

        except Exception as e:
            logger.error("Failed to initialize Apache AGE client", error=str(e))
            raise

    async def _setup_age_extension(self) -> None:
        """Setup Apache AGE extension in PostgreSQL"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Create AGE extension if not exists
                await conn.execute("CREATE EXTENSION IF NOT EXISTS age;")

                # Load AGE into search path
                await conn.execute("LOAD 'age';")
                await conn.execute("SET search_path = ag_catalog, '$user', public;")

                logger.info("Apache AGE extension setup complete")

            except Exception as e:
                logger.error("Failed to setup AGE extension", error=str(e))
                raise

    async def _create_graph(self) -> None:
        """Create the property graph if it doesn't exist"""
        async with self.connection_pool.acquire() as conn:
            try:
                # Create graph using AGE function
                query = f"SELECT create_graph('{self.graph_name}');"
                await conn.execute(query)

                logger.info("Property graph created", graph_name=self.graph_name)

            except asyncpg.exceptions.DuplicateObjectError:
                # Graph already exists
                logger.debug(
                    "Property graph already exists", graph_name=self.graph_name
                )
            except Exception as e:
                logger.error("Failed to create graph", error=str(e))
                raise

    async def execute_cypher(
        self,
        cypher_query: str,
        parameters: Optional[dict[str, Any]] = None,
        cache_key: Optional[str] = None,
        cache_ttl: int = 300,
    ) -> list[dict[str, Any]]:
        """
        Execute Cypher query with Redis caching for performance

        Args:
            cypher_query: Cypher query string
            parameters: Query parameters
            cache_key: Optional cache key for Redis
            cache_ttl: Cache TTL in seconds (default 5 minutes)
        """
        if not self._initialized:
            await self.initialize()

        # Check Redis cache first if cache_key provided
        if cache_key and self.relevance_cache:
            try:
                cached_result = await self.relevance_cache.redis.redis.get(
                    f"cypher:{cache_key}"
                )
                if cached_result:
                    logger.debug("Cypher query cache hit", cache_key=cache_key)
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning("Cache lookup failed", error=str(e))

        async with self.connection_pool.acquire() as conn:
            try:
                # Prepare AGE query with graph context
                age_query = f"""
                SELECT * FROM cypher('{self.graph_name}', $$
                {cypher_query}
                $$) as (result agtype);
                """

                # Execute query
                start_time = datetime.utcnow()
                rows = await conn.fetch(age_query)
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Process results
                results = []
                for row in rows:
                    if row["result"]:
                        # Parse AGE result format
                        result_data = json.loads(str(row["result"]))
                        results.append(result_data)

                logger.info(
                    "Cypher query executed",
                    query_length=len(cypher_query),
                    result_count=len(results),
                    execution_time_ms=round(execution_time, 2),
                )

                # Cache result if cache_key provided
                if cache_key and self.relevance_cache and results:
                    try:
                        await self.relevance_cache.redis.redis.setex(
                            f"cypher:{cache_key}", cache_ttl, json.dumps(results)
                        )
                        logger.debug("Cypher result cached", cache_key=cache_key)
                    except Exception as e:
                        logger.warning("Cache storage failed", error=str(e))

                return results

            except Exception as e:
                logger.error(
                    "Cypher query execution failed", query=cypher_query, error=str(e)
                )
                raise

    async def create_node(
        self, label: str, properties: dict[str, Any], node_id: Optional[str] = None
    ) -> GraphNode:
        """Create a new node in the property graph"""
        if not node_id:
            node_id = f"{label.lower()}_{datetime.utcnow().timestamp()}"

        # Add metadata
        properties.update(
            {
                "id": node_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        )

        # Build Cypher CREATE query
        props_str = json.dumps(properties).replace('"', "'")
        cypher_query = f"CREATE (n:{label} {props_str}) RETURN n"

        results = await self.execute_cypher(cypher_query)

        logger.info(
            "Graph node created",
            label=label,
            node_id=node_id,
            properties_count=len(properties),
        )

        return GraphNode(
            id=node_id, label=label, properties=properties, created_at=datetime.utcnow()
        )

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        properties: Optional[dict[str, Any]] = None,
        weight: float = 1.0,
    ) -> GraphEdge:
        """Create a new edge between nodes"""
        if properties is None:
            properties = {}

        # Add metadata
        properties.update(
            {"weight": weight, "created_at": datetime.utcnow().isoformat()}
        )

        # Build Cypher MATCH and CREATE query
        props_str = json.dumps(properties).replace('"', "'")
        cypher_query = f"""
        MATCH (a {{id: '{source_id}'}}), (b {{id: '{target_id}'}})
        CREATE (a)-[r:{relationship} {props_str}]->(b)
        RETURN r
        """

        results = await self.execute_cypher(cypher_query)

        edge_id = f"{source_id}_{relationship}_{target_id}"

        logger.info(
            "Graph edge created",
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            weight=weight,
        )

        return GraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship=relationship,
            properties=properties,
            weight=weight,
            created_at=datetime.utcnow(),
        )

    async def find_connected_memories(
        self,
        user_id: str,
        max_depth: int = 3,
        relationship_types: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        Find memories connected to a user through graph traversal
        Uses Redis caching for performance optimization
        """
        cache_key = f"connected_memories:{user_id}:{max_depth}"

        if relationship_types is None:
            relationship_types = ["CREATED", "LINKED_TO", "TAGGED_WITH"]

        # Build dynamic Cypher query for traversal
        rel_pattern = "|".join(relationship_types)
        cypher_query = f"""
        MATCH path = (u:User {{id: '{user_id}'}})-[:{rel_pattern}*1..{max_depth}]->(m:Memory)
        RETURN m.id as memory_id, m.title as title, m.type as type,
               length(path) as depth, relationships(path) as relationships
        ORDER BY depth ASC
        LIMIT 50
        """

        return await self.execute_cypher(
            cypher_query,
            cache_key=cache_key,
            cache_ttl=600,  # 10 minutes cache for connected memories
        )

    async def calculate_graph_relevance(
        self, user_id: str, memory_id: str, context_id: Optional[str] = None
    ) -> float:
        """
        Calculate relevance score using graph traversal and edge weights
        Integrates with SPEC-031 relevance scoring and Redis caching
        """
        cache_key = f"graph_relevance:{user_id}:{memory_id}:{context_id or 'default'}"

        # Check if we have cached relevance score
        if self.relevance_cache:
            cached_score = await self.relevance_cache.get_score(
                user_id, context_id or "graph", memory_id
            )
            if cached_score is not None:
                return cached_score

        # Calculate relevance using graph traversal
        cypher_query = f"""
        MATCH path = (u:User {{id: '{user_id}'}})-[*1..3]->(m:Memory {{id: '{memory_id}'}})
        WITH path, relationships(path) as rels
        UNWIND rels as rel
        RETURN avg(rel.weight) as avg_weight, length(path) as path_length, count(rels) as edge_count
        """

        results = await self.execute_cypher(cypher_query, cache_key=cache_key)

        if not results:
            return 0.0

        # Calculate relevance score based on graph metrics
        result = results[0]
        avg_weight = float(result.get("avg_weight", 0.5))
        path_length = int(result.get("path_length", 999))
        edge_count = int(result.get("edge_count", 0))

        # Relevance formula: weighted by path distance and edge weights
        relevance_score = (avg_weight * edge_count) / max(path_length, 1)
        relevance_score = min(relevance_score, 1.0)  # Cap at 1.0

        # Cache the computed score using SPEC-033 Redis integration
        if self.relevance_cache:
            await self.relevance_cache.set_score(
                user_id, context_id or "graph", memory_id, relevance_score, ttl=900
            )

        logger.debug(
            "Graph relevance calculated",
            user_id=user_id,
            memory_id=memory_id,
            relevance_score=relevance_score,
            avg_weight=avg_weight,
            path_length=path_length,
        )

        return relevance_score

    async def get_memory_network(self, user_id: str, limit: int = 20) -> dict[str, Any]:
        """
        Get the memory network graph for a user
        Returns nodes and edges for visualization
        """
        cache_key = f"memory_network:{user_id}:{limit}"

        # Get nodes (memories, macros, topics, etc.)
        nodes_query = f"""
        MATCH (u:User {{id: '{user_id}'}})-[:CREATED|LINKED_TO*1..2]->(n)
        RETURN DISTINCT n.id as id, labels(n)[0] as label, n as properties
        LIMIT {limit}
        """

        # Get edges between these nodes
        edges_query = f"""
        MATCH (u:User {{id: '{user_id}'}})-[:CREATED|LINKED_TO*1..2]->(n1)
        MATCH (n1)-[r]->(n2)
        WHERE n2.id IS NOT NULL
        RETURN n1.id as source, n2.id as target, type(r) as relationship,
               r.weight as weight, r as properties
        LIMIT {limit * 2}
        """

        # Execute both queries with caching
        nodes_results = await self.execute_cypher(
            nodes_query, cache_key=f"{cache_key}_nodes", cache_ttl=300
        )

        edges_results = await self.execute_cypher(
            edges_query, cache_key=f"{cache_key}_edges", cache_ttl=300
        )

        return {
            "nodes": nodes_results,
            "edges": edges_results,
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def close(self) -> None:
        """Close database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Apache AGE client connections closed")


# Global AGE client instance
age_client: Optional[ApacheAGEClient] = None


async def get_age_client() -> ApacheAGEClient:
    """Dependency injection for Apache AGE client"""
    global age_client

    if age_client is None:
        # Get database URL from environment or use default
        import os

        database_url = os.getenv(
            "DATABASE_URL", "postgresql://mem0user:mem0pass@localhost:5432/mem0db"
        )

        age_client = ApacheAGEClient(database_url)
        await age_client.initialize()

    return age_client


# Convenience functions for common graph operations
async def create_memory_node(
    memory_id: str,
    title: str,
    content: str,
    memory_type: str = "core",
    user_id: Optional[str] = None,
) -> GraphNode:
    """Create a memory node in the property graph"""
    client = await get_age_client()

    properties = {
        "title": title,
        "content": content[:500],  # Truncate for graph storage
        "type": memory_type,
    }

    node = await client.create_node("Memory", properties, memory_id)

    # Create user relationship if provided
    if user_id:
        await client.create_edge(user_id, memory_id, "CREATED")

    return node


async def link_memories(
    source_memory_id: str,
    target_memory_id: str,
    relationship: str = "LINKED_TO",
    weight: float = 1.0,
) -> GraphEdge:
    """Link two memories in the property graph"""
    client = await get_age_client()

    return await client.create_edge(
        source_memory_id, target_memory_id, relationship, weight=weight
    )


async def get_user_memory_graph(user_id: str) -> dict[str, Any]:
    """Get the complete memory graph for a user"""
    client = await get_age_client()

    return await client.get_memory_network(user_id)
