"""
Graph Intelligence Models
Data models for advanced graph intelligence features
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class SharingPolicy(Enum):
    """Memory sharing policy levels"""
    PRIVATE = "private"
    TEAM_ONLY = "team_only"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"
    PUBLIC = "public"


class PrivacyLevel(Enum):
    """Privacy levels for memory content"""
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    PUBLIC = "public"


@dataclass
class TeamContext:
    """Team context for memory federation"""
    team_id: str
    team_name: str
    department: str
    organization: str
    access_level: int
    specializations: List[str] = field(default_factory=list)
    collaboration_history: Dict[str, float] = field(default_factory=dict)


@dataclass
class SharingRule:
    """Rules for memory sharing between teams"""
    rule_id: str
    source_team: str
    target_teams: List[str]
    content_filters: List[str]
    privacy_level: PrivacyLevel
    sharing_policy: SharingPolicy
    auto_approve: bool = False
    expiry_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FederatedMemory:
    """Memory with federation metadata"""
    memory_id: str
    original_team: str
    shared_with: List[str]
    sharing_score: float
    privacy_filtered: bool
    federation_timestamp: datetime
    access_count: int = 0
    feedback_score: Optional[float] = None


@dataclass
class FederationResult:
    """Result of memory federation operation"""
    success: bool
    federated_memories: List[FederatedMemory]
    filtered_count: int
    sharing_policies_applied: List[str]
    privacy_violations: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class GraphContext:
    """Context for graph-aware ML operations"""
    user_id: str
    team_context: TeamContext
    current_task: Optional[str] = None
    recent_memories: List[str] = field(default_factory=list)
    collaboration_network: Dict[str, float] = field(default_factory=dict)
    expertise_areas: List[str] = field(default_factory=list)


@dataclass
class ScoredMemory:
    """Memory with ML-generated relevance score"""
    memory_id: str
    content_preview: str
    relevance_score: float
    confidence: float
    reasoning: List[str]
    graph_connections: List[str] = field(default_factory=list)
    temporal_relevance: float = 0.0
    team_relevance: float = 0.0


@dataclass
class RelationshipPrediction:
    """Predicted relationship between memories"""
    memory_a: str
    memory_b: str
    relationship_type: str
    confidence: float
    supporting_evidence: List[str]
    graph_path: List[str] = field(default_factory=list)


@dataclass
class EmbeddingUpdate:
    """Update to memory embeddings based on graph intelligence"""
    memory_id: str
    original_embedding: List[float]
    enhanced_embedding: List[float]
    improvement_score: float
    graph_features: Dict[str, float]
    update_timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserFeedback:
    """User feedback for adaptive learning"""
    feedback_id: str
    user_id: str
    memory_id: str
    query: str
    relevance_rating: int  # 1-5 scale
    usefulness_rating: int  # 1-5 scale
    context_accuracy: int  # 1-5 scale
    feedback_text: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WeightUpdate:
    """Update to ranking weights based on feedback"""
    feature_weights: Dict[str, float]
    confidence_threshold: float
    learning_rate: float
    update_reason: str
    performance_improvement: float


@dataclass
class KnowledgeGap:
    """Identified gap in team knowledge"""
    gap_id: str
    team_id: str
    topic_area: str
    confidence: float
    suggested_sources: List[str]
    urgency_score: float
    related_queries: List[str] = field(default_factory=list)
    potential_experts: List[str] = field(default_factory=list)


@dataclass
class TrendingTopic:
    """Trending topic in memory access patterns"""
    topic: str
    trend_score: float
    growth_rate: float
    related_memories: List[str]
    teams_involved: List[str]
    time_window: str
    peak_timestamp: datetime


@dataclass
class SuggestedConnection:
    """Suggested connection between memories"""
    source_memory: str
    target_memory: str
    connection_type: str
    confidence: float
    reasoning: str
    potential_value: float


@dataclass
class TeamInsights:
    """Generated insights for a team"""
    team_id: str
    knowledge_coverage: Dict[str, float]
    collaboration_patterns: Dict[str, Any]
    trending_topics: List[TrendingTopic]
    knowledge_gaps: List[KnowledgeGap]
    productivity_metrics: Dict[str, float]
    recommendations: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GraphMLMetrics:
    """Metrics for graph ML performance"""
    model_accuracy: float
    prediction_confidence: float
    processing_latency_ms: float
    memory_usage_mb: float
    throughput_qps: float
    error_rate: float
    last_training: datetime
    model_version: str


@dataclass
class FederationMetrics:
    """Metrics for memory federation performance"""
    total_federations: int
    successful_shares: int
    privacy_blocks: int
    average_sharing_score: float
    cross_team_discoveries: int
    federation_latency_ms: float
    user_satisfaction: float
    knowledge_reuse_rate: float
