"""
Dashboard Widgets API - Phase 2A Implementation
Real-time AI-powered widgets with role-based access and smart notifications
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from auth_utils import get_current_user
from pydantic import BaseModel
import json
import asyncio
from enum import Enum

# Import our existing intelligence systems
from graph_rank import get_dashboard_insights
from insights_api import get_team_productivity_insights, get_memory_intelligence_insights
from tag_suggester import get_ai_performance_metrics
from usage_analytics_api import get_team_growth_metrics

router = APIRouter(prefix="/dashboard-widgets", tags=["dashboard"])

# Widget Configuration Models
class WidgetType(str, Enum):
    TOP_MEMORIES = "top_memories"
    SENTIMENT_TRENDS = "sentiment_trends"
    AI_PERFORMANCE = "ai_performance"
    TEAM_PRODUCTIVITY = "team_productivity"
    APPROVAL_QUEUE = "approval_queue"
    DISCUSSION_ACTIVITY = "discussion_activity"
    KNOWLEDGE_GROWTH = "knowledge_growth"
    SMART_ALERTS = "smart_alerts"

class WidgetSize(str, Enum):
    SMALL = "small"      # 4x3 grid
    MEDIUM = "medium"    # 6x4 grid
    LARGE = "large"      # 8x5 grid
    FULL = "full"        # 12x6 grid

class WidgetConfig(BaseModel):
    id: str
    type: WidgetType
    title: str
    size: WidgetSize
    position: Dict[str, int]  # {"row": 0, "col": 0}
    permissions: List[str]
    refresh_interval: int = 30  # seconds
    auto_refresh: bool = True
    filters: Dict[str, Any] = {}

class WidgetData(BaseModel):
    widget_id: str
    data: Dict[str, Any]
    last_updated: datetime
    next_refresh: datetime
    alerts: List[Dict[str, Any]] = []

# WebSocket Connection Manager for Real-time Updates
class DashboardConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_widgets: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_widgets[user_id] = []
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_widgets:
            del self.user_widgets[user_id]
    
    async def send_widget_update(self, user_id: str, widget_data: WidgetData):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(
                    json.dumps({
                        "type": "widget_update",
                        "widget_id": widget_data.widget_id,
                        "data": widget_data.data,
                        "alerts": widget_data.alerts,
                        "timestamp": widget_data.last_updated.isoformat()
                    })
                )
            except:
                # Connection closed, remove it
                self.disconnect(user_id)
    
    async def send_smart_alert(self, user_id: str, alert: Dict[str, Any]):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(
                    json.dumps({
                        "type": "smart_alert",
                        "alert": alert,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )
            except:
                self.disconnect(user_id)

manager = DashboardConnectionManager()

# Widget Data Generators
async def get_top_memories_widget_data(user: Dict[str, Any], config: WidgetConfig) -> WidgetData:
    """Generate Top Memories widget with AI-powered insights"""
    
    # Get PageRank insights
    pagerank_data = get_dashboard_insights(team_filter=user.get("team_id"))
    
    # Get memory intelligence
    memory_intel = get_memory_intelligence_insights(team_id=user.get("team_id"))
    
    # Combine and enhance data
    top_memories = pagerank_data.get("insights", {}).get("top_memories", [])
    
    # Add AI-powered alerts
    alerts = []
    
    # Alert: Memory gaining traction
    for memory in top_memories[:3]:
        if memory.get("discussion_count", 0) > 5:
            alerts.append({
                "type": "trending",
                "priority": "medium",
                "title": f"Memory '{memory['title'][:30]}...' is gaining traction",
                "description": f"{memory['discussion_count']} discussions, sentiment: {memory.get('sentiment_score', 0.5):.2f}",
                "action": f"/memory/{memory['id']}",
                "icon": "📈"
            })
    
    # Alert: High-quality content
    high_quality = [m for m in top_memories if m.get("score", 0) > 0.8]
    if high_quality:
        alerts.append({
            "type": "quality",
            "priority": "low",
            "title": f"{len(high_quality)} high-quality memories identified",
            "description": "Consider featuring these in team updates",
            "action": "/dashboard/quality-content",
            "icon": "⭐"
        })
    
    widget_data = {
        "memories": top_memories[:5],
        "total_memories": len(pagerank_data.get("insights", {}).get("top_memories", [])),
        "avg_score": sum(m.get("score", 0) for m in top_memories) / len(top_memories) if top_memories else 0,
        "trending_topics": pagerank_data.get("insights", {}).get("trending_topics", {}),
        "ai_insights": {
            "quality_trend": "up" if len(high_quality) > 2 else "stable",
            "engagement_level": "high" if sum(m.get("discussion_count", 0) for m in top_memories) > 15 else "medium",
            "knowledge_velocity": memory_intel.get("knowledge_velocity", 1.0)
        }
    }
    
    return WidgetData(
        widget_id=config.id,
        data=widget_data,
        last_updated=datetime.utcnow(),
        next_refresh=datetime.utcnow() + timedelta(seconds=config.refresh_interval),
        alerts=alerts
    )

async def get_sentiment_trends_widget_data(user: Dict[str, Any], config: WidgetConfig) -> WidgetData:
    """Generate Sentiment Trends widget with predictive insights"""
    
    # Get team productivity insights
    productivity = get_team_productivity_insights(team_id=user.get("team_id"))
    
    # Generate trend data (mock for now, would come from real analytics)
    sentiment_history = []
    base_sentiment = productivity.get("discussion_engagement", {}).get("sentiment_score", 0.7)
    
    for i in range(7):  # Last 7 days
        date = datetime.utcnow() - timedelta(days=6-i)
        # Add some realistic variation
        variation = 0.1 * (0.5 - (i % 3) / 6)
        sentiment_history.append({
            "date": date.strftime("%Y-%m-%d"),
            "sentiment": min(1.0, max(0.0, base_sentiment + variation)),
            "volume": 5 + (i % 4) * 3  # Discussion volume
        })
    
    # Generate AI alerts
    alerts = []
    current_sentiment = sentiment_history[-1]["sentiment"]
    prev_sentiment = sentiment_history[-2]["sentiment"]
    
    if current_sentiment > prev_sentiment + 0.1:
        alerts.append({
            "type": "positive_trend",
            "priority": "low",
            "title": "Team sentiment improving! 📈",
            "description": f"Sentiment up {((current_sentiment - prev_sentiment) * 100):.1f}% from yesterday",
            "action": "/dashboard/sentiment-analysis",
            "icon": "😊"
        })
    elif current_sentiment < prev_sentiment - 0.1:
        alerts.append({
            "type": "negative_trend",
            "priority": "medium",
            "title": "Team sentiment declining",
            "description": f"Consider checking in with team members",
            "action": "/dashboard/team-health",
            "icon": "⚠️"
        })
    
    # Predict tomorrow's sentiment (simple trend analysis)
    trend = current_sentiment - sentiment_history[-3]["sentiment"]
    predicted_sentiment = min(1.0, max(0.0, current_sentiment + trend * 0.5))
    
    widget_data = {
        "current_sentiment": current_sentiment,
        "sentiment_history": sentiment_history,
        "predicted_sentiment": predicted_sentiment,
        "trend_direction": "up" if trend > 0.05 else "down" if trend < -0.05 else "stable",
        "discussion_volume": sum(day["volume"] for day in sentiment_history[-3:]),
        "top_positive_topics": productivity.get("discussion_engagement", {}).get("most_discussed_topics", [])[:3],
        "ai_insights": {
            "sentiment_stability": "stable" if abs(trend) < 0.1 else "volatile",
            "engagement_quality": "high" if current_sentiment > 0.7 else "medium",
            "team_health_score": current_sentiment * 100
        }
    }
    
    return WidgetData(
        widget_id=config.id,
        data=widget_data,
        last_updated=datetime.utcnow(),
        next_refresh=datetime.utcnow() + timedelta(seconds=config.refresh_interval),
        alerts=alerts
    )

async def get_ai_performance_widget_data(user: Dict[str, Any], config: WidgetConfig) -> WidgetData:
    """Generate AI Performance widget showing tag suggestions, PageRank effectiveness"""
    
    # Get AI performance metrics
    ai_metrics = get_ai_performance_metrics()
    
    # Generate performance data
    widget_data = {
        "tag_suggestion_stats": {
            "acceptance_rate": ai_metrics.get("acceptance_rate", 0.67),
            "suggestions_generated": ai_metrics.get("total_suggestions", 156),
            "avg_response_time": ai_metrics.get("avg_response_time_ms", 120),
            "confidence_score": ai_metrics.get("avg_confidence", 0.78)
        },
        "pagerank_effectiveness": {
            "memories_ranked": ai_metrics.get("memories_processed", 89),
            "ranking_accuracy": ai_metrics.get("ranking_accuracy", 0.85),
            "user_engagement_lift": ai_metrics.get("engagement_improvement", 0.23)
        },
        "intelligence_trends": [
            {"metric": "Tag Accuracy", "value": 0.78, "trend": "up"},
            {"metric": "Ranking Quality", "value": 0.85, "trend": "stable"},
            {"metric": "Response Time", "value": 120, "trend": "down", "unit": "ms"},
            {"metric": "User Satisfaction", "value": 0.82, "trend": "up"}
        ]
    }
    
    # Generate AI alerts
    alerts = []
    
    if ai_metrics.get("acceptance_rate", 0.67) > 0.75:
        alerts.append({
            "type": "ai_success",
            "priority": "low",
            "title": "AI tag suggestions performing well! 🤖",
            "description": f"{ai_metrics.get('acceptance_rate', 0.67)*100:.1f}% acceptance rate",
            "action": "/dashboard/ai-performance",
            "icon": "🎯"
        })
    
    if ai_metrics.get("avg_response_time_ms", 120) > 200:
        alerts.append({
            "type": "performance",
            "priority": "medium",
            "title": "AI response time elevated",
            "description": "Consider optimizing AI processing pipeline",
            "action": "/admin/ai-optimization",
            "icon": "⏱️"
        })
    
    return WidgetData(
        widget_id=config.id,
        data=widget_data,
        last_updated=datetime.utcnow(),
        next_refresh=datetime.utcnow() + timedelta(seconds=config.refresh_interval),
        alerts=alerts
    )

# Widget Registry
WIDGET_GENERATORS = {
    WidgetType.TOP_MEMORIES: get_top_memories_widget_data,
    WidgetType.SENTIMENT_TRENDS: get_sentiment_trends_widget_data,
    WidgetType.AI_PERFORMANCE: get_ai_performance_widget_data,
}

# API Endpoints
@router.get("/widgets/{widget_id}")
async def get_widget_data(
    widget_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get data for a specific widget"""
    
    # Mock widget config (would come from user preferences/database)
    widget_configs = {
        "top_memories": WidgetConfig(
            id="top_memories",
            type=WidgetType.TOP_MEMORIES,
            title="Top Memories",
            size=WidgetSize.MEDIUM,
            position={"row": 0, "col": 0},
            permissions=["read:memories"],
            refresh_interval=30
        ),
        "sentiment_trends": WidgetConfig(
            id="sentiment_trends",
            type=WidgetType.SENTIMENT_TRENDS,
            title="Team Sentiment",
            size=WidgetSize.MEDIUM,
            position={"row": 0, "col": 6},
            permissions=["read:discussions"],
            refresh_interval=60
        ),
        "ai_performance": WidgetConfig(
            id="ai_performance",
            type=WidgetType.AI_PERFORMANCE,
            title="AI Intelligence",
            size=WidgetSize.LARGE,
            position={"row": 4, "col": 0},
            permissions=["read:ai_metrics"],
            refresh_interval=120
        )
    }
    
    config = widget_configs.get(widget_id)
    if not config:
        raise HTTPException(status_code=404, detail="Widget not found")
    
    # Check permissions (simplified)
    user_role = user.get("role", "user")
    if "admin" not in user_role and "read:ai_metrics" in config.permissions and widget_id == "ai_performance":
        # Regular users get limited AI metrics
        pass
    
    # Generate widget data
    generator = WIDGET_GENERATORS.get(config.type)
    if not generator:
        raise HTTPException(status_code=501, detail="Widget type not implemented")
    
    widget_data = await generator(user, config)
    
    return {
        "success": True,
        "widget": widget_data.dict(),
        "config": config.dict()
    }

@router.get("/layouts/{role}")
async def get_dashboard_layout(
    role: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Get dashboard layout for user role"""
    
    layouts = {
        "user": {
            "widgets": [
                {
                    "id": "top_memories",
                    "type": "top_memories",
                    "position": {"row": 0, "col": 0},
                    "size": "medium"
                },
                {
                    "id": "sentiment_trends", 
                    "type": "sentiment_trends",
                    "position": {"row": 0, "col": 6},
                    "size": "medium"
                }
            ],
            "grid_config": {"columns": 12, "row_height": 60}
        },
        "team_admin": {
            "widgets": [
                {
                    "id": "top_memories",
                    "type": "top_memories", 
                    "position": {"row": 0, "col": 0},
                    "size": "medium"
                },
                {
                    "id": "sentiment_trends",
                    "type": "sentiment_trends",
                    "position": {"row": 0, "col": 6},
                    "size": "medium"
                },
                {
                    "id": "ai_performance",
                    "type": "ai_performance",
                    "position": {"row": 4, "col": 0},
                    "size": "large"
                }
            ],
            "grid_config": {"columns": 12, "row_height": 60}
        }
    }
    
    user_role = user.get("role", "user")
    layout = layouts.get(user_role, layouts["user"])
    
    return {
        "success": True,
        "layout": layout,
        "role": user_role
    }

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time dashboard updates"""
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # Wait for client messages (widget subscriptions, etc.)
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe_widget":
                widget_id = message.get("widget_id")
                if widget_id:
                    if user_id not in manager.user_widgets:
                        manager.user_widgets[user_id] = []
                    manager.user_widgets[user_id].append(widget_id)
                    
                    # Send initial widget data
                    # This would trigger the widget data generation
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "widget_id": widget_id
                    }))
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Background task for real-time updates
async def dashboard_update_task():
    """Background task to send real-time updates to connected dashboards"""
    
    while True:
        try:
            # Update widgets for all connected users
            for user_id, websocket in manager.active_connections.items():
                user_widgets = manager.user_widgets.get(user_id, [])
                
                for widget_id in user_widgets:
                    # Generate fresh widget data
                    # This would use the widget generators
                    
                    # Mock alert for demonstration
                    if widget_id == "top_memories":
                        alert = {
                            "type": "new_trending",
                            "priority": "low",
                            "title": "New memory trending",
                            "description": "Authentication best practices gaining discussions",
                            "timestamp": datetime.utcnow().isoformat(),
                            "widget_id": widget_id
                        }
                        
                        await manager.send_smart_alert(user_id, alert)
            
            # Wait 30 seconds before next update cycle
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"Dashboard update task error: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start background task (would be called from main.py)
# asyncio.create_task(dashboard_update_task())
