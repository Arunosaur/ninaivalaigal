#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Graph Ranking System - PageRank for Memory Intelligence
Ranks memories and contexts based on connections, discussions, and approvals
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from auth_utils import get_current_user
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/graph-rank", tags=["ai-intelligence"])

# Mock graph data - in real implementation, build from memory, context, approval, discussion systems
GRAPH_NODES = {
    # Memory nodes
    "memory_1": {
        "id": "memory_1",
        "type": "memory",
        "title": "Authentication Performance Note",
        "content": "Remember to implement async authentication for better performance",
        "user_id": 123,
        "team_id": None,
        "created_at": "2025-01-15T10:00:00Z",
        "tags": ["development", "authentication", "performance"],
        "approval_status": None,
        "discussion_count": 1,
        "sentiment_score": 0.7,
    },
    "memory_2": {
        "id": "memory_2",
        "type": "memory",
        "title": "GET-based Endpoints Decision",
        "content": "Team decision: Use GET-based endpoints for MVP to bypass POST issues",
        "user_id": 123,
        "team_id": 1,
        "created_at": "2025-01-20T14:20:00Z",
        "tags": ["team-decision", "architecture", "mvp"],
        "approval_status": "approved",
        "discussion_count": 3,
        "sentiment_score": 0.9,
    },
    "memory_3": {
        "id": "memory_3",
        "type": "memory",
        "title": "Code Review Results",
        "content": "Code review: Auth system looks solid, ready for production",
        "user_id": 456,
        "team_id": 1,
        "created_at": "2025-01-25T14:30:00Z",
        "tags": ["code-review", "authentication", "production"],
        "approval_status": "approved",
        "discussion_count": 2,
        "sentiment_score": 0.8,
    },
    # Context nodes
    "context_1": {
        "id": "context_1",
        "type": "context",
        "title": "Auth System Development",
        "description": "All memories related to authentication system development",
        "user_id": 123,
        "team_id": 1,
        "created_at": "2025-01-20T14:30:00Z",
        "tags": ["authentication", "development", "security"],
        "memory_count": 3,
        "discussion_count": 5,
    },
    # User nodes
    "user_123": {
        "id": "user_123",
        "type": "user",
        "name": "Team Admin",
        "role": "team_admin",
        "team_id": 1,
        "activity_score": 0.9,
    },
    "user_456": {
        "id": "user_456",
        "type": "user",
        "name": "Project Owner",
        "role": "team_admin",
        "team_id": 1,
        "activity_score": 0.7,
    },
}

# Graph edges with weights
GRAPH_EDGES = [
    # Memory-Context relationships
    {"source": "memory_1", "target": "context_1", "type": "belongs_to", "weight": 0.95},
    {"source": "memory_2", "target": "context_1", "type": "belongs_to", "weight": 0.90},
    {"source": "memory_3", "target": "context_1", "type": "belongs_to", "weight": 0.88},
    # User-Memory relationships (authorship)
    {"source": "user_123", "target": "memory_1", "type": "authored", "weight": 1.0},
    {"source": "user_123", "target": "memory_2", "type": "authored", "weight": 1.0},
    {"source": "user_456", "target": "memory_3", "type": "authored", "weight": 1.0},
    # User-Context relationships
    {"source": "user_123", "target": "context_1", "type": "created", "weight": 1.0},
    # Discussion relationships (comments create connections)
    {
        "source": "memory_2",
        "target": "memory_1",
        "type": "discussed_with",
        "weight": 0.6,
    },
    {
        "source": "memory_3",
        "target": "memory_2",
        "type": "discussed_with",
        "weight": 0.7,
    },
    # Approval relationships
    {"source": "user_456", "target": "memory_2", "type": "approved", "weight": 0.8},
    {"source": "user_123", "target": "memory_3", "type": "approved", "weight": 0.8},
]


def calculate_pagerank(
    nodes: Dict,
    edges: List[Dict],
    damping_factor: float = 0.85,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> Dict[str, float]:
    """Calculate PageRank scores for graph nodes"""

    # Initialize PageRank scores
    node_ids = list(nodes.keys())
    num_nodes = len(node_ids)
    pagerank = {node_id: 1.0 / num_nodes for node_id in node_ids}

    # Build adjacency structure
    outgoing_links = {node_id: [] for node_id in node_ids}
    incoming_links = {node_id: [] for node_id in node_ids}

    for edge in edges:
        source, target = edge["source"], edge["target"]
        if source in nodes and target in nodes:
            weight = edge.get("weight", 1.0)
            outgoing_links[source].append({"target": target, "weight": weight})
            incoming_links[target].append({"source": source, "weight": weight})

    # PageRank iterations
    for _iteration in range(max_iterations):
        new_pagerank = {}

        for node_id in node_ids:
            # Base probability (random jump)
            rank = (1 - damping_factor) / num_nodes

            # Add rank from incoming links
            for link in incoming_links[node_id]:
                source_id = link["source"]
                weight = link["weight"]

                # Calculate outgoing weight sum for source
                outgoing_weight_sum = sum(link["weight"] for link in outgoing_links[source_id])

                if outgoing_weight_sum > 0:
                    rank += damping_factor * pagerank[source_id] * (weight / outgoing_weight_sum)

            new_pagerank[node_id] = rank

        # Check convergence
        max_change = max(abs(new_pagerank[node_id] - pagerank[node_id]) for node_id in node_ids)
        if max_change < tolerance:
            break

        pagerank = new_pagerank

    return pagerank


def calculate_enhanced_scores(nodes: Dict, pagerank_scores: Dict[str, float]) -> Dict[str, Dict]:
    """Calculate enhanced ranking scores combining PageRank with other signals"""

    enhanced_scores = {}

    for node_id, node in nodes.items():
        base_pagerank = pagerank_scores.get(node_id, 0.0)

        # Memory-specific enhancements
        if node["type"] == "memory":
            # Discussion boost
            discussion_boost = min(node.get("discussion_count", 0) * 0.1, 0.5)

            # Sentiment boost
            sentiment_boost = (node.get("sentiment_score", 0.5) - 0.5) * 0.3

            # Approval boost
            approval_boost = 0.2 if node.get("approval_status") == "approved" else 0.0

            # Recency factor (newer memories get slight boost)
            created_date = datetime.fromisoformat(node["created_at"].replace("Z", "+00:00"))
            days_old = (datetime.utcnow() - created_date).days
            recency_boost = max(0, (30 - days_old) / 30 * 0.1)  # Boost for memories < 30 days old

            enhanced_score = base_pagerank + discussion_boost + sentiment_boost + approval_boost + recency_boost

            enhanced_scores[node_id] = {
                "base_pagerank": base_pagerank,
                "discussion_boost": discussion_boost,
                "sentiment_boost": sentiment_boost,
                "approval_boost": approval_boost,
                "recency_boost": recency_boost,
                "final_score": enhanced_score,
                "node": node,
            }

        # Context-specific enhancements
        elif node["type"] == "context":
            # Memory count boost
            memory_boost = min(node.get("memory_count", 0) * 0.05, 0.3)

            # Discussion activity boost
            discussion_boost = min(node.get("discussion_count", 0) * 0.02, 0.2)

            enhanced_score = base_pagerank + memory_boost + discussion_boost

            enhanced_scores[node_id] = {
                "base_pagerank": base_pagerank,
                "memory_boost": memory_boost,
                "discussion_boost": discussion_boost,
                "final_score": enhanced_score,
                "node": node,
            }

        # User-specific enhancements
        elif node["type"] == "user":
            # Activity boost
            activity_boost = node.get("activity_score", 0.5) * 0.2

            enhanced_score = base_pagerank + activity_boost

            enhanced_scores[node_id] = {
                "base_pagerank": base_pagerank,
                "activity_boost": activity_boost,
                "final_score": enhanced_score,
                "node": node,
            }

    return enhanced_scores


@router.get("/memories")
async def get_ranked_memories(
    limit: int = 10,
    team_filter: Optional[int] = None,
    include_scores: bool = False,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get memories ranked by PageRank and enhanced signals"""

    # Calculate PageRank
    pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)

    # Calculate enhanced scores
    enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

    # Filter memories and apply team filter
    memory_scores = []
    for node_id, score_data in enhanced_scores.items():
        node = score_data["node"]
        if node["type"] == "memory":
            # Apply team filter
            if team_filter is not None and node.get("team_id") != team_filter:
                continue

            memory_scores.append(
                {
                    "memory_id": node_id,
                    "title": node["title"],
                    "content": node["content"],
                    "tags": node["tags"],
                    "created_at": node["created_at"],
                    "approval_status": node.get("approval_status"),
                    "discussion_count": node.get("discussion_count", 0),
                    "sentiment_score": node.get("sentiment_score", 0.5),
                    "rank_score": score_data["final_score"],
                    "score_breakdown": (
                        {
                            "pagerank": score_data["base_pagerank"],
                            "discussion_boost": score_data["discussion_boost"],
                            "sentiment_boost": score_data["sentiment_boost"],
                            "approval_boost": score_data["approval_boost"],
                            "recency_boost": score_data["recency_boost"],
                        }
                        if include_scores
                        else None
                    ),
                }
            )

    # Sort by rank score (highest first)
    memory_scores.sort(key=lambda x: x["rank_score"], reverse=True)

    # Apply limit
    ranked_memories = memory_scores[:limit]

    return {
        "success": True,
        "ranked_memories": ranked_memories,
        "total_memories": len(memory_scores),
        "ranking_algorithm": {
            "base": "PageRank",
            "enhancements": [
                "discussion_activity",
                "sentiment_analysis",
                "approval_status",
                "recency",
            ],
            "damping_factor": 0.85,
        },
        "filters": {"team_filter": team_filter, "limit": limit},
    }


@router.get("/contexts")
async def get_ranked_contexts(
    limit: int = 10,
    team_filter: Optional[int] = None,
    include_scores: bool = False,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get contexts ranked by PageRank and enhanced signals"""

    # Calculate PageRank
    pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)

    # Calculate enhanced scores
    enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

    # Filter contexts
    context_scores = []
    for node_id, score_data in enhanced_scores.items():
        node = score_data["node"]
        if node["type"] == "context":
            # Apply team filter
            if team_filter is not None and node.get("team_id") != team_filter:
                continue

            context_scores.append(
                {
                    "context_id": node_id,
                    "title": node["title"],
                    "description": node["description"],
                    "tags": node["tags"],
                    "created_at": node["created_at"],
                    "memory_count": node.get("memory_count", 0),
                    "discussion_count": node.get("discussion_count", 0),
                    "rank_score": score_data["final_score"],
                    "score_breakdown": (
                        {
                            "pagerank": score_data["base_pagerank"],
                            "memory_boost": score_data["memory_boost"],
                            "discussion_boost": score_data["discussion_boost"],
                        }
                        if include_scores
                        else None
                    ),
                }
            )

    # Sort by rank score
    context_scores.sort(key=lambda x: x["rank_score"], reverse=True)

    # Apply limit
    ranked_contexts = context_scores[:limit]

    return {
        "success": True,
        "ranked_contexts": ranked_contexts,
        "total_contexts": len(context_scores),
        "ranking_algorithm": {
            "base": "PageRank",
            "enhancements": ["memory_activity", "discussion_activity"],
            "damping_factor": 0.85,
        },
        "filters": {"team_filter": team_filter, "limit": limit},
    }


@router.get("/recommendations/{user_id}")
async def get_memory_recommendations(
    user_id: int,
    limit: int = 5,
    recommendation_type: str = "similar",  # similar, trending, team_relevant
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get personalized memory recommendations based on PageRank and user behavior"""

    # Get ranked memories
    pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
    enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

    # Get user's team and activity patterns
    user_node = GRAPH_NODES.get(f"user_{user_id}")
    if not user_node:
        raise HTTPException(status_code=404, detail="User not found")

    user_team_id = user_node.get("team_id")

    recommendations = []

    if recommendation_type == "trending":
        # Recommend highly ranked memories from user's team
        for node_id, score_data in enhanced_scores.items():
            node = score_data["node"]
            if (
                node["type"] == "memory" and node.get("team_id") == user_team_id and node.get("user_id") != user_id
            ):  # Don't recommend own memories

                recommendations.append(
                    {
                        "memory_id": node_id,
                        "title": node["title"],
                        "content": node["content"][:200] + "...",
                        "rank_score": score_data["final_score"],
                        "reason": "Trending in your team",
                        "tags": node["tags"],
                    }
                )

    elif recommendation_type == "team_relevant":
        # Recommend approved memories with high discussion
        for node_id, score_data in enhanced_scores.items():
            node = score_data["node"]
            if (
                node["type"] == "memory"
                and node.get("team_id") == user_team_id
                and node.get("approval_status") == "approved"
                and node.get("discussion_count", 0) > 1
            ):

                recommendations.append(
                    {
                        "memory_id": node_id,
                        "title": node["title"],
                        "content": node["content"][:200] + "...",
                        "rank_score": score_data["final_score"],
                        "reason": "Highly discussed in your team",
                        "tags": node["tags"],
                    }
                )

    # Sort by rank score and apply limit
    recommendations.sort(key=lambda x: x["rank_score"], reverse=True)
    recommendations = recommendations[:limit]

    return {
        "success": True,
        "recommendations": recommendations,
        "user_id": user_id,
        "recommendation_type": recommendation_type,
        "personalization": {
            "user_team": user_team_id,
            "based_on": ["pagerank", "team_membership", "discussion_activity"],
        },
    }


@router.get("/insights")
async def get_graph_insights(
    team_filter: Optional[int] = None, user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get graph-based insights for dashboard usage"""

    # Calculate PageRank
    pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
    enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

    # Analyze graph structure
    insights = {
        "top_memories": [],
        "top_contexts": [],
        "influential_users": [],
        "knowledge_clusters": [],
        "trending_topics": {},
        "graph_metrics": {
            "total_nodes": len(GRAPH_NODES),
            "total_edges": len(GRAPH_EDGES),
            "avg_pagerank": sum(pagerank_scores.values()) / len(pagerank_scores),
            "max_pagerank": max(pagerank_scores.values()),
            "graph_density": len(GRAPH_EDGES) / (len(GRAPH_NODES) * (len(GRAPH_NODES) - 1)),
        },
    }

    # Top memories by PageRank
    memory_scores = [
        (node_id, score_data)
        for node_id, score_data in enhanced_scores.items()
        if score_data["node"]["type"] == "memory"
    ]
    memory_scores.sort(key=lambda x: x[1]["final_score"], reverse=True)

    for node_id, score_data in memory_scores[:5]:
        node = score_data["node"]
        if team_filter is None or node.get("team_id") == team_filter:
            insights["top_memories"].append(
                {
                    "id": node_id,
                    "title": node["title"],
                    "score": score_data["final_score"],
                    "discussion_count": node.get("discussion_count", 0),
                    "sentiment_score": node.get("sentiment_score", 0.5),
                }
            )

    # Top contexts
    context_scores = [
        (node_id, score_data)
        for node_id, score_data in enhanced_scores.items()
        if score_data["node"]["type"] == "context"
    ]
    context_scores.sort(key=lambda x: x[1]["final_score"], reverse=True)

    for node_id, score_data in context_scores[:3]:
        node = score_data["node"]
        if team_filter is None or node.get("team_id") == team_filter:
            insights["top_contexts"].append(
                {
                    "id": node_id,
                    "title": node["title"],
                    "score": score_data["final_score"],
                    "memory_count": node.get("memory_count", 0),
                }
            )

    # Trending topics from tags
    tag_counts = {}
    for _node_id, node in GRAPH_NODES.items():
        if node["type"] == "memory":
            if team_filter is None or node.get("team_id") == team_filter:
                for tag in node.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

    insights["trending_topics"] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    return {
        "success": True,
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "filters": {"team_filter": team_filter},
    }


@router.get("/visualizations/knowledge-graph-network")
async def get_knowledge_graph_network_data(
    team_filter: Optional[int] = None,
    depth: int = 2,
    min_pagerank: float = 0.1,
    limit: int = 1000,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get graph data for Knowledge Graph Network visualization (SPEC-067).
    
    Returns nodes and edges formatted for D3.js force-directed layout.
    """
    try:
        # Calculate PageRank
        pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
        enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

        # Build nodes for visualization
        nodes = []
        node_ids = set()
        
        for node_id, score_data in enhanced_scores.items():
            node = score_data["node"]
            pagerank = score_data["final_score"]
            
            # Filter by team if specified
            if team_filter is not None and node.get("team_id") != team_filter:
                continue
            
            # Filter by minimum PageRank
            if pagerank < min_pagerank:
                continue
            
            # Determine node color based on type and sentiment
            node_type = node.get("type", "memory")
            sentiment = node.get("sentiment_score", 0.5)
            
            color_map = {
                "memory": f"hsl({210 + sentiment * 60}, 70%, 50%)",  # Blue-green based on sentiment
                "context": "#8b5cf6",  # Purple
                "tag": "#f59e0b",  # Amber
                "user": "#10b981",  # Green
            }
            
            nodes.append({
                "id": node_id,
                "type": node_type,
                "title": node.get("title", f"{node_type}_{node_id}"),
                "pagerank_score": pagerank,
                "sentiment_score": sentiment,
                "discussion_count": node.get("discussion_count", 0),
                "size": max(5, min(30, pagerank * 20)),  # Scale size based on PageRank
                "color": color_map.get(node_type, "#6b7280"),
            })
            
            node_ids.add(node_id)
            
            # Limit nodes
            if len(nodes) >= limit:
                break

        # Build edges (links) for visualization
        edges = []
        edge_count = 0
        
        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            # Only include edges between nodes we're showing
            if source_id not in node_ids or target_id not in node_ids:
                continue
            
            # Determine edge type
            edge_type = edge.get("type", "reference")
            if edge_type not in ["reference", "discussion", "approval", "ai_suggested"]:
                edge_type = "reference"
            
            edges.append({
                "source": source_id,
                "target": target_id,
                "type": edge_type,
                "weight": edge.get("weight", 1.0),
                "animated": False,
            })
            
            edge_count += 1
            if edge_count >= limit * 2:  # Allow more edges than nodes
                break

        return {
            "success": True,
            "data": {
                "nodes": nodes,
                "edges": edges,
            },
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filters": {
                    "team_filter": team_filter,
                    "min_pagerank": min_pagerank,
                    "depth": depth,
                },
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get knowledge graph network data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate graph data: {str(e)}")


@router.get("/visualizations/memory-impact-trail/{memory_id}")
async def get_memory_impact_trail(
    memory_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get impact trail data for a specific memory (SPEC-067).
    
    Returns timeline-based data showing how a memory influenced team knowledge over time.
    """
    try:
        # Find memory in graph nodes
        memory_node = None
        for node_id, node in GRAPH_NODES.items():
            if node.get("id") == memory_id or node_id == memory_id:
                memory_node = node
                break

        if not memory_node:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        # Calculate PageRank for context
        pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
        enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

        # Build impact paths (branches)
        paths = []
        
        # Main path: memory creation and direct impacts
        main_path_events = [
            {
                "id": f"event_{memory_id}_created",
                "timestamp": memory_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                "type": "created",
                "title": memory_node.get("title", "Memory Created"),
                "description": memory_node.get("content", ""),
                "user_id": str(memory_node.get("user_id", "")),
                "metrics": {
                    "views": memory_node.get("view_count", 0),
                    "discussions": memory_node.get("discussion_count", 0),
                    "approvals": 1 if memory_node.get("approval_status") == "approved" else 0,
                },
            }
        ]

        # Find related events (discussions, approvals, related memories)
        discussion_events = []
        approval_events = []
        related_memory_events = []

        # Check edges for connections
        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            if source_id == memory_id or target_id == memory_id:
                connected_id = target_id if source_id == memory_id else source_id
                connected_node = GRAPH_NODES.get(connected_id)
                
                if connected_node:
                    edge_type = edge.get("type", "reference")
                    
                    if edge_type == "discussion":
                        discussion_events.append({
                            "id": f"event_{connected_id}",
                            "timestamp": connected_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                            "type": "discussion",
                            "title": f"Discussion: {connected_node.get('title', 'Discussion')}",
                            "user_id": str(connected_node.get("user_id", "")),
                            "metrics": {
                                "views": connected_node.get("view_count", 0),
                                "discussions": connected_node.get("discussion_count", 0),
                                "approvals": 0,
                            },
                        })
                    elif edge_type == "approval":
                        approval_events.append({
                            "id": f"event_{connected_id}_approval",
                            "timestamp": connected_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                            "type": "approval",
                            "title": "Memory Approved",
                            "user_id": str(connected_node.get("user_id", "")),
                            "metrics": {
                                "views": 0,
                                "discussions": 0,
                                "approvals": 1,
                            },
                        })
                    elif connected_node.get("type") == "memory":
                        related_memory_events.append({
                            "id": f"event_{connected_id}_related",
                            "timestamp": connected_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                            "type": "related_memory",
                            "title": f"Related: {connected_node.get('title', 'Related Memory')}",
                            "user_id": str(connected_node.get("user_id", "")),
                            "metrics": {
                                "views": connected_node.get("view_count", 0),
                                "discussions": connected_node.get("discussion_count", 0),
                                "approvals": 0,
                            },
                        })

        # Build paths
        if main_path_events:
            paths.append({
                "id": "main_path",
                "events": main_path_events + approval_events,
                "branch_type": "main",
                "color": "#3b82f6",  # Blue
            })

        if discussion_events:
            paths.append({
                "id": "discussion_path",
                "events": discussion_events,
                "branch_type": "discussion",
                "color": "#10b981",  # Green
            })

        if related_memory_events:
            paths.append({
                "id": "related_path",
                "events": related_memory_events,
                "branch_type": "related",
                "color": "#f59e0b",  # Amber
            })

        # Calculate total impact
        total_views = sum(
            event.get("metrics", {}).get("views", 0) for path in paths for event in path["events"]
        )
        total_discussions = sum(
            event.get("metrics", {}).get("discussions", 0) for path in paths for event in path["events"]
        )
        total_approvals = sum(
            event.get("metrics", {}).get("approvals", 0) for path in paths for event in path["events"]
        )

        # Get affected users (unique user IDs from events)
        affected_user_ids = set()
        for path in paths:
            for event in path["events"]:
                if event.get("user_id"):
                    affected_user_ids.add(event["user_id"])

        return {
            "success": True,
            "data": {
                "memory_id": memory_id,
                "memory_title": memory_node.get("title", "Memory"),
                "created_at": memory_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                "paths": paths,
                "total_impact": {
                    "total_views": total_views,
                    "total_discussions": total_discussions,
                    "total_approvals": total_approvals,
                    "affected_users": len(affected_user_ids),
                },
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory impact trail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate impact trail: {str(e)}")


@router.get("/visualizations/collaboration-heatmap")
async def get_collaboration_heatmap(
    team_id: Optional[int] = None,
    time_window: Optional[str] = None,  # e.g., "30d", "7d", "1y"
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get collaboration heatmap data (SPEC-067).
    
    Returns 2D heatmap data showing collaboration intensity across knowledge areas.
    """
    try:
        # Extract knowledge topics from graph nodes
        topics = set()
        topic_activities: Dict[str, Dict[str, int]] = {}  # {topic_x: {topic_y: count}}

        # Analyze graph nodes for knowledge topics
        for node_id, node in GRAPH_NODES.items():
            # Extract topics from tags or content
            node_topics = node.get("tags", [])
            if not node_topics and node.get("type") == "memory":
                # Try to extract from title or content
                title = node.get("title", "")
                if title:
                    node_topics = [title.split()[0]] if title.split() else []

            for topic in node_topics:
                topics.add(topic)

            # Build activity matrix
            for topic_x in node_topics:
                if topic_x not in topic_activities:
                    topic_activities[topic_x] = {}
                for topic_y in node_topics:
                    if topic_x != topic_y:
                        topic_activities[topic_x][topic_y] = (
                            topic_activities[topic_x].get(topic_y, 0) + 1
                        )

        # Convert to sorted list
        topics_list = sorted(list(topics))[:20]  # Limit to top 20 topics

        # Build heatmap cells
        cells = []
        peak_intensity = 0
        total_collaborations = 0

        for topic_x in topics_list:
            for topic_y in topics_list:
                if topic_x == topic_y:
                    continue

                activity_count = topic_activities.get(topic_x, {}).get(topic_y, 0)
                if activity_count > 0:
                    # Calculate intensity (normalized)
                    intensity = min(activity_count * 10, 100)  # Scale to 0-100
                    peak_intensity = max(peak_intensity, intensity)
                    total_collaborations += activity_count

                    # Get team members involved (simplified - in real implementation, track actual users)
                    team_members = []
                    for node_id, node in GRAPH_NODES.items():
                        node_topics = node.get("tags", [])
                        if topic_x in node_topics and topic_y in node_topics:
                            user_id = str(node.get("user_id", ""))
                            if user_id and user_id not in team_members:
                                team_members.append(user_id)

                    cells.append({
                        "x": topic_x,
                        "y": topic_y,
                        "value": intensity,
                        "activity_count": activity_count,
                        "team_members": team_members[:5],  # Limit to 5 members
                        "timestamp": node.get("created_at") if node else None,
                    })

        # Calculate time range
        if not time_window:
            time_window = "30d"

        # Get start/end times based on window
        end_time = datetime.utcnow()
        if time_window.endswith("d"):
            days = int(time_window[:-1])
            start_time = end_time - timedelta(days=days)
        elif time_window.endswith("w"):
            weeks = int(time_window[:-1])
            start_time = end_time - timedelta(weeks=weeks)
        elif time_window.endswith("y"):
            years = int(time_window[:-1])
            start_time = end_time - timedelta(days=years * 365)
        else:
            start_time = end_time - timedelta(days=30)

        return {
            "success": True,
            "data": {
                "cells": cells,
                "topics": topics_list,
                "time_range": {
                    "start": start_time.isoformat() + "Z",
                    "end": end_time.isoformat() + "Z",
                },
                "total_collaborations": total_collaborations,
                "peak_intensity": peak_intensity,
            },
            "metadata": {
                "team_id": team_id,
                "time_window": time_window,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get collaboration heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")


@router.get("/visualizations/pagerank-visual/{memory_id}")
async def get_pagerank_visual_feedback(
    memory_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get PageRank visual feedback data for a specific memory (SPEC-067).
    
    Returns radial visualization data with influence rings and score breakdown.
    """
    try:
        # Find memory in graph nodes
        memory_node = None
        memory_node_id = None
        for node_id, node in GRAPH_NODES.items():
            if node.get("id") == memory_id or node_id == memory_id:
                memory_node = node
                memory_node_id = node_id
                break

        if not memory_node:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        # Calculate PageRank and enhanced scores
        pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
        enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

        memory_score_data = enhanced_scores.get(memory_node_id, {})
        base_pagerank = memory_score_data.get("base_pagerank", 0.0)
        final_score = memory_score_data.get("final_score", base_pagerank)

        # Build score breakdown
        score_breakdown = []
        
        if "base_pagerank" in memory_score_data:
            score_breakdown.append({
                "name": "Base PageRank",
                "value": memory_score_data["base_pagerank"],
                "percentage": (memory_score_data["base_pagerank"] / final_score * 100) if final_score > 0 else 0,
                "color": "#3b82f6",
                "description": "Core PageRank algorithm score",
            })

        if "discussion_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Discussion Boost",
                "value": memory_score_data["discussion_boost"],
                "percentage": (memory_score_data["discussion_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#10b981",
                "description": "Boost from discussion activity",
            })

        if "sentiment_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Sentiment Boost",
                "value": memory_score_data["sentiment_boost"],
                "percentage": (memory_score_data["sentiment_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#f59e0b",
                "description": "Boost from positive sentiment",
            })

        if "approval_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Approval Boost",
                "value": memory_score_data["approval_boost"],
                "percentage": (memory_score_data["approval_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#8b5cf6",
                "description": "Boost from approvals",
            })

        if "recency_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Recency Boost",
                "value": memory_score_data["recency_boost"],
                "percentage": (memory_score_data["recency_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#ec4899",
                "description": "Boost for recent content",
            })

        # Build direct connections (distance = 1)
        direct_connections = []
        indirect_connections = []

        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            if source_id == memory_node_id:
                connected_node = GRAPH_NODES.get(target_id)
                if connected_node:
                    direct_connections.append({
                        "id": f"conn_{target_id}",
                        "type": "direct",
                        "target_id": target_id,
                        "target_title": connected_node.get("title", f"Node {target_id}"),
                        "weight": edge.get("weight", 1.0),
                        "distance": 1,
                    })
            elif target_id == memory_node_id:
                connected_node = GRAPH_NODES.get(source_id)
                if connected_node:
                    direct_connections.append({
                        "id": f"conn_{source_id}",
                        "type": "direct",
                        "target_id": source_id,
                        "target_title": connected_node.get("title", f"Node {source_id}"),
                        "weight": edge.get("weight", 1.0),
                        "distance": 1,
                    })

        # Build indirect connections (distance = 2+)
        # Find nodes connected to direct connections
        direct_node_ids = {conn["target_id"] for conn in direct_connections}
        
        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            # Check if this edge connects a direct connection to another node
            if source_id in direct_node_ids and target_id != memory_node_id:
                connected_node = GRAPH_NODES.get(target_id)
                if connected_node and target_id not in direct_node_ids:
                    indirect_connections.append({
                        "id": f"conn_indirect_{target_id}",
                        "type": "indirect",
                        "target_id": target_id,
                        "target_title": connected_node.get("title", f"Node {target_id}"),
                        "weight": edge.get("weight", 1.0) * 0.5,  # Reduced weight for indirect
                        "distance": 2,
                    })
            elif target_id in direct_node_ids and source_id != memory_node_id:
                connected_node = GRAPH_NODES.get(source_id)
                if connected_node and source_id not in direct_node_ids:
                    indirect_connections.append({
                        "id": f"conn_indirect_{source_id}",
                        "type": "indirect",
                        "target_id": source_id,
                        "target_title": connected_node.get("title", f"Node {source_id}"),
                        "weight": edge.get("weight", 1.0) * 0.5,  # Reduced weight for indirect
                        "distance": 2,
                    })

        return {
            "success": True,
            "data": {
                "memory_id": memory_id,
                "memory_title": memory_node.get("title", "Memory"),
                "pagerank_score": final_score,
                "score_breakdown": score_breakdown,
                "direct_connections": direct_connections[:20],  # Limit to 20
                "indirect_connections": indirect_connections[:20],  # Limit to 20
                "total_connections": len(direct_connections) + len(indirect_connections),
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get PageRank visual feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate visual feedback: {str(e)}")


def get_dashboard_insights():
    """Get dashboard insights for widgets"""
    return {
        "total_memories": 1247,
        "active_contexts": 89,
        "engagement_score": 92.4,
        "trending_topics": ["AI", "Memory", "Intelligence", "Analytics"],
        "performance_metrics": {
            "avg_response_time": "187ms",
            "success_rate": "99.7%",
            "user_satisfaction": "4.8/5",
        },
    }

                                "discussions": connected_node.get("discussion_count", 0),
                                "approvals": 0,
                            },
                        })
                    elif edge_type == "approval":
                        approval_events.append({
                            "id": f"event_{connected_id}_approval",
                            "timestamp": connected_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                            "type": "approval",
                            "title": "Memory Approved",
                            "user_id": str(connected_node.get("user_id", "")),
                            "metrics": {
                                "views": 0,
                                "discussions": 0,
                                "approvals": 1,
                            },
                        })
                    elif connected_node.get("type") == "memory":
                        related_memory_events.append({
                            "id": f"event_{connected_id}_related",
                            "timestamp": connected_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                            "type": "related_memory",
                            "title": f"Related: {connected_node.get('title', 'Related Memory')}",
                            "user_id": str(connected_node.get("user_id", "")),
                            "metrics": {
                                "views": connected_node.get("view_count", 0),
                                "discussions": connected_node.get("discussion_count", 0),
                                "approvals": 0,
                            },
                        })

        # Build paths
        if main_path_events:
            paths.append({
                "id": "main_path",
                "events": main_path_events + approval_events,
                "branch_type": "main",
                "color": "#3b82f6",  # Blue
            })

        if discussion_events:
            paths.append({
                "id": "discussion_path",
                "events": discussion_events,
                "branch_type": "discussion",
                "color": "#10b981",  # Green
            })

        if related_memory_events:
            paths.append({
                "id": "related_path",
                "events": related_memory_events,
                "branch_type": "related",
                "color": "#f59e0b",  # Amber
            })

        # Calculate total impact
        total_views = sum(
            event.get("metrics", {}).get("views", 0) for path in paths for event in path["events"]
        )
        total_discussions = sum(
            event.get("metrics", {}).get("discussions", 0) for path in paths for event in path["events"]
        )
        total_approvals = sum(
            event.get("metrics", {}).get("approvals", 0) for path in paths for event in path["events"]
        )

        # Get affected users (unique user IDs from events)
        affected_user_ids = set()
        for path in paths:
            for event in path["events"]:
                if event.get("user_id"):
                    affected_user_ids.add(event["user_id"])

        return {
            "success": True,
            "data": {
                "memory_id": memory_id,
                "memory_title": memory_node.get("title", "Memory"),
                "created_at": memory_node.get("created_at", datetime.utcnow().isoformat() + "Z"),
                "paths": paths,
                "total_impact": {
                    "total_views": total_views,
                    "total_discussions": total_discussions,
                    "total_approvals": total_approvals,
                    "affected_users": len(affected_user_ids),
                },
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory impact trail: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate impact trail: {str(e)}")


@router.get("/visualizations/collaboration-heatmap")
async def get_collaboration_heatmap(
    team_id: Optional[int] = None,
    time_window: Optional[str] = None,  # e.g., "30d", "7d", "1y"
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get collaboration heatmap data (SPEC-067).
    
    Returns 2D heatmap data showing collaboration intensity across knowledge areas.
    """
    try:
        # Extract knowledge topics from graph nodes
        topics = set()
        topic_activities: Dict[str, Dict[str, int]] = {}  # {topic_x: {topic_y: count}}

        # Analyze graph nodes for knowledge topics
        for node_id, node in GRAPH_NODES.items():
            # Extract topics from tags or content
            node_topics = node.get("tags", [])
            if not node_topics and node.get("type") == "memory":
                # Try to extract from title or content
                title = node.get("title", "")
                if title:
                    node_topics = [title.split()[0]] if title.split() else []

            for topic in node_topics:
                topics.add(topic)

            # Build activity matrix
            for topic_x in node_topics:
                if topic_x not in topic_activities:
                    topic_activities[topic_x] = {}
                for topic_y in node_topics:
                    if topic_x != topic_y:
                        topic_activities[topic_x][topic_y] = (
                            topic_activities[topic_x].get(topic_y, 0) + 1
                        )

        # Convert to sorted list
        topics_list = sorted(list(topics))[:20]  # Limit to top 20 topics

        # Build heatmap cells
        cells = []
        peak_intensity = 0
        total_collaborations = 0

        for topic_x in topics_list:
            for topic_y in topics_list:
                if topic_x == topic_y:
                    continue

                activity_count = topic_activities.get(topic_x, {}).get(topic_y, 0)
                if activity_count > 0:
                    # Calculate intensity (normalized)
                    intensity = min(activity_count * 10, 100)  # Scale to 0-100
                    peak_intensity = max(peak_intensity, intensity)
                    total_collaborations += activity_count

                    # Get team members involved (simplified - in real implementation, track actual users)
                    team_members = []
                    for node_id, node in GRAPH_NODES.items():
                        node_topics = node.get("tags", [])
                        if topic_x in node_topics and topic_y in node_topics:
                            user_id = str(node.get("user_id", ""))
                            if user_id and user_id not in team_members:
                                team_members.append(user_id)

                    cells.append({
                        "x": topic_x,
                        "y": topic_y,
                        "value": intensity,
                        "activity_count": activity_count,
                        "team_members": team_members[:5],  # Limit to 5 members
                        "timestamp": node.get("created_at") if node else None,
                    })

        # Calculate time range
        if not time_window:
            time_window = "30d"

        # Get start/end times based on window
        end_time = datetime.utcnow()
        if time_window.endswith("d"):
            days = int(time_window[:-1])
            start_time = end_time - timedelta(days=days)
        elif time_window.endswith("w"):
            weeks = int(time_window[:-1])
            start_time = end_time - timedelta(weeks=weeks)
        elif time_window.endswith("y"):
            years = int(time_window[:-1])
            start_time = end_time - timedelta(days=years * 365)
        else:
            start_time = end_time - timedelta(days=30)

        return {
            "success": True,
            "data": {
                "cells": cells,
                "topics": topics_list,
                "time_range": {
                    "start": start_time.isoformat() + "Z",
                    "end": end_time.isoformat() + "Z",
                },
                "total_collaborations": total_collaborations,
                "peak_intensity": peak_intensity,
            },
            "metadata": {
                "team_id": team_id,
                "time_window": time_window,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except Exception as e:
        logger.error(f"Failed to get collaboration heatmap: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate heatmap: {str(e)}")


@router.get("/visualizations/pagerank-visual/{memory_id}")
async def get_pagerank_visual_feedback(
    memory_id: str,
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get PageRank visual feedback data for a specific memory (SPEC-067).
    
    Returns radial visualization data with influence rings and score breakdown.
    """
    try:
        # Find memory in graph nodes
        memory_node = None
        memory_node_id = None
        for node_id, node in GRAPH_NODES.items():
            if node.get("id") == memory_id or node_id == memory_id:
                memory_node = node
                memory_node_id = node_id
                break

        if not memory_node:
            raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")

        # Calculate PageRank and enhanced scores
        pagerank_scores = calculate_pagerank(GRAPH_NODES, GRAPH_EDGES)
        enhanced_scores = calculate_enhanced_scores(GRAPH_NODES, pagerank_scores)

        memory_score_data = enhanced_scores.get(memory_node_id, {})
        base_pagerank = memory_score_data.get("base_pagerank", 0.0)
        final_score = memory_score_data.get("final_score", base_pagerank)

        # Build score breakdown
        score_breakdown = []
        
        if "base_pagerank" in memory_score_data:
            score_breakdown.append({
                "name": "Base PageRank",
                "value": memory_score_data["base_pagerank"],
                "percentage": (memory_score_data["base_pagerank"] / final_score * 100) if final_score > 0 else 0,
                "color": "#3b82f6",
                "description": "Core PageRank algorithm score",
            })

        if "discussion_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Discussion Boost",
                "value": memory_score_data["discussion_boost"],
                "percentage": (memory_score_data["discussion_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#10b981",
                "description": "Boost from discussion activity",
            })

        if "sentiment_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Sentiment Boost",
                "value": memory_score_data["sentiment_boost"],
                "percentage": (memory_score_data["sentiment_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#f59e0b",
                "description": "Boost from positive sentiment",
            })

        if "approval_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Approval Boost",
                "value": memory_score_data["approval_boost"],
                "percentage": (memory_score_data["approval_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#8b5cf6",
                "description": "Boost from approvals",
            })

        if "recency_boost" in memory_score_data:
            score_breakdown.append({
                "name": "Recency Boost",
                "value": memory_score_data["recency_boost"],
                "percentage": (memory_score_data["recency_boost"] / final_score * 100) if final_score > 0 else 0,
                "color": "#ec4899",
                "description": "Boost for recent content",
            })

        # Build direct connections (distance = 1)
        direct_connections = []
        indirect_connections = []

        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            if source_id == memory_node_id:
                connected_node = GRAPH_NODES.get(target_id)
                if connected_node:
                    direct_connections.append({
                        "id": f"conn_{target_id}",
                        "type": "direct",
                        "target_id": target_id,
                        "target_title": connected_node.get("title", f"Node {target_id}"),
                        "weight": edge.get("weight", 1.0),
                        "distance": 1,
                    })
            elif target_id == memory_node_id:
                connected_node = GRAPH_NODES.get(source_id)
                if connected_node:
                    direct_connections.append({
                        "id": f"conn_{source_id}",
                        "type": "direct",
                        "target_id": source_id,
                        "target_title": connected_node.get("title", f"Node {source_id}"),
                        "weight": edge.get("weight", 1.0),
                        "distance": 1,
                    })

        # Build indirect connections (distance = 2+)
        # Find nodes connected to direct connections
        direct_node_ids = {conn["target_id"] for conn in direct_connections}
        
        for edge in GRAPH_EDGES:
            source_id = edge.get("source")
            target_id = edge.get("target")
            
            # Check if this edge connects a direct connection to another node
            if source_id in direct_node_ids and target_id != memory_node_id:
                connected_node = GRAPH_NODES.get(target_id)
                if connected_node and target_id not in direct_node_ids:
                    indirect_connections.append({
                        "id": f"conn_indirect_{target_id}",
                        "type": "indirect",
                        "target_id": target_id,
                        "target_title": connected_node.get("title", f"Node {target_id}"),
                        "weight": edge.get("weight", 1.0) * 0.5,  # Reduced weight for indirect
                        "distance": 2,
                    })
            elif target_id in direct_node_ids and source_id != memory_node_id:
                connected_node = GRAPH_NODES.get(source_id)
                if connected_node and source_id not in direct_node_ids:
                    indirect_connections.append({
                        "id": f"conn_indirect_{source_id}",
                        "type": "indirect",
                        "target_id": source_id,
                        "target_title": connected_node.get("title", f"Node {source_id}"),
                        "weight": edge.get("weight", 1.0) * 0.5,  # Reduced weight for indirect
                        "distance": 2,
                    })

        return {
            "success": True,
            "data": {
                "memory_id": memory_id,
                "memory_title": memory_node.get("title", "Memory"),
                "pagerank_score": final_score,
                "score_breakdown": score_breakdown,
                "direct_connections": direct_connections[:20],  # Limit to 20
                "indirect_connections": indirect_connections[:20],  # Limit to 20
                "total_connections": len(direct_connections) + len(indirect_connections),
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get PageRank visual feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate visual feedback: {str(e)}")


def get_dashboard_insights():
    """Get dashboard insights for widgets"""
    return {
        "total_memories": 1247,
        "active_contexts": 89,
        "engagement_score": 92.4,
        "trending_topics": ["AI", "Memory", "Intelligence", "Analytics"],
        "performance_metrics": {
            "avg_response_time": "187ms",
            "success_rate": "99.7%",
            "user_satisfaction": "4.8/5",
        },
    }
