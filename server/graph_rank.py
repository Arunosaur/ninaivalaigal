"""
Graph Ranking System - PageRank for Memory Intelligence
Ranks memories and contexts based on connections, discussions, and approvals
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from auth_utils import get_current_user
import math

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
        "sentiment_score": 0.7
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
        "sentiment_score": 0.9
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
        "sentiment_score": 0.8
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
        "discussion_count": 5
    },
    # User nodes
    "user_123": {
        "id": "user_123",
        "type": "user",
        "name": "Team Admin",
        "role": "team_admin",
        "team_id": 1,
        "activity_score": 0.9
    },
    "user_456": {
        "id": "user_456", 
        "type": "user",
        "name": "Project Owner",
        "role": "team_admin",
        "team_id": 1,
        "activity_score": 0.7
    }
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
    {"source": "memory_2", "target": "memory_1", "type": "discussed_with", "weight": 0.6},
    {"source": "memory_3", "target": "memory_2", "type": "discussed_with", "weight": 0.7},
    
    # Approval relationships
    {"source": "user_456", "target": "memory_2", "type": "approved", "weight": 0.8},
    {"source": "user_123", "target": "memory_3", "type": "approved", "weight": 0.8}
]

def calculate_pagerank(nodes: Dict, edges: List[Dict], damping_factor: float = 0.85, max_iterations: int = 100, tolerance: float = 1e-6) -> Dict[str, float]:
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
    for iteration in range(max_iterations):
        new_pagerank = {}
        
        for node_id in node_ids:
            # Base probability (random jump)
            rank = (1 - damping_factor) / num_nodes
            
            # Add rank from incoming links
            for link in incoming_links[node_id]:
                source_id = link["source"]
                weight = link["weight"]
                
                # Calculate outgoing weight sum for source
                outgoing_weight_sum = sum(l["weight"] for l in outgoing_links[source_id])
                
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
                "node": node
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
                "node": node
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
                "node": node
            }
    
    return enhanced_scores

@router.get("/memories")
async def get_ranked_memories(
    limit: int = 10,
    team_filter: Optional[int] = None,
    include_scores: bool = False,
    user: Dict[str, Any] = Depends(get_current_user)
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
            
            memory_scores.append({
                "memory_id": node_id,
                "title": node["title"],
                "content": node["content"],
                "tags": node["tags"],
                "created_at": node["created_at"],
                "approval_status": node.get("approval_status"),
                "discussion_count": node.get("discussion_count", 0),
                "sentiment_score": node.get("sentiment_score", 0.5),
                "rank_score": score_data["final_score"],
                "score_breakdown": {
                    "pagerank": score_data["base_pagerank"],
                    "discussion_boost": score_data["discussion_boost"],
                    "sentiment_boost": score_data["sentiment_boost"],
                    "approval_boost": score_data["approval_boost"],
                    "recency_boost": score_data["recency_boost"]
                } if include_scores else None
            })
    
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
            "enhancements": ["discussion_activity", "sentiment_analysis", "approval_status", "recency"],
            "damping_factor": 0.85
        },
        "filters": {
            "team_filter": team_filter,
            "limit": limit
        }
    }

@router.get("/contexts")
async def get_ranked_contexts(
    limit: int = 10,
    team_filter: Optional[int] = None,
    include_scores: bool = False,
    user: Dict[str, Any] = Depends(get_current_user)
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
            
            context_scores.append({
                "context_id": node_id,
                "title": node["title"],
                "description": node["description"],
                "tags": node["tags"],
                "created_at": node["created_at"],
                "memory_count": node.get("memory_count", 0),
                "discussion_count": node.get("discussion_count", 0),
                "rank_score": score_data["final_score"],
                "score_breakdown": {
                    "pagerank": score_data["base_pagerank"],
                    "memory_boost": score_data["memory_boost"],
                    "discussion_boost": score_data["discussion_boost"]
                } if include_scores else None
            })
    
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
            "damping_factor": 0.85
        },
        "filters": {
            "team_filter": team_filter,
            "limit": limit
        }
    }

@router.get("/recommendations/{user_id}")
async def get_memory_recommendations(
    user_id: int,
    limit: int = 5,
    recommendation_type: str = "similar",  # similar, trending, team_relevant
    user: Dict[str, Any] = Depends(get_current_user)
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
            if (node["type"] == "memory" and 
                node.get("team_id") == user_team_id and
                node.get("user_id") != user_id):  # Don't recommend own memories
                
                recommendations.append({
                    "memory_id": node_id,
                    "title": node["title"],
                    "content": node["content"][:200] + "...",
                    "rank_score": score_data["final_score"],
                    "reason": "Trending in your team",
                    "tags": node["tags"]
                })
    
    elif recommendation_type == "team_relevant":
        # Recommend approved memories with high discussion
        for node_id, score_data in enhanced_scores.items():
            node = score_data["node"]
            if (node["type"] == "memory" and 
                node.get("team_id") == user_team_id and
                node.get("approval_status") == "approved" and
                node.get("discussion_count", 0) > 1):
                
                recommendations.append({
                    "memory_id": node_id,
                    "title": node["title"],
                    "content": node["content"][:200] + "...",
                    "rank_score": score_data["final_score"],
                    "reason": "Highly discussed in your team",
                    "tags": node["tags"]
                })
    
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
            "based_on": ["pagerank", "team_membership", "discussion_activity"]
        }
    }

@router.get("/insights")
async def get_graph_insights(
    team_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
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
            "graph_density": len(GRAPH_EDGES) / (len(GRAPH_NODES) * (len(GRAPH_NODES) - 1))
        }
    }
    
    # Top memories by PageRank
    memory_scores = [(node_id, score_data) for node_id, score_data in enhanced_scores.items() 
                    if score_data["node"]["type"] == "memory"]
    memory_scores.sort(key=lambda x: x[1]["final_score"], reverse=True)
    
    for node_id, score_data in memory_scores[:5]:
        node = score_data["node"]
        if team_filter is None or node.get("team_id") == team_filter:
            insights["top_memories"].append({
                "id": node_id,
                "title": node["title"],
                "score": score_data["final_score"],
                "discussion_count": node.get("discussion_count", 0),
                "sentiment_score": node.get("sentiment_score", 0.5)
            })
    
    # Top contexts
    context_scores = [(node_id, score_data) for node_id, score_data in enhanced_scores.items() 
                     if score_data["node"]["type"] == "context"]
    context_scores.sort(key=lambda x: x[1]["final_score"], reverse=True)
    
    for node_id, score_data in context_scores[:3]:
        node = score_data["node"]
        if team_filter is None or node.get("team_id") == team_filter:
            insights["top_contexts"].append({
                "id": node_id,
                "title": node["title"],
                "score": score_data["final_score"],
                "memory_count": node.get("memory_count", 0)
            })
    
    # Trending topics from tags
    tag_counts = {}
    for node_id, node in GRAPH_NODES.items():
        if node["type"] == "memory":
            if team_filter is None or node.get("team_id") == team_filter:
                for tag in node.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    insights["trending_topics"] = dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    return {
        "success": True,
        "insights": insights,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "filters": {
            "team_filter": team_filter
        }
    }
