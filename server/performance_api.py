"""
Performance API Endpoints
Provides API endpoints for monitoring and managing performance optimizations
"""

from typing import Dict

import structlog
from fastapi import APIRouter, HTTPException

from .performance import get_performance_manager

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/stats")
async def get_performance_stats() -> Dict:
    """
    Get comprehensive performance statistics.

    Returns detailed statistics about:
    - Database connection pools
    - Redis cache performance
    - Query cache statistics
    - Response cache statistics
    - Overall request performance
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        return {
            "status": "success",
            "data": stats,
        }

    except Exception as e:
        logger.error("Failed to get performance stats", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance stats: {str(e)}"
        )


@router.get("/health")
async def get_performance_health() -> Dict:
    """
    Get performance component health status.

    Returns health status for:
    - Database connections
    - Redis connectivity
    - Cache performance
    - Overall system health
    """
    try:
        manager = get_performance_manager()
        health = await manager.health_check()

        status_code = 200 if health["overall_status"] == "healthy" else 503

        return {
            "status": health["overall_status"],
            "data": health,
        }

    except Exception as e:
        logger.error("Failed to get performance health", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance health: {str(e)}"
        )


@router.post("/optimize/database-pools")
async def optimize_database_pools() -> Dict:
    """
    Analyze and optimize database connection pools.

    Returns recommendations for pool size optimization based on usage patterns.
    """
    try:
        manager = get_performance_manager()
        optimization = await manager.optimize_database_pools()

        return {
            "status": "success",
            "data": optimization,
        }

    except Exception as e:
        logger.error("Failed to optimize database pools", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to optimize database pools: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_all_caches() -> Dict:
    """
    Clear all caches for troubleshooting.

    Clears:
    - Query cache
    - Response cache
    - Async optimizer cache
    """
    try:
        manager = get_performance_manager()
        results = await manager.clear_all_caches()

        logger.info("All caches cleared via API", results=results)

        return {
            "status": "success",
            "message": "All caches cleared successfully",
            "data": results,
        }

    except Exception as e:
        logger.error("Failed to clear caches", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clear caches: {str(e)}")


@router.get("/metrics/summary")
async def get_performance_summary() -> Dict:
    """
    Get a summary of key performance metrics.

    Returns high-level performance indicators suitable for dashboards.
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        # Extract key metrics for summary
        summary = {
            "request_performance": {},
            "cache_performance": {},
            "database_performance": {},
            "redis_performance": {},
        }

        # Overall performance
        if "overall" in stats:
            overall = stats["overall"]
            summary["request_performance"] = {
                "total_requests": overall.get("total_requests", 0),
                "avg_response_time_ms": overall.get("avg_response_time_ms", 0),
                "requests_per_second": overall.get("requests_per_second", 0),
                "uptime_seconds": overall.get("uptime_seconds", 0),
            }

        # Cache performance
        if "redis" in stats:
            redis_stats = stats["redis"]
            summary["cache_performance"] = {
                "cache_hit_rate": redis_stats.get("cache_hit_rate", 0),
                "keyspace_hits": redis_stats.get("keyspace_hits", 0),
                "keyspace_misses": redis_stats.get("keyspace_misses", 0),
                "ops_per_second": redis_stats.get("instantaneous_ops_per_sec", 0),
            }

        # Database performance
        if "database" in stats:
            db_stats = stats["database"]
            summary["database_performance"] = {
                "pool_size": db_stats.get("pool_size", 0),
                "checked_out_connections": db_stats.get("checked_out_connections", 0),
                "connections_per_second": db_stats.get("connections_per_second", 0),
                "error_rate": db_stats.get("error_rate", 0),
            }

        # Redis performance
        if "redis" in stats:
            redis_stats = stats["redis"]
            summary["redis_performance"] = {
                "connected_clients": redis_stats.get("connected_clients", 0),
                "used_memory_human": redis_stats.get("used_memory_human", "0B"),
                "ops_per_second": redis_stats.get("instantaneous_ops_per_sec", 0),
            }

        return {
            "status": "success",
            "data": summary,
        }

    except Exception as e:
        logger.error("Failed to get performance summary", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance summary: {str(e)}"
        )


@router.get("/benchmarks")
async def get_performance_benchmarks() -> Dict:
    """
    Get performance benchmarks and targets.

    Returns current performance against established targets.
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        # Define performance targets
        targets = {
            "api_latency_p95_ms": 100,
            "database_query_avg_ms": 50,
            "cache_hit_rate_min": 0.90,
            "memory_usage_max_mb": 512,
            "concurrent_users_target": 1000,
            "throughput_target_rps": 15000,
        }

        # Calculate current performance against targets
        benchmarks = {
            "targets": targets,
            "current": {},
            "status": {},
        }

        # Extract current values
        if "overall" in stats:
            overall = stats["overall"]
            benchmarks["current"]["avg_response_time_ms"] = overall.get(
                "avg_response_time_ms", 0
            )
            benchmarks["current"]["requests_per_second"] = overall.get(
                "requests_per_second", 0
            )

        if "redis" in stats:
            redis_stats = stats["redis"]
            benchmarks["current"]["cache_hit_rate"] = redis_stats.get(
                "cache_hit_rate", 0
            )

        # Calculate status against targets
        current = benchmarks["current"]

        benchmarks["status"]["api_latency"] = (
            "good"
            if current.get("avg_response_time_ms", 0) <= targets["api_latency_p95_ms"]
            else "needs_improvement"
        )

        benchmarks["status"]["cache_performance"] = (
            "good"
            if current.get("cache_hit_rate", 0) >= targets["cache_hit_rate_min"]
            else "needs_improvement"
        )

        benchmarks["status"]["throughput"] = (
            "good"
            if current.get("requests_per_second", 0) >= targets["throughput_target_rps"]
            else "needs_improvement"
        )

        return {
            "status": "success",
            "data": benchmarks,
        }

    except Exception as e:
        logger.error("Failed to get performance benchmarks", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get performance benchmarks: {str(e)}"
        )


@router.get("/recommendations")
async def get_performance_recommendations() -> Dict:
    """
    Get performance optimization recommendations.

    Analyzes current performance and suggests optimizations.
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        recommendations = []

        # Analyze cache performance
        if "redis" in stats:
            redis_stats = stats["redis"]
            hit_rate = redis_stats.get("cache_hit_rate", 0)

            if hit_rate < 0.5:
                recommendations.append(
                    {
                        "category": "caching",
                        "priority": "high",
                        "issue": f"Low cache hit rate: {hit_rate:.2%}",
                        "recommendation": "Review cache TTL settings and cache key strategies",
                        "impact": "High - can significantly improve response times",
                    }
                )

        # Analyze database performance
        if "database" in stats:
            db_stats = stats["database"]
            error_rate = db_stats.get("error_rate", 0)

            if error_rate > 0.05:  # More than 5% error rate
                recommendations.append(
                    {
                        "category": "database",
                        "priority": "high",
                        "issue": f"High database error rate: {error_rate:.2%}",
                        "recommendation": "Investigate database connection issues and optimize queries",
                        "impact": "High - affects application reliability",
                    }
                )

        # Analyze response times
        if "overall" in stats:
            overall = stats["overall"]
            avg_response_time = overall.get("avg_response_time_ms", 0)

            if avg_response_time > 200:  # More than 200ms average
                recommendations.append(
                    {
                        "category": "performance",
                        "priority": "medium",
                        "issue": f"High average response time: {avg_response_time:.1f}ms",
                        "recommendation": "Enable response caching and optimize slow endpoints",
                        "impact": "Medium - improves user experience",
                    }
                )

        # Add general recommendations if no specific issues found
        if not recommendations:
            recommendations.append(
                {
                    "category": "optimization",
                    "priority": "low",
                    "issue": "Performance appears healthy",
                    "recommendation": "Consider implementing predictive caching and load testing",
                    "impact": "Low - proactive optimization",
                }
            )

        return {
            "status": "success",
            "data": {
                "recommendations": recommendations,
                "analysis_timestamp": stats.get("timestamp", "unknown"),
            },
        }

    except Exception as e:
        logger.error("Failed to get performance recommendations", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance recommendations: {str(e)}",
        )


@router.get("/graph/stats")
async def get_graph_performance_stats() -> Dict:
    """
    Get graph database performance statistics.

    Returns detailed statistics about:
    - Graph query performance
    - Graph cache hit rates
    - Apache AGE query optimization
    - Memory network analysis performance
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        # Extract graph-specific stats
        graph_stats = {
            "graph_optimizer": stats.get("graph_optimizer", {}),
            "graph_intelligence": stats.get("graph_intelligence", {}),
        }

        return {
            "status": "success",
            "data": graph_stats,
        }

    except Exception as e:
        logger.error("Failed to get graph performance stats", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph performance stats: {str(e)}"
        )


@router.get("/graph/intelligence/summary")
async def get_graph_intelligence_summary() -> Dict:
    """
    Get summary of graph intelligence performance.

    Returns high-level metrics for:
    - Context explanations
    - Relevance inferences
    - Memory network analyses
    - Feedback loop processing
    """
    try:
        manager = get_performance_manager()

        if not manager.graph_intelligence:
            return {
                "status": "info",
                "message": "Graph intelligence optimization not enabled",
                "data": {},
            }

        stats = (
            await manager.graph_intelligence.get_graph_intelligence_performance_stats()
        )

        # Extract key metrics for summary
        summary = {
            "intelligence_operations": stats.get("intelligence_metrics", {}),
            "performance_summary": stats.get("performance_summary", {}),
            "optimization_impact": stats.get("optimization_impact", {}),
        }

        return {
            "status": "success",
            "data": summary,
        }

    except Exception as e:
        logger.error("Failed to get graph intelligence summary", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph intelligence summary: {str(e)}",
        )


@router.post("/graph/cache/clear")
async def clear_graph_caches() -> Dict:
    """
    Clear graph-specific caches.

    Clears:
    - Graph query cache
    - Context explanation cache
    - Relevance inference cache
    - Memory network analysis cache
    """
    try:
        manager = get_performance_manager()

        if not manager.graph_optimizer:
            return {
                "status": "info",
                "message": "Graph optimizer not initialized",
                "data": {},
            }

        # Clear graph-specific caches
        results = {}

        # Clear all graph caches
        if hasattr(manager.graph_optimizer.query_cache, "clear_all_cache"):
            graph_cleared = await manager.graph_optimizer.query_cache.clear_all_cache()
            results["graph_cache_cleared"] = graph_cleared

        logger.info("Graph caches cleared via API", results=results)

        return {
            "status": "success",
            "message": "Graph caches cleared successfully",
            "data": results,
        }

    except Exception as e:
        logger.error("Failed to clear graph caches", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to clear graph caches: {str(e)}"
        )


@router.get("/graph/benchmarks")
async def get_graph_performance_benchmarks() -> Dict:
    """
    Get graph database performance benchmarks.

    Returns current graph performance against established targets.
    """
    try:
        manager = get_performance_manager()
        stats = await manager.get_comprehensive_stats()

        # Define graph performance targets
        graph_targets = {
            "context_explanation_ms": 100,
            "relevance_inference_ms": 150,
            "memory_network_analysis_ms": 200,
            "graph_cache_hit_rate_min": 0.80,
            "graph_query_avg_ms": 50,
        }

        # Extract current graph performance
        current_graph = {}
        benchmarks = {
            "targets": graph_targets,
            "current": current_graph,
            "status": {},
        }

        # Extract graph intelligence metrics if available
        if "graph_intelligence" in stats:
            intelligence_stats = stats["graph_intelligence"]
            performance_summary = intelligence_stats.get("performance_summary", {})

            current_graph["avg_explanation_time_ms"] = performance_summary.get(
                "avg_explanation_time_ms", 0
            )
            current_graph["avg_inference_time_ms"] = performance_summary.get(
                "avg_inference_time_ms", 0
            )

        # Extract graph optimizer metrics if available
        if "graph_optimizer" in stats:
            optimizer_stats = stats["graph_optimizer"]
            cache_performance = optimizer_stats.get("cache_performance", {})

            current_graph["graph_cache_hit_rate"] = cache_performance.get("hit_rate", 0)
            current_graph["avg_query_time_ms"] = optimizer_stats.get(
                "query_metrics", {}
            ).get("avg_query_time_ms", 0)

        # Calculate status against targets
        benchmarks["status"]["context_explanation"] = (
            "good"
            if current_graph.get("avg_explanation_time_ms", 0)
            <= graph_targets["context_explanation_ms"]
            else "needs_improvement"
        )

        benchmarks["status"]["relevance_inference"] = (
            "good"
            if current_graph.get("avg_inference_time_ms", 0)
            <= graph_targets["relevance_inference_ms"]
            else "needs_improvement"
        )

        benchmarks["status"]["graph_cache_performance"] = (
            "good"
            if current_graph.get("graph_cache_hit_rate", 0)
            >= graph_targets["graph_cache_hit_rate_min"]
            else "needs_improvement"
        )

        return {
            "status": "success",
            "data": benchmarks,
        }

    except Exception as e:
        logger.error("Failed to get graph performance benchmarks", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph performance benchmarks: {str(e)}",
        )


# Add router to main application
def setup_performance_api(app):
    """Set up performance API endpoints."""
    app.include_router(router)
