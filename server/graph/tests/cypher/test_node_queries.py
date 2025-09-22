"""
SPEC-060 Apache AGE Node Query Tests
Unit tests for node-level Cypher queries with Redis caching integration
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import our graph models and client
from server.graph.age_client import ApacheAGEClient
from server.graph.models.node_models import (
    AgentType,
    MemoryNode,
    MemoryType,
    NodeType,
    UserNode,
    create_agent_node,
    create_macro_node,
    create_memory_node,
    create_user_node,
)


class TestNodeQueries:
    """Test suite for Apache AGE node queries"""

    @pytest.mark.asyncio
    async def test_create_user_node_query(self):
        """Test creating a user node with Cypher"""
        try:
            # Create user node model
            user_node = create_user_node(
                user_id="test_user_1",
                name="Test User",
                email="test@medhasys.com",
                role="developer",
            )

            # Verify node properties
            assert user_node.id == "test_user_1"
            assert user_node.label == NodeType.USER.value
            assert user_node.properties["name"] == "Test User"
            assert user_node.properties["email"] == "test@medhasys.com"
            assert user_node.properties["role"] == "developer"

            # Test Cypher property formatting
            cypher_props = user_node.to_cypher_properties()
            assert "id: 'test_user_1'" in cypher_props
            assert "name: 'Test User'" in cypher_props

        except ImportError:
            pytest.skip("Graph models not available for testing")

    @pytest.mark.asyncio
    async def test_create_memory_node_query(self):
        """Test creating a memory node with different types"""
        try:
            # Create core memory node
            memory_node = create_memory_node(
                memory_id="mem_001",
                title="Redis Integration",
                content="SPEC-033 implementation details for Redis caching",
                memory_type=MemoryType.CORE,
                user_id="test_user_1",
                relevance_score=0.95,
            )

            # Verify node properties
            assert memory_node.id == "mem_001"
            assert memory_node.label == NodeType.MEMORY.value
            assert memory_node.properties["type"] == MemoryType.CORE.value
            assert memory_node.properties["relevance_score"] == 0.95
            assert memory_node.properties["user_id"] == "test_user_1"

            # Test content truncation for graph storage
            assert len(memory_node.properties["content"]) <= 1000

        except ImportError:
            pytest.skip("Graph models not available for testing")

    @pytest.mark.asyncio
    async def test_create_macro_node_query(self):
        """Test creating a macro node with automation properties"""
        try:
            # Create macro node
            macro_node = create_macro_node(
                macro_id="macro_setup_001",
                name="Infrastructure Setup",
                description="Automated infrastructure deployment sequence",
                tag="deployment",
                automation_level=0.85,
                trigger_frequency="daily",
                user_id="test_user_1",
            )

            # Verify node properties
            assert macro_node.id == "macro_setup_001"
            assert macro_node.label == NodeType.MACRO.value
            assert macro_node.properties["automation_level"] == 0.85
            assert macro_node.properties["trigger_frequency"] == "daily"

        except ImportError:
            pytest.skip("Graph models not available for testing")

    @pytest.mark.asyncio
    async def test_create_agent_node_query(self):
        """Test creating an agent node with capabilities"""
        try:
            # Create AI assistant agent
            agent_node = create_agent_node(
                agent_id="agent_em_001",
                name="eM Assistant",
                agent_type=AgentType.AI_ASSISTANT,
                capabilities="memory_management,context_analysis,relevance_scoring",
                version="2.0",
                active=True,
            )

            # Verify node properties
            assert agent_node.id == "agent_em_001"
            assert agent_node.label == NodeType.AGENT.value
            assert agent_node.properties["type"] == AgentType.AI_ASSISTANT.value
            assert agent_node.properties["active"] is True
            assert "memory_management" in agent_node.properties["capabilities"]

        except ImportError:
            pytest.skip("Graph models not available for testing")

    @pytest.mark.asyncio
    @patch("server.graph.age_client.asyncpg.create_pool")
    async def test_age_client_node_creation(self, mock_create_pool):
        """Test Apache AGE client node creation with mocked database"""
        try:
            # Mock database connection
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_create_pool.return_value = mock_pool
            mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

            # Mock successful query execution
            mock_conn.execute.return_value = None
            mock_conn.fetch.return_value = [
                {"result": '{"id": "test_user_1", "name": "Test User"}'}
            ]

            # Create AGE client
            client = ApacheAGEClient("postgresql://test:test@localhost/test")

            # Mock Redis cache
            with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                mock_cache.return_value = None

                # Test node creation
                node = await client.create_node(
                    "User",
                    {
                        "name": "Test User",
                        "email": "test@medhasys.com",
                        "role": "developer",
                    },
                    "test_user_1",
                )

                # Verify node creation
                assert node.id == "test_user_1"
                assert node.label == "User"
                assert node.properties["name"] == "Test User"

        except ImportError:
            pytest.skip("AGE client not available for testing")

    @pytest.mark.asyncio
    async def test_node_query_caching(self):
        """Test Redis caching for node queries"""
        try:
            # Mock Redis cache
            mock_cache = Mock()
            mock_cache.redis.redis.get = AsyncMock(return_value=None)
            mock_cache.redis.redis.setex = AsyncMock(return_value=True)

            with patch("server.graph.age_client.get_relevance_cache") as mock_get_cache:
                mock_get_cache.return_value = mock_cache

                # Mock database operations
                with patch(
                    "server.graph.age_client.asyncpg.create_pool"
                ) as mock_create_pool:
                    mock_pool = AsyncMock()
                    mock_conn = AsyncMock()
                    mock_create_pool.return_value = mock_pool
                    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

                    mock_conn.execute.return_value = None
                    mock_conn.fetch.return_value = [
                        {
                            "result": '{"nodes": [{"id": "test_user_1", "label": "User"}]}'
                        }
                    ]

                    # Create client and execute cached query
                    client = ApacheAGEClient("postgresql://test:test@localhost/test")

                    # Execute query with caching
                    results = await client.execute_cypher(
                        "MATCH (n:User) RETURN n LIMIT 5",
                        cache_key="test_user_nodes",
                        cache_ttl=300,
                    )

                    # Verify cache was attempted
                    mock_cache.redis.redis.get.assert_called_once()

        except ImportError:
            pytest.skip("AGE client caching not available for testing")

    @pytest.mark.asyncio
    async def test_complex_node_traversal_query(self):
        """Test complex node traversal with multiple node types"""
        try:
            # Mock database with complex query results
            with patch(
                "server.graph.age_client.asyncpg.create_pool"
            ) as mock_create_pool:
                mock_pool = AsyncMock()
                mock_conn = AsyncMock()
                mock_create_pool.return_value = mock_pool
                mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

                # Mock complex traversal results
                mock_conn.execute.return_value = None
                mock_conn.fetch.return_value = [
                    {
                        "result": '{"memory_id": "mem_001", "title": "Redis Setup", "depth": 1}'
                    },
                    {
                        "result": '{"memory_id": "mem_002", "title": "Graph Model", "depth": 2}'
                    },
                ]

                # Mock Redis cache
                with patch("server.graph.age_client.get_relevance_cache") as mock_cache:
                    mock_cache.return_value = None

                    client = ApacheAGEClient("postgresql://test:test@localhost/test")

                    # Test connected memories traversal
                    results = await client.find_connected_memories(
                        user_id="test_user_1",
                        max_depth=3,
                        relationship_types=["CREATED", "LINKED_TO"],
                    )

                    # Verify results structure
                    assert len(results) == 2
                    assert results[0]["memory_id"] == "mem_001"
                    assert results[1]["depth"] == 2

        except ImportError:
            pytest.skip("AGE client traversal not available for testing")

    @pytest.mark.asyncio
    async def test_node_property_validation(self):
        """Test node property validation and formatting"""
        try:
            # Test user node with various property types
            user_node = UserNode(
                id="validation_test_user",
                label=NodeType.USER.value,
                name="Validation User",
                email="validation@test.com",
                role="admin",
                team_id="team_001",
                organization_id="org_001",
            )

            # Test property formatting for Cypher
            cypher_props = user_node.to_cypher_properties()

            # Verify string properties are quoted
            assert "'Validation User'" in cypher_props
            assert "'validation@test.com'" in cypher_props
            assert "'admin'" in cypher_props

            # Verify structure
            assert cypher_props.startswith("{")
            assert cypher_props.endswith("}")
            assert "id:" in cypher_props

        except ImportError:
            pytest.skip("Node models not available for testing")

    @pytest.mark.asyncio
    async def test_node_timestamp_handling(self):
        """Test automatic timestamp handling in nodes"""
        try:
            # Create node without explicit timestamps
            memory_node = MemoryNode(
                id="timestamp_test_mem",
                label=NodeType.MEMORY.value,
                title="Timestamp Test",
                content="Testing automatic timestamp generation",
                memory_type=MemoryType.CORE,
            )

            # Verify timestamps were auto-generated
            assert memory_node.created_at is not None
            assert memory_node.updated_at is not None
            assert isinstance(memory_node.created_at, datetime)
            assert isinstance(memory_node.updated_at, datetime)

            # Verify timestamps are in properties for Cypher
            cypher_props = memory_node.to_cypher_properties()
            assert "created_at:" in cypher_props
            assert "updated_at:" in cypher_props

        except ImportError:
            pytest.skip("Node models not available for testing")


class TestNodeQueryPerformance:
    """Performance tests for node queries with Redis integration"""

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_node_creation_performance(self, benchmark):
        """Benchmark node creation performance"""
        try:

            def create_test_nodes():
                nodes = []
                for i in range(10):
                    node = create_memory_node(
                        memory_id=f"perf_mem_{i}",
                        title=f"Performance Test Memory {i}",
                        content=f"Content for performance test memory {i}",
                        memory_type=MemoryType.CORE,
                        relevance_score=0.8,
                    )
                    nodes.append(node)
                return nodes

            # Benchmark node creation
            nodes = benchmark(create_test_nodes)
            assert len(nodes) == 10
            assert all(node.label == NodeType.MEMORY.value for node in nodes)

        except ImportError:
            pytest.skip("Node models not available for benchmarking")

    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_cypher_property_formatting_performance(self, benchmark):
        """Benchmark Cypher property formatting performance"""
        try:
            # Create a complex node with many properties
            user_node = UserNode(
                id="perf_user_001",
                label=NodeType.USER.value,
                name="Performance Test User",
                email="perf@test.com",
                role="developer",
                team_id="team_perf_001",
                organization_id="org_perf_001",
            )

            # Add additional properties
            user_node.properties.update(
                {
                    "department": "Engineering",
                    "location": "San Francisco",
                    "skills": "Python,JavaScript,Go",
                    "experience_years": 5,
                    "active": True,
                    "last_login": datetime.utcnow().isoformat(),
                }
            )

            # Benchmark property formatting
            def format_properties():
                return user_node.to_cypher_properties()

            cypher_props = benchmark(format_properties)
            assert isinstance(cypher_props, str)
            assert len(cypher_props) > 100  # Should be substantial

        except ImportError:
            pytest.skip("Node models not available for benchmarking")
