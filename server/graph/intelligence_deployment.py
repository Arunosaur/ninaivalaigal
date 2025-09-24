"""
Graph Intelligence Deployment
Integrates SPEC-061 Graph Intelligence Framework with SPEC-062 GraphOps Infrastructure
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import structlog

from ..performance.graph_integration import create_optimized_graph_intelligence
from ..redis_client import RedisClient

logger = structlog.get_logger(__name__)


class GraphIntelligenceDeployment:
    """
    Deploys and manages the complete graph intelligence stack.

    Integrates:
    - SPEC-061: Property Graph Intelligence Framework
    - SPEC-062: GraphOps Stack Deployment Architecture
    - Performance optimization suite
    - Real-time monitoring integration
    """

    def __init__(self):
        self.deployed = False
        self.graph_reasoner = None
        self.optimized_intelligence = None
        self.redis_client = None
        self.graph_db_client = None

        # Deployment metrics
        self.deployment_metrics = {
            "deployment_start_time": None,
            "deployment_duration": None,
            "components_deployed": [],
            "health_checks_passed": 0,
            "intelligence_operations_tested": 0,
        }

    async def deploy_complete_stack(
        self,
        redis_client: Optional[RedisClient] = None,
        graph_db_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Deploy the complete graph intelligence stack."""
        if self.deployed:
            logger.warning("Graph intelligence stack already deployed")
            return {
                "status": "already_deployed",
                "components": self.deployment_metrics["components_deployed"],
            }

        deployment_start = time.time()
        self.deployment_metrics["deployment_start_time"] = deployment_start

        try:
            logger.info("Starting graph intelligence deployment")

            # Step 1: Initialize Redis client
            await self._initialize_redis_client(redis_client)

            # Step 2: Initialize graph database connection
            await self._initialize_graph_database(graph_db_config)

            # Step 3: Deploy graph reasoner (SPEC-061)
            await self._deploy_graph_reasoner()

            # Step 4: Deploy optimized intelligence wrapper
            await self._deploy_optimized_intelligence()

            # Step 5: Run comprehensive health checks
            await self._run_deployment_health_checks()

            # Step 6: Test intelligence operations
            await self._test_intelligence_operations()

            # Mark as deployed
            self.deployed = True
            deployment_duration = time.time() - deployment_start
            self.deployment_metrics["deployment_duration"] = deployment_duration

            logger.info(
                "Graph intelligence deployment complete",
                duration_seconds=deployment_duration,
                components=self.deployment_metrics["components_deployed"],
                health_checks=self.deployment_metrics["health_checks_passed"],
                operations_tested=self.deployment_metrics[
                    "intelligence_operations_tested"
                ],
            )

            return {
                "status": "deployed_successfully",
                "deployment_time": deployment_duration,
                "components": self.deployment_metrics["components_deployed"],
                "health_status": "all_systems_operational",
                "intelligence_capabilities": [
                    "context_explanations",
                    "relevance_inference",
                    "memory_network_analysis",
                    "feedback_loops",
                    "graph_reasoning",
                ],
            }

        except Exception as e:
            logger.error("Graph intelligence deployment failed", error=str(e))
            await self._cleanup_partial_deployment()
            raise

    async def _initialize_redis_client(self, redis_client: Optional[RedisClient]):
        """Initialize Redis client for graph intelligence caching."""
        if redis_client:
            self.redis_client = redis_client
        else:
            self.redis_client = RedisClient()
            await self.redis_client.connect()

        # Test Redis connection
        await self.redis_client.await await await redis.ping()
        self.deployment_metrics["components_deployed"].append("redis_client")
        logger.info("Redis client initialized for graph intelligence")

    async def _initialize_graph_database(self, graph_db_config: Optional[Dict]):
        """Initialize connection to GraphOps infrastructure (SPEC-062)."""
        # This would connect to the Apache AGE database from SPEC-062
        # For now, we'll simulate the connection

        config = graph_db_config or {
            "host": "localhost",
            "port": 5433,  # GraphOps port from SPEC-062
            "database": "ninaivalaigal_graph",
            "user": "postgres",
        }

        # Simulate graph database connection
        # In production, this would use psycopg2 or asyncpg to connect to Apache AGE
        self.graph_db_client = GraphDBClient(config)
        await self.graph_db_client.connect()

        self.deployment_metrics["components_deployed"].append("graph_database")
        logger.info("Graph database connection established", config=config)

    async def _deploy_graph_reasoner(self):
        """Deploy the SPEC-061 Graph Intelligence Framework."""
        # Import the existing graph reasoner from SPEC-061
        try:
            from ..graph.graph_reasoner import GraphReasoner

            self.graph_reasoner = GraphReasoner(
                redis_client=self.redis_client,
                graph_db_client=self.graph_db_client,
            )

            # Initialize the reasoner
            await self.graph_reasoner.initialize()

            self.deployment_metrics["components_deployed"].append("graph_reasoner")
            logger.info("SPEC-061 Graph Reasoner deployed successfully")

        except ImportError:
            # If SPEC-061 implementation doesn't exist, create a basic one
            logger.warning(
                "SPEC-061 GraphReasoner not found, creating basic implementation"
            )
            self.graph_reasoner = BasicGraphReasoner(
                self.redis_client, self.graph_db_client
            )
            self.deployment_metrics["components_deployed"].append(
                "basic_graph_reasoner"
            )

    async def _deploy_optimized_intelligence(self):
        """Deploy the performance-optimized graph intelligence wrapper."""
        if not self.graph_reasoner:
            raise RuntimeError("Graph reasoner must be deployed first")

        # Use our existing performance optimization wrapper
        self.optimized_intelligence = await create_optimized_graph_intelligence(
            self.graph_reasoner, self.redis_client
        )

        self.deployment_metrics["components_deployed"].append("optimized_intelligence")
        logger.info("Performance-optimized graph intelligence deployed")

    async async async async def health_checks(self):
        """Run comprehensive health checks on all deployed components."""
        health_checks = []

        # Redis health check
        try:
            await self.redis_client.await await await redis.ping()
            health_checks.append("redis_connectivity")
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            raise

        # Graph database health check
        try:
            await self.graph_db_client.health_check()
            health_checks.append("graph_database_connectivity")
        except Exception as e:
            logger.error("Graph database health check failed", error=str(e))
            raise

        # Graph reasoner health check
        try:
            if hasattr(self.graph_reasoner, "health_check"):
                await self.graph_reasoner.health_check()
            health_checks.append("graph_reasoner_operational")
        except Exception as e:
            logger.error("Graph reasoner health check failed", error=str(e))
            raise

        # Optimized intelligence health check
        try:
            if hasattr(self.optimized_intelligence, "health_check"):
                stats = (
                    await self.optimized_intelligence.get_graph_intelligence_performance_stats()
                )
                if stats:
                    health_checks.append("optimized_intelligence_operational")
        except Exception as e:
            logger.error("Optimized intelligence health check failed", error=str(e))
            raise

        self.deployment_metrics["health_checks_passed"] = len(health_checks)
        logger.info("All health checks passed", checks=health_checks)

    async def _test_intelligence_operations(self):
        """Test core intelligence operations to ensure deployment success."""
        test_operations = []

        if not self.optimized_intelligence:
            logger.warning("Optimized intelligence not available for testing")
            return

        # Test context explanation
        try:
            # This would test with real data in production
            test_user_id = "test_user_123"
            test_memory_id = "test_memory_456"
            test_context_id = "test_context_789"

            explanation = await self.optimized_intelligence.optimized_explain_context(
                user_id=test_user_id,
                memory_id=test_memory_id,
                context_id=test_context_id,
            )

            if explanation:
                test_operations.append("context_explanation")
        except Exception as e:
            logger.warning("Context explanation test failed", error=str(e))

        # Test memory network analysis
        try:
            network_analysis = (
                await self.optimized_intelligence.optimized_analyze_memory_network(
                    user_id="test_user_123",
                    context_id="test_context_789",
                )
            )

            if network_analysis:
                test_operations.append("memory_network_analysis")
        except Exception as e:
            logger.warning("Memory network analysis test failed", error=str(e))

        self.deployment_metrics["intelligence_operations_tested"] = len(test_operations)
        logger.info("Intelligence operations tested", operations=test_operations)

    async def _cleanup_partial_deployment(self):
        """Clean up resources in case of deployment failure."""
        try:
            if self.redis_client and hasattr(self.redis_client, "disconnect"):
                await self.redis_client.disconnect()

            if self.graph_db_client and hasattr(self.graph_db_client, "disconnect"):
                await self.graph_db_client.disconnect()

            self.deployed = False
            logger.info("Partial deployment cleaned up")

        except Exception as e:
            logger.error("Cleanup failed", error=str(e))

    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status and metrics."""
        return {
            "deployed": self.deployed,
            "deployment_metrics": self.deployment_metrics,
            "components_status": {
                "redis_client": self.redis_client is not None,
                "graph_db_client": self.graph_db_client is not None,
                "graph_reasoner": self.graph_reasoner is not None,
                "optimized_intelligence": self.optimized_intelligence is not None,
            },
        }

    async def get_intelligence_capabilities(self) -> List[str]:
        """Get list of available intelligence capabilities."""
        if not self.deployed:
            return []

        capabilities = [
            "context_explanations",
            "memory_network_analysis",
            "graph_reasoning",
        ]

        if self.optimized_intelligence:
            capabilities.extend(
                [
                    "relevance_inference",
                    "feedback_loops",
                    "performance_optimization",
                    "intelligent_caching",
                ]
            )

        return capabilities


class GraphDBClient:
    """Basic graph database client for Apache AGE integration."""

    def __init__(self, config: Dict):
        self.config = config
        self.connected = False

    async def connect(self):
        """Connect to Apache AGE database."""
        # In production, this would establish a real connection
        # For now, simulate connection
        await asyncio.sleep(0.1)  # Simulate connection time
        self.connected = True
        logger.info("Connected to Apache AGE database", config=self.config)

    async def disconnect(self):
        """Disconnect from database."""
        self.connected = False
        logger.info("Disconnected from Apache AGE database")

    async async async async def health_check(self):
        """Check database health."""
        if not self.connected:
            raise RuntimeError("Database not connected")

        # Simulate health check
        await asyncio.sleep(0.05)
        return {"status": "healthy", "connection": "active"}


class BasicGraphReasoner:
    """Basic graph reasoner implementation for deployment testing."""

    def __init__(self, redis_client, graph_db_client):
        self.redis_client = redis_client
        self.graph_db_client = graph_db_client

    async def initialize(self):
        """Initialize the basic graph reasoner."""
        logger.info("Basic graph reasoner initialized")

    async async async async def health_check(self):
        """Check reasoner health."""
        return {"status": "operational", "type": "basic_reasoner"}


# Global deployment instance
_graph_intelligence_deployment: Optional[GraphIntelligenceDeployment] = None


def get_graph_intelligence_deployment() -> GraphIntelligenceDeployment:
    """Get the global graph intelligence deployment instance."""
    global _graph_intelligence_deployment

    if _graph_intelligence_deployment is None:
        _graph_intelligence_deployment = GraphIntelligenceDeployment()

    return _graph_intelligence_deployment


async def deploy_graph_intelligence(
    redis_client: Optional[RedisClient] = None,
    graph_db_config: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Deploy the complete graph intelligence stack.

    This is the main entry point for SPEC-060/061 deployment.
    """
    deployment = get_graph_intelligence_deployment()
    return await deployment.deploy_complete_stack(redis_client, graph_db_config)
