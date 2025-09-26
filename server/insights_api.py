"""
Insights API - Dashboard Intelligence
Aggregates data from all systems to provide actionable insights for teams and managers
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from auth_utils import get_current_user

router = APIRouter(prefix="/insights", tags=["dashboard"])

# Mock aggregated data from all systems
def get_team_productivity_insights(team_id: int, days_back: int = 30) -> Dict[str, Any]:
    """Get team productivity insights combining all system data"""
    
    # Mock data aggregated from memory, approval, discussion, timeline systems
    return {
        "memory_activity": {
            "memories_created": 23,
            "memories_approved": 18,
            "memories_discussed": 15,
            "avg_memories_per_day": 0.77,
            "trend": "up",
            "quality_score": 0.82
        },
        "approval_efficiency": {
            "avg_approval_time_hours": 18.5,
            "approval_rate": 0.78,
            "pending_approvals": 3,
            "bottleneck_stage": None,
            "process_health": "good"
        },
        "discussion_engagement": {
            "total_comments": 67,
            "avg_comments_per_memory": 2.9,
            "sentiment_score": 0.73,
            "participation_rate": 0.85,
            "most_discussed_topics": ["authentication", "performance", "architecture"]
        },
        "knowledge_growth": {
            "contexts_created": 4,
            "knowledge_connections": 28,
            "tag_diversity": 0.68,
            "knowledge_velocity": 1.2,
            "learning_indicators": ["high cross-referencing", "active tagging", "context building"]
        }
    }

def get_memory_intelligence_insights(team_id: int = None) -> Dict[str, Any]:
    """Get memory intelligence insights using PageRank and AI analysis"""
    
    return {
        "top_memories": [
            {
                "id": "memory_2",
                "title": "GET-based Endpoints Decision",
                "rank_score": 0.89,
                "discussion_count": 3,
                "sentiment_score": 0.9,
                "influence_level": "high"
            },
            {
                "id": "memory_3", 
                "title": "Code Review Results",
                "rank_score": 0.76,
                "discussion_count": 2,
                "sentiment_score": 0.8,
                "influence_level": "medium"
            }
        ],
        "knowledge_clusters": {
            "authentication": {
                "memory_count": 8,
                "discussion_activity": "high",
                "sentiment": "positive",
                "trending": True
            },
            "performance": {
                "memory_count": 6,
                "discussion_activity": "medium", 
                "sentiment": "constructive",
                "trending": True
            },
            "architecture": {
                "memory_count": 5,
                "discussion_activity": "high",
                "sentiment": "positive",
                "trending": False
            }
        },
        "ai_suggestions": {
            "auto_tags_generated": 45,
            "tag_acceptance_rate": 0.67,
            "recommendation_accuracy": 0.74,
            "emerging_topics": ["async", "optimization", "endpoints"]
        }
    }

@router.get("/team/{team_id}/dashboard")
async def get_team_dashboard(
    team_id: int,
    days_back: int = 30,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get comprehensive team dashboard insights"""
    
    # Check team access (simplified)
    user_role = user.get("role", "user")
    if user_role not in ["admin", "org_admin", "team_admin"]:
        raise HTTPException(status_code=403, detail="Access denied - admin role required")
    
    # Get productivity insights
    productivity = get_team_productivity_insights(team_id, days_back)
    
    # Get memory intelligence
    intelligence = get_memory_intelligence_insights(team_id)
    
    # Calculate team health score
    health_factors = [
        productivity["memory_activity"]["quality_score"],
        productivity["approval_efficiency"]["approval_rate"],
        productivity["discussion_engagement"]["sentiment_score"],
        productivity["knowledge_growth"]["knowledge_velocity"] / 2.0  # Normalize to 0-1
    ]
    team_health_score = sum(health_factors) / len(health_factors)
    
    # Identify key insights and recommendations
    insights = []
    recommendations = []
    
    # Memory activity insights
    if productivity["memory_activity"]["trend"] == "up":
        insights.append("📈 Memory creation is trending upward - team is actively capturing knowledge")
    
    if productivity["approval_efficiency"]["avg_approval_time_hours"] > 24:
        recommendations.append("⚡ Consider streamlining approval process - current avg time is 18.5 hours")
    
    if productivity["discussion_engagement"]["sentiment_score"] > 0.7:
        insights.append("😊 Team discussions are predominantly positive - healthy collaboration")
    
    if intelligence["ai_suggestions"]["tag_acceptance_rate"] < 0.7:
        recommendations.append("🏷️ Review AI tag suggestions - acceptance rate could be improved")
    
    return {
        "success": True,
        "team_id": team_id,
        "dashboard": {
            "team_health_score": team_health_score,
            "productivity_metrics": productivity,
            "intelligence_insights": intelligence,
            "key_insights": insights,
            "recommendations": recommendations,
            "time_period": {
                "days_back": days_back,
                "start_date": (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z",
                "end_date": datetime.utcnow().isoformat() + "Z"
            }
        },
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/memory-trends")
async def get_memory_trends(
    days_back: int = 30,
    team_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get memory creation and engagement trends over time"""
    
    # Mock trend data - in real implementation, aggregate from timeline and memory systems
    trend_data = []
    
    # Generate daily trend data for the past days_back
    for i in range(days_back, 0, -1):
        date = datetime.utcnow() - timedelta(days=i)
        
        # Mock daily metrics with some variation
        base_memories = 2 if i % 7 < 5 else 1  # Weekday vs weekend pattern
        variation = (i % 3) - 1  # Add some variation
        
        trend_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "memories_created": max(0, base_memories + variation),
            "memories_approved": max(0, base_memories + variation - 1),
            "comments_added": max(0, (base_memories + variation) * 2),
            "contexts_linked": max(0, base_memories + variation // 2),
            "avg_sentiment": 0.7 + (i % 5) * 0.05,  # Vary between 0.7-0.9
            "pagerank_activity": 0.5 + (i % 4) * 0.1   # Vary between 0.5-0.8
        })
    
    # Calculate trend indicators
    recent_week = trend_data[-7:]
    previous_week = trend_data[-14:-7] if len(trend_data) >= 14 else trend_data[:7]
    
    recent_avg_memories = sum(d["memories_created"] for d in recent_week) / len(recent_week)
    previous_avg_memories = sum(d["memories_created"] for d in previous_week) / len(previous_week)
    
    memory_trend = "up" if recent_avg_memories > previous_avg_memories else "down" if recent_avg_memories < previous_avg_memories else "stable"
    
    return {
        "success": True,
        "trends": {
            "daily_data": trend_data,
            "summary": {
                "total_memories": sum(d["memories_created"] for d in trend_data),
                "total_approvals": sum(d["memories_approved"] for d in trend_data),
                "total_comments": sum(d["comments_added"] for d in trend_data),
                "avg_daily_memories": sum(d["memories_created"] for d in trend_data) / len(trend_data),
                "memory_trend": memory_trend,
                "avg_sentiment": sum(d["avg_sentiment"] for d in trend_data) / len(trend_data)
            }
        },
        "visualization_config": {
            "chart_type": "line",
            "x_axis": "date",
            "y_axes": ["memories_created", "memories_approved", "comments_added"],
            "colors": {
                "memories_created": "#4CAF50",
                "memories_approved": "#2196F3", 
                "comments_added": "#FF9800"
            }
        },
        "filters": {
            "days_back": days_back,
            "team_filter": team_filter
        }
    }

@router.get("/sentiment-analysis")
async def get_sentiment_analysis(
    days_back: int = 30,
    team_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get sentiment analysis across discussions and memories"""
    
    # Mock sentiment data aggregated from discussion system
    sentiment_data = {
        "overall_sentiment": {
            "score": 0.73,
            "trend": "positive",
            "distribution": {
                "positive": 0.45,
                "neutral": 0.35,
                "constructive": 0.15,
                "negative": 0.05
            }
        },
        "sentiment_by_topic": {
            "authentication": {"score": 0.82, "volume": 23, "trend": "stable"},
            "performance": {"score": 0.78, "volume": 18, "trend": "up"},
            "architecture": {"score": 0.71, "volume": 15, "trend": "up"},
            "code-review": {"score": 0.85, "volume": 12, "trend": "stable"},
            "planning": {"score": 0.69, "volume": 8, "trend": "down"}
        },
        "sentiment_timeline": [
            {"date": "2025-01-20", "positive": 0.7, "neutral": 0.2, "constructive": 0.1, "negative": 0.0},
            {"date": "2025-01-21", "positive": 0.8, "neutral": 0.15, "constructive": 0.05, "negative": 0.0},
            {"date": "2025-01-22", "positive": 0.6, "neutral": 0.3, "constructive": 0.1, "negative": 0.0},
            {"date": "2025-01-23", "positive": 0.75, "neutral": 0.2, "constructive": 0.05, "negative": 0.0},
            {"date": "2025-01-24", "positive": 0.9, "neutral": 0.1, "constructive": 0.0, "negative": 0.0}
        ],
        "user_sentiment_patterns": {
            "123": {"name": "Team Admin", "avg_sentiment": 0.78, "comment_count": 15, "positivity_trend": "stable"},
            "456": {"name": "Project Owner", "avg_sentiment": 0.85, "comment_count": 12, "positivity_trend": "up"},
            "789": {"name": "Team Member", "avg_sentiment": 0.65, "comment_count": 8, "positivity_trend": "up"}
        }
    }
    
    # Generate insights based on sentiment data
    insights = []
    
    if sentiment_data["overall_sentiment"]["score"] > 0.7:
        insights.append("😊 Team communication is predominantly positive - healthy collaboration environment")
    
    # Find most positive topic
    most_positive_topic = max(sentiment_data["sentiment_by_topic"].items(), key=lambda x: x[1]["score"])
    insights.append(f"🌟 '{most_positive_topic[0]}' generates the most positive discussions (score: {most_positive_topic[1]['score']:.2f})")
    
    # Check for trending topics
    trending_up = [topic for topic, data in sentiment_data["sentiment_by_topic"].items() if data["trend"] == "up"]
    if trending_up:
        insights.append(f"📈 Trending topics with improving sentiment: {', '.join(trending_up)}")
    
    return {
        "success": True,
        "sentiment_analysis": sentiment_data,
        "insights": insights,
        "recommendations": [
            "Continue fostering positive discussions around high-performing topics",
            "Monitor topics with declining sentiment for potential issues",
            "Recognize team members with consistently positive contributions"
        ],
        "time_period": {
            "days_back": days_back,
            "start_date": (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z",
            "end_date": datetime.utcnow().isoformat() + "Z"
        }
    }

@router.get("/knowledge-hotspots")
async def get_knowledge_hotspots(
    team_filter: Optional[int] = None,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get knowledge hotspots - most discussed and linked topics per context"""
    
    # Mock hotspot data combining context, memory, and discussion data
    hotspots = [
        {
            "context_id": "context_1",
            "context_title": "Auth System Development",
            "hotspot_score": 0.89,
            "memory_count": 8,
            "discussion_count": 23,
            "avg_sentiment": 0.82,
            "top_memories": [
                {
                    "id": "memory_2",
                    "title": "GET-based Endpoints Decision",
                    "discussion_count": 5,
                    "pagerank_score": 0.89
                },
                {
                    "id": "memory_3",
                    "title": "Code Review Results", 
                    "discussion_count": 3,
                    "pagerank_score": 0.76
                }
            ],
            "trending_tags": ["authentication", "performance", "endpoints"],
            "activity_trend": "up",
            "knowledge_density": 0.75
        },
        {
            "context_id": "context_2",
            "context_title": "Performance Optimization",
            "hotspot_score": 0.72,
            "memory_count": 5,
            "discussion_count": 15,
            "avg_sentiment": 0.78,
            "top_memories": [
                {
                    "id": "memory_5",
                    "title": "Database Query Optimization",
                    "discussion_count": 4,
                    "pagerank_score": 0.68
                }
            ],
            "trending_tags": ["performance", "database", "optimization"],
            "activity_trend": "stable",
            "knowledge_density": 0.68
        }
    ]
    
    # Calculate overall knowledge landscape metrics
    total_discussions = sum(h["discussion_count"] for h in hotspots)
    total_memories = sum(h["memory_count"] for h in hotspots)
    avg_sentiment = sum(h["avg_sentiment"] for h in hotspots) / len(hotspots)
    
    return {
        "success": True,
        "knowledge_hotspots": hotspots,
        "landscape_metrics": {
            "total_hotspots": len(hotspots),
            "total_discussions": total_discussions,
            "total_memories": total_memories,
            "avg_sentiment": avg_sentiment,
            "knowledge_concentration": 0.73,  # How concentrated knowledge is in hotspots
            "cross_pollination_score": 0.65   # How much knowledge flows between contexts
        },
        "visualization_data": {
            "heatmap_data": [
                {"context": h["context_title"], "activity": h["hotspot_score"], "sentiment": h["avg_sentiment"]}
                for h in hotspots
            ],
            "network_data": {
                "nodes": [{"id": h["context_id"], "label": h["context_title"], "size": h["memory_count"]} for h in hotspots],
                "edges": [
                    {"source": "context_1", "target": "context_2", "weight": 0.4, "type": "knowledge_flow"}
                ]
            }
        },
        "filters": {
            "team_filter": team_filter
        }
    }

@router.get("/ai-performance")
async def get_ai_performance_metrics(
    days_back: int = 30,
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI system performance metrics for PageRank and tag suggestions"""
    
    # Mock AI performance data
    ai_metrics = {
        "pagerank_performance": {
            "algorithm_accuracy": 0.84,
            "ranking_stability": 0.91,
            "user_satisfaction": 0.78,
            "computation_time_ms": 45,
            "memory_ranking_changes": 12,
            "top_ranked_accuracy": 0.89
        },
        "tag_suggestion_performance": {
            "suggestion_accuracy": 0.73,
            "acceptance_rate": 0.67,
            "avg_confidence_score": 0.78,
            "suggestions_generated": 156,
            "suggestions_accepted": 104,
            "user_feedback_score": 4.2,
            "processing_time_ms": 120
        },
        "recommendation_engine": {
            "recommendation_accuracy": 0.71,
            "click_through_rate": 0.34,
            "user_engagement_lift": 0.23,
            "recommendations_served": 89,
            "positive_feedback": 67
        },
        "model_performance_trends": [
            {"date": "2025-01-20", "pagerank_accuracy": 0.82, "tag_accuracy": 0.71, "recommendation_ctr": 0.32},
            {"date": "2025-01-21", "pagerank_accuracy": 0.83, "tag_accuracy": 0.72, "recommendation_ctr": 0.33},
            {"date": "2025-01-22", "pagerank_accuracy": 0.84, "tag_accuracy": 0.73, "recommendation_ctr": 0.34},
            {"date": "2025-01-23", "pagerank_accuracy": 0.85, "tag_accuracy": 0.74, "recommendation_ctr": 0.35},
            {"date": "2025-01-24", "pagerank_accuracy": 0.84, "tag_accuracy": 0.73, "recommendation_ctr": 0.34}
        ]
    }
    
    # Generate AI insights and recommendations
    ai_insights = []
    ai_recommendations = []
    
    if ai_metrics["pagerank_performance"]["algorithm_accuracy"] > 0.8:
        ai_insights.append("🎯 PageRank algorithm is performing well with 84% accuracy")
    
    if ai_metrics["tag_suggestion_performance"]["acceptance_rate"] < 0.7:
        ai_recommendations.append("🏷️ Consider fine-tuning tag suggestion model - acceptance rate is 67%")
    
    if ai_metrics["recommendation_engine"]["click_through_rate"] > 0.3:
        ai_insights.append("🎯 Recommendation engine is driving good engagement with 34% CTR")
    
    return {
        "success": True,
        "ai_performance": ai_metrics,
        "insights": ai_insights,
        "recommendations": ai_recommendations,
        "optimization_opportunities": [
            "Increase tag suggestion confidence threshold to improve acceptance rate",
            "A/B test different PageRank damping factors for better ranking",
            "Incorporate user feedback loops to improve recommendation accuracy"
        ],
        "time_period": {
            "days_back": days_back,
            "start_date": (datetime.utcnow() - timedelta(days=days_back)).isoformat() + "Z",
            "end_date": datetime.utcnow().isoformat() + "Z"
        }
    }
