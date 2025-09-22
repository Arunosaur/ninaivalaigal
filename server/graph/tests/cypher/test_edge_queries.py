"""
SPEC-060 Apache AGE Edge Query Tests
Unit tests for edge-level Cypher queries with Redis caching integration
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import our graph models and client
from server.graph.age_client import ApacheAGEClient
from server.graph.models.edge_models import (
    CreatedEdge,
    InfluencesEdge,
    RelationshipType,
    TaggedWithEdge,
    create_created_edge,
    create_influences_edge,
    create_linked_to_edge,
    create_member_of_edge,
    create_triggered_by_edge,
)


class TestEdgeQueries:
    """Test suite for Apache AGE edge queries"""

    @pytest.mark.asyncio
    async def test_create_created_edge(self):
        """Test creating a CREATED relationship edge"""
        try:
            # Create CREATED edge
            created_edge = create_created_edge(
                source_id="user_001",
                target_id="memory_001",
                confidence=0.95,
                weight=1.0,
            )

            # Verify edge properties
            assert created_edge.source_id == "user_001"
            assert created_edge.target_id == "memory_001"
            assert created_edge.relationship_type == RelationshipType.CREATED.value
            assert created_edge.properties["confidence"] == 0.95
            assert created_edge.weight == 1.0

            # Test Cypher generation
            cypher_query = created_edge.to_cypher_create()
            assert "MATCH (a {id: 'user_001'}), (b {id: 'memory_001'})" in cypher_query
            assert "CREATE (a)-[r:CREATED" in cypher_query
            assert "confidence: 0.95" in cypher_query

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    async def test_create_linked_to_edge(self):
        """Test creating a LINKED_TO relationship edge"""
        try:
            # Create LINKED_TO edge
            linked_edge = create_linked_to_edge(
                source_id="memory_001",
                target_id="macro_001",
                relevance="high",
                link_type="semantic",
                weight=0.85,
            )

            # Verify edge properties
            assert linked_edge.source_id == "memory_001"
            assert linked_edge.target_id == "macro_001"
            assert linked_edge.relationship_type == RelationshipType.LINKED_TO.value
            assert linked_edge.properties["relevance"] == "high"
            assert linked_edge.properties["link_type"] == "semantic"
            assert linked_edge.weight == 0.85

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    async def test_create_triggered_by_edge(self):
        """Test creating a TRIGGERED_BY relationship edge"""
        try:
            # Create TRIGGERED_BY edge
            triggered_edge = create_triggered_by_edge(
                source_id="macro_001",
                target_id="agent_001",
                frequency="daily",
                automation_level=0.9,
                weight=1.0,
            )

            # Verify edge properties
            assert triggered_edge.source_id == "macro_001"
            assert triggered_edge.target_id == "agent_001"
            assert (
                triggered_edge.relationship_type == RelationshipType.TRIGGERED_BY.value
            )
            assert triggered_edge.properties["frequency"] == "daily"
            assert triggered_edge.properties["automation_level"] == 0.9

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    async def test_create_member_of_edge(self):
        """Test creating a MEMBER_OF relationship edge"""
        try:
            # Create MEMBER_OF edge
            member_edge = create_member_of_edge(
                source_id="user_001",
                target_id="team_001",
                role="developer",
                permissions="read_write",
                weight=1.0,
            )

            # Verify edge properties
            assert member_edge.source_id == "user_001"
            assert member_edge.target_id == "team_001"
            assert member_edge.relationship_type == RelationshipType.MEMBER_OF.value
            assert member_edge.properties["role"] == "developer"
            assert member_edge.properties["permissions"] == "read_write"
            assert member_edge.properties["active"] is True

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    async def test_create_influences_edge(self):
        """Test creating an INFLUENCES relationship edge"""
        try:
            # Create INFLUENCES edge
            influences_edge = create_influences_edge(
                source_id="memory_001",
                target_id="memory_002",
                influence_type="prerequisite",
                strength=0.8,
                weight=0.75,
            )

            # Verify edge properties
            assert influences_edge.source_id == "memory_001"
            assert influences_edge.target_id == "memory_002"
            assert (
                influences_edge.relationship_type == RelationshipType.INFLUENCES.value
            )
            assert influences_edge.properties["influence_type"] == "prerequisite"
            assert influences_edge.properties["strength"] == 0.8
            assert influences_edge.weight == 0.75

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    @patch("server.graph.age_client.asyncpg.create_pool")
    async def test_age_client_edge_creation(self, mock_create_pool):
        """Test Apache AGE client edge creation with mocked database"""
        try:
            # Mock database connection
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_create_pool.return_value = mock_pool
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

            # Mock successful query execution
            mock_conn.execute.return_value = None
            mock_conn.fetch.return_value = [
                {"result": '{"type": "CREATED", "weight": 1.0}'}
            ]

            # Create AGE client
            client = ApacheAGEClient("postgresql://test:test@localhost/test")

            # Mock Redis cache
            with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                mock_cache.return_value = None

                # Test edge creation
                edge = await client.create_edge(
                    source_id="user_001",
                    target_id="memory_001",
                    relationship="CREATED",
                    properties={"confidence": 0.95},
                    weight=1.0,
                )

                # Verify edge creation
                assert edge.source_id == "user_001"
                assert edge.target_id == "memory_001"
                assert edge.relationship == "CREATED"
                assert edge.weight == 1.0

        except ImportError:
            pytest.skip("AGE client not available for testing")

    @pytest.mark.asyncio
    async def test_graph_traversal_with_edges(self):
        """Test graph traversal using edge relationships"""
        try:
            # Mock database with traversal results
            with patch(
                "server.graph.age_client.asyncpg.create_pool"
            ) as mock_create_pool:
                mock_pool = AsyncMock()
                mock_conn = AsyncMock()
                mock_create_pool.return_value = mock_pool
                mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

                # Mock traversal results with edge information
                mock_conn.execute.return_value = None
                mock_conn.fetch.return_value = [
                    {
                        "result": '{"memory_id": "mem_001", "title": "Redis Setup", "depth": 1, "relationships": [{"type": "CREATED", "weight": 1.0}]}'
                    },
                    {
                        "result": '{"memory_id": "mem_002", "title": "Graph Model", "depth": 2, "relationships": [{"type": "LINKED_TO", "weight": 0.8}]}'
                    },
                ]

                # Mock Redis cache
                with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                    mock_cache.return_value = None

                    client = ApacheAGEClient("postgresql://test:test@localhost/test")

                    # Test connected memories with relationship details
                    results = await client.find_connected_memories(
                        user_id="user_001",
                        max_depth=2,
                        relationship_types=["CREATED", "LINKED_TO"],
                    )

                    # Verify results include relationship information
                    assert len(results) == 2
                    assert "relationships" in results[0]
                    assert results[0]["relationships"][0]["type"] == "CREATED"

        except ImportError:
            pytest.skip("AGE client traversal not available for testing")

    @pytest.mark.asyncio
    async def test_graph_relevance_calculation_with_edges(self):
        """Test graph-based relevance calculation using edge weights"""
        try:
            # Mock database with relevance calculation results
            with patch(
                "server.graph.age_client.asyncpg.create_pool"
            ) as mock_create_pool:
                mock_pool = AsyncMock()
                mock_conn = AsyncMock()
                mock_create_pool.return_value = mock_pool
                mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

                # Mock relevance calculation results
                mock_conn.execute.return_value = None
                mock_conn.fetch.return_value = [
                    {
                        "result": '{"avg_weight": 0.85, "path_length": 2, "edge_count": 3}'
                    }
                ]

                # Mock Redis cache for relevance scores
                with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                    mock_relevance_cache = Mock()
                    mock_relevance_cache.get_score = AsyncMock(return_value=None)
                    mock_relevance_cache.set_score = AsyncMock(return_value=True)
                    mock_cache.return_value = mock_relevance_cache

                    client = ApacheAGEClient("postgresql://test:test@localhost/test")

                    # Test relevance calculation
                    relevance_score = await client.calculate_graph_relevance(
                        user_id="user_001",
                        memory_id="memory_001",
                        context_id="context_001",
                    )

                    # Verify relevance calculation
                    assert isinstance(relevance_score, float)
                    assert 0.0 <= relevance_score <= 1.0

                    # Verify cache operations were called
                    mock_relevance_cache.get_score.assert_called_once()
                    mock_relevance_cache.set_score.assert_called_once()

        except ImportError:
            pytest.skip("AGE client relevance calculation not available for testing")

    @pytest.mark.asyncio
    async def test_edge_property_validation(self):
        """Test edge property validation and Cypher formatting"""
        try:
            # Create edge with complex properties
            tagged_edge = TaggedWithEdge(
                id="",  # Auto-generated
                source_id="memory_001",
                target_id="topic_001",
                relationship_type=RelationshipType.TAGGED_WITH.value,
                relevance=0.9,
                auto_tagged=True,
                confidence=0.85,
                weight=0.8,
            )

            # Test property formatting for Cypher
            cypher_props = tagged_edge.to_cypher_properties()

            # Verify properties are correctly formatted
            assert "relevance: 0.9" in cypher_props
            assert (
                "auto_tagged: True" in cypher_props
                or "auto_tagged: true" in cypher_props
            )
            assert "confidence: 0.85" in cypher_props
            assert "weight: 0.8" in cypher_props

            # Verify structure
            assert cypher_props.startswith("{")
            assert cypher_props.endswith("}")

        except ImportError:
            pytest.skip("Edge models not available for testing")

    @pytest.mark.asyncio
    async def test_edge_timestamp_handling(self):
        """Test automatic timestamp handling in edges"""
        try:
            # Create edge without explicit timestamps
            created_edge = CreatedEdge(
                id="",  # Auto-generated
                source_id="user_001",
                target_id="memory_001",
                relationship_type=RelationshipType.CREATED.value,
                confidence=1.0,
            )

            # Verify timestamps were auto-generated
            assert created_edge.created_at is not None
            assert created_edge.updated_at is not None
            assert isinstance(created_edge.created_at, datetime)
            assert isinstance(created_edge.updated_at, datetime)

            # Verify ID was auto-generated
            assert created_edge.id == "user_001_CREATED_memory_001"

            # Verify timestamps are in properties for Cypher
            cypher_props = created_edge.to_cypher_properties()
            assert "created_at:" in cypher_props
            assert "updated_at:" in cypher_props

        except ImportError:
            pytest.skip("Edge models not available for testing")


class TestEdgeQueryPerformance:
    """Performance tests for edge queries with Redis integration"""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_edge_creation_performance(self, benchmark):
        """Benchmark edge creation performance"""
        try:

            def create_test_edges():
                edges = []
                for i in range(10):
                    edge = create_linked_to_edge(
                        source_id=f"memory_{i}",
                        target_id=f"macro_{i}",
                        relevance="medium",
                        link_type="semantic",
                        weight=0.8,
                    )
                    edges.append(edge)
                return edges

            # Benchmark edge creation
            edges = benchmark(create_test_edges)
            assert len(edges) == 10
            assert all(
                edge.relationship_type == RelationshipType.LINKED_TO.value
                for edge in edges
            )

        except ImportError:
            pytest.skip("Edge models not available for benchmarking")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cypher_edge_formatting_performance(self, benchmark):
        """Benchmark Cypher edge formatting performance"""
        try:
            # Create a complex edge with many properties
            influences_edge = InfluencesEdge(
                id="",  # Auto-generated
                source_id="memory_complex_001",
                target_id="memory_complex_002",
                relationship_type=RelationshipType.INFLUENCES.value,
                influence_type="prerequisite",
                strength=0.75,
                bidirectional=False,
                weight=0.9,
            )

            # Add additional properties
            influences_edge.properties.update(
                {
                    "algorithm": "graph_neural_network",
                    "computed_at": datetime.utcnow().isoformat(),
                    "validation_score": 0.92,
                    "source_confidence": 0.88,
                    "target_confidence": 0.91,
                }
            )

            # Benchmark property formatting
            def format_edge_properties():
                return influences_edge.to_cypher_properties()

            cypher_props = benchmark(format_edge_properties)
            assert isinstance(cypher_props, str)
            assert len(cypher_props) > 100  # Should be substantial

        except ImportError:
            pytest.skip("Edge models not available for benchmarking")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cypher_create_statement_performance(self, benchmark):
        """Benchmark Cypher CREATE statement generation performance"""
        try:
            # Create multiple edge types
            edges = [
                create_created_edge("user_001", "memory_001", confidence=0.95),
                create_linked_to_edge("memory_001", "macro_001", relevance="high"),
                create_triggered_by_edge("macro_001", "agent_001", frequency="daily"),
                create_member_of_edge("user_001", "team_001", role="developer"),
                create_influences_edge("memory_001", "memory_002", strength=0.8),
            ]

            # Benchmark Cypher CREATE statement generation
            def generate_cypher_statements():
                statements = []
                for edge in edges:
                    statement = edge.to_cypher_create()
                    statements.append(statement)
                return statements

            statements = benchmark(generate_cypher_statements)
            assert len(statements) == 5
            assert all("CREATE (a)-[r:" in stmt for stmt in statements)

        except ImportError:
            pytest.skip("Edge models not available for benchmarking")


class TestComplexGraphQueries:
    """Test complex graph queries involving multiple nodes and edges"""

    @pytest.mark.asyncio
    async def test_memory_network_visualization(self):
        """Test getting memory network for visualization"""
        try:
            # Mock database with network results
            with patch(
                "server.graph.age_client.asyncpg.create_pool"
            ) as mock_create_pool:
                mock_pool = AsyncMock()
                mock_conn = AsyncMock()
                mock_create_pool.return_value = mock_pool
                mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

                # Mock network query results
                mock_conn.execute.return_value = None
                mock_conn.fetch.side_effect = [
                    # Nodes query result
                    [
                        {
                            "result": '{"id": "mem_001", "label": "Memory", "properties": {"title": "Redis Setup"}}'
                        },
                        {
                            "result": '{"id": "macro_001", "label": "Macro", "properties": {"name": "Setup Sequence"}}'
                        },
                    ],
                    # Edges query result
                    [
                        {
                            "result": '{"source": "mem_001", "target": "macro_001", "relationship": "LINKED_TO", "weight": 0.9}'
                        }
                    ],
                ]

                # Mock Redis cache
                with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                    mock_cache.return_value = None

                    client = ApacheAGEClient("postgresql://test:test@localhost/test")

                    # Test memory network retrieval
                    network = await client.get_memory_network(
                        user_id="user_001", limit=20
                    )

                    # Verify network structure
                    assert "nodes" in network
                    assert "edges" in network
                    assert "user_id" in network
                    assert "generated_at" in network
                    assert network["user_id"] == "user_001"
                    assert len(network["nodes"]) == 2
                    assert len(network["edges"]) == 1

        except ImportError:
            pytest.skip("AGE client network queries not available for testing")
