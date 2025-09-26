"""
Tag Suggester System - GPT-Powered Auto-Tagging
Uses AI to suggest relevant tags for memories based on content analysis
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime
from auth_utils import get_current_user
import re
import json

router = APIRouter(prefix="/tag-suggester", tags=["ai-intelligence"])

# Mock GPT responses - in real implementation, integrate with OpenAI API
MOCK_GPT_RESPONSES = {
    "Remember to implement async authentication for better performance": {
        "suggested_tags": ["authentication", "performance", "async"],
        "confidence_scores": [0.95, 0.88, 0.82],
        "reasoning": "Content discusses authentication implementation with focus on performance optimization using async patterns"
    },
    "Team decision: Use GET-based endpoints for MVP to bypass POST issues": {
        "suggested_tags": ["architecture", "mvp", "endpoints"],
        "confidence_scores": [0.92, 0.89, 0.85],
        "reasoning": "Content describes architectural decision for MVP development regarding API endpoint design"
    },
    "Code review: Auth system looks solid, ready for production": {
        "suggested_tags": ["code-review", "production", "authentication"],
        "confidence_scores": [0.98, 0.91, 0.87],
        "reasoning": "Content is a code review assessment focusing on authentication system production readiness"
    },
    "Database queries reduced by 40% through optimization": {
        "suggested_tags": ["performance", "database", "optimization"],
        "confidence_scores": [0.94, 0.92, 0.89],
        "reasoning": "Content reports performance improvements through database optimization techniques"
    },
    "Sprint planning meeting notes for Q1 goals": {
        "suggested_tags": ["planning", "sprint", "goals"],
        "confidence_scores": [0.96, 0.93, 0.88],
        "reasoning": "Content relates to agile sprint planning and quarterly goal setting"
    }
}

# Existing tag database for context and suggestions
EXISTING_TAGS_DB = {
    "technical": ["authentication", "performance", "database", "api", "security", "optimization", "async", "endpoints"],
    "process": ["code-review", "planning", "sprint", "mvp", "production", "testing", "deployment"],
    "team": ["team-decision", "collaboration", "meeting", "discussion", "feedback"],
    "project": ["architecture", "design", "implementation", "goals", "roadmap", "requirements"],
    "quality": ["bug-fix", "improvement", "refactoring", "documentation", "standards"]
}

def extract_keywords(text: str) -> List[str]:
    """Extract potential keywords from text using simple NLP techniques"""
    # Convert to lowercase and remove special characters
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean_text.split()
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
    
    # Extract meaningful words (length > 2, not stop words)
    keywords = [word for word in words if len(word) > 2 and word not in stop_words]
    
    # Return unique keywords
    return list(set(keywords))

def mock_gpt_tag_suggestion(content: str, existing_tags: List[str] = None) -> Dict[str, Any]:
    """Mock GPT API call for tag suggestions"""
    
    # Check if we have a mock response for this content
    if content in MOCK_GPT_RESPONSES:
        return MOCK_GPT_RESPONSES[content]
    
    # Generate suggestions based on keywords and existing tags
    keywords = extract_keywords(content)
    
    # Find matching tags from existing tag database
    suggested_tags = []
    confidence_scores = []
    
    # Check against existing tag categories
    for category, tags in EXISTING_TAGS_DB.items():
        for tag in tags:
            # Simple matching - check if tag appears in keywords or content
            if tag in keywords or tag in content.lower():
                if tag not in suggested_tags:
                    suggested_tags.append(tag)
                    # Higher confidence for exact matches
                    confidence = 0.9 if tag in keywords else 0.7
                    confidence_scores.append(confidence)
    
    # If we don't have enough suggestions, add some from keywords
    if len(suggested_tags) < 3:
        for keyword in keywords[:3]:
            if keyword not in suggested_tags and len(keyword) > 3:
                suggested_tags.append(keyword)
                confidence_scores.append(0.6)
    
    # Limit to top 3 suggestions
    if len(suggested_tags) > 3:
        # Sort by confidence and take top 3
        tag_confidence_pairs = list(zip(suggested_tags, confidence_scores))
        tag_confidence_pairs.sort(key=lambda x: x[1], reverse=True)
        suggested_tags = [pair[0] for pair in tag_confidence_pairs[:3]]
        confidence_scores = [pair[1] for pair in tag_confidence_pairs[:3]]
    
    return {
        "suggested_tags": suggested_tags[:3],
        "confidence_scores": confidence_scores[:3],
        "reasoning": f"Tags suggested based on content analysis and keyword extraction from: {', '.join(keywords[:5])}"
    }

@router.get("/suggest")
async def suggest_tags(
    content: str,
    existing_tags: Optional[str] = None,
    max_suggestions: int = 3,
    min_confidence: float = 0.5,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Suggest tags for memory content using AI analysis"""
    
    if not content or len(content.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Content must be at least 10 characters long for tag suggestion"
        )
    
    # Parse existing tags if provided
    existing_tag_list = []
    if existing_tags:
        existing_tag_list = [tag.strip() for tag in existing_tags.split(",") if tag.strip()]
    
    # Get AI suggestions (mock GPT call)
    try:
        gpt_response = mock_gpt_tag_suggestion(content, existing_tag_list)
        
        # Filter by confidence threshold
        filtered_suggestions = []
        for i, (tag, confidence) in enumerate(zip(gpt_response["suggested_tags"], gpt_response["confidence_scores"])):
            if confidence >= min_confidence:
                filtered_suggestions.append({
                    "tag": tag,
                    "confidence": confidence,
                    "rank": i + 1,
                    "already_exists": tag in existing_tag_list
                })
        
        # Limit to max suggestions
        filtered_suggestions = filtered_suggestions[:max_suggestions]
        
        # Get related tags from existing database
        related_tags = []
        for suggestion in filtered_suggestions:
            tag = suggestion["tag"]
            for category, tags in EXISTING_TAGS_DB.items():
                if tag in tags:
                    # Add other tags from same category as related
                    category_tags = [t for t in tags if t != tag and t not in existing_tag_list][:2]
                    related_tags.extend(category_tags)
        
        # Remove duplicates from related tags
        related_tags = list(set(related_tags))[:5]
        
        return {
            "success": True,
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "suggestions": filtered_suggestions,
            "related_tags": related_tags,
            "ai_analysis": {
                "reasoning": gpt_response["reasoning"],
                "keywords_extracted": extract_keywords(content)[:10],
                "confidence_threshold": min_confidence
            },
            "existing_tags": existing_tag_list,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Tag suggestion failed: {str(e)}",
            "fallback_suggestions": extract_keywords(content)[:3]
        }

@router.get("/batch-suggest")
async def batch_suggest_tags(
    memory_ids: str,  # Comma-separated memory IDs
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Suggest tags for multiple memories in batch"""
    
    # Parse memory IDs
    try:
        id_list = [int(id.strip()) for id in memory_ids.split(",") if id.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid memory ID format")
    
    if len(id_list) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 memories per batch request")
    
    # Mock memory database lookup
    mock_memories = {
        1: {
            "id": 1,
            "content": "Remember to implement async authentication for better performance",
            "existing_tags": ["development"]
        },
        2: {
            "id": 2,
            "content": "Team decision: Use GET-based endpoints for MVP to bypass POST issues",
            "existing_tags": ["team-decision"]
        },
        3: {
            "id": 3,
            "content": "Code review: Auth system looks solid, ready for production",
            "existing_tags": []
        }
    }
    
    batch_results = []
    
    for memory_id in id_list:
        memory = mock_memories.get(memory_id)
        if not memory:
            batch_results.append({
                "memory_id": memory_id,
                "success": False,
                "error": "Memory not found"
            })
            continue
        
        # Get suggestions for this memory
        try:
            gpt_response = mock_gpt_tag_suggestion(memory["content"], memory["existing_tags"])
            
            suggestions = []
            for i, (tag, confidence) in enumerate(zip(gpt_response["suggested_tags"], gpt_response["confidence_scores"])):
                suggestions.append({
                    "tag": tag,
                    "confidence": confidence,
                    "rank": i + 1,
                    "already_exists": tag in memory["existing_tags"]
                })
            
            batch_results.append({
                "memory_id": memory_id,
                "success": True,
                "content_preview": memory["content"][:50] + "...",
                "suggestions": suggestions,
                "existing_tags": memory["existing_tags"]
            })
            
        except Exception as e:
            batch_results.append({
                "memory_id": memory_id,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": True,
        "batch_results": batch_results,
        "total_processed": len(batch_results),
        "successful": len([r for r in batch_results if r["success"]]),
        "failed": len([r for r in batch_results if not r["success"]])
    }

@router.get("/tag-analytics")
async def get_tag_analytics(
    team_filter: Optional[int] = None,
    days_back: int = 30,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get analytics on tag usage and AI suggestion performance"""
    
    # Mock analytics data
    analytics = {
        "tag_usage_stats": {
            "most_used_tags": [
                {"tag": "authentication", "count": 15, "trend": "up"},
                {"tag": "performance", "count": 12, "trend": "stable"},
                {"tag": "team-decision", "count": 8, "trend": "up"},
                {"tag": "code-review", "count": 6, "trend": "down"},
                {"tag": "mvp", "count": 5, "trend": "up"}
            ],
            "tag_categories": {
                "technical": 45,
                "process": 28,
                "team": 18,
                "project": 15,
                "quality": 12
            },
            "total_unique_tags": 67,
            "avg_tags_per_memory": 2.3
        },
        "ai_suggestion_stats": {
            "suggestions_generated": 156,
            "suggestions_accepted": 89,
            "acceptance_rate": 0.57,
            "avg_confidence_score": 0.78,
            "top_suggested_tags": [
                {"tag": "performance", "suggested_count": 23, "accepted_count": 18},
                {"tag": "authentication", "suggested_count": 19, "accepted_count": 15},
                {"tag": "optimization", "suggested_count": 14, "accepted_count": 8}
            ]
        },
        "tag_quality_metrics": {
            "high_confidence_suggestions": 67,  # > 0.8 confidence
            "medium_confidence_suggestions": 54,  # 0.6-0.8 confidence
            "low_confidence_suggestions": 35,  # < 0.6 confidence
            "user_feedback_score": 4.2,  # out of 5
            "suggestion_relevance_score": 0.73
        },
        "trending_topics": {
            "emerging_tags": ["async", "optimization", "endpoints"],
            "declining_tags": ["legacy", "deprecated", "old-system"],
            "seasonal_patterns": {
                "planning": "high in Q1",
                "performance": "consistent year-round",
                "security": "spikes during audits"
            }
        }
    }
    
    return {
        "success": True,
        "analytics": analytics,
        "time_period": {
            "days_back": days_back,
            "start_date": (datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - 
                          datetime.timedelta(days=days_back)).isoformat() + "Z",
            "end_date": datetime.utcnow().isoformat() + "Z"
        },
        "filters": {
            "team_filter": team_filter
        }
    }

@router.get("/tag-clusters")
async def get_tag_clusters(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get tag clusters and relationships for visualization"""
    
    # Mock tag clustering data
    clusters = {
        "technical_cluster": {
            "center_tag": "authentication",
            "related_tags": ["security", "api", "endpoints", "async", "performance"],
            "strength": 0.85,
            "memory_count": 23
        },
        "process_cluster": {
            "center_tag": "code-review",
            "related_tags": ["testing", "production", "deployment", "standards"],
            "strength": 0.78,
            "memory_count": 18
        },
        "planning_cluster": {
            "center_tag": "sprint",
            "related_tags": ["planning", "goals", "roadmap", "requirements"],
            "strength": 0.72,
            "memory_count": 15
        }
    }
    
    # Tag relationship network for visualization
    tag_network = {
        "nodes": [
            {"id": "authentication", "type": "tag", "cluster": "technical", "size": 23},
            {"id": "performance", "type": "tag", "cluster": "technical", "size": 18},
            {"id": "code-review", "type": "tag", "cluster": "process", "size": 15},
            {"id": "planning", "type": "tag", "cluster": "planning", "size": 12},
            {"id": "mvp", "type": "tag", "cluster": "project", "size": 10}
        ],
        "edges": [
            {"source": "authentication", "target": "performance", "weight": 0.7},
            {"source": "authentication", "target": "code-review", "weight": 0.5},
            {"source": "code-review", "target": "planning", "weight": 0.6},
            {"source": "planning", "target": "mvp", "weight": 0.8}
        ]
    }
    
    return {
        "success": True,
        "clusters": clusters,
        "tag_network": tag_network,
        "visualization_config": {
            "node_size_scale": [5, 25],
            "edge_weight_scale": [1, 5],
            "cluster_colors": {
                "technical": "#4CAF50",
                "process": "#2196F3", 
                "planning": "#FF9800",
                "project": "#9C27B0"
            }
        }
    }
