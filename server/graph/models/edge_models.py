"""
SPEC-060 Apache AGE Edge Models
Python dataclass models for property graph relationships with Redis integration
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RelationshipType(Enum):
    """Enumeration of supported relationship types in the property graph"""

    CREATED = "CREATED"
    LINKED_TO = "LINKED_TO"
    TRIGGERED_BY = "TRIGGERED_BY"
    TAGGED_WITH = "TAGGED_WITH"
    DERIVED_FROM = "DERIVED_FROM"
    BELONGS_TO = "BELONGS_TO"
    MEMBER_OF = "MEMBER_OF"
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    INFLUENCES = "INFLUENCES"
    PARTICIPATED_IN = "PARTICIPATED_IN"
    CREATED_IN = "CREATED_IN"
    DEPENDS_ON = "DEPENDS_ON"
    SIMILAR_TO = "SIMILAR_TO"
    FOLLOWS = "FOLLOWS"


@dataclass
class BaseEdge:
    """Base class for all graph edges/relationships"""

    id: str
    source_id: str
    target_id: str
    relationship_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

        # Generate ID if not provided
        if not self.id:
            self.id = f"{self.source_id}_{self.relationship_type}_{self.target_id}"

    def to_cypher_properties(self) -> str:
        """Convert edge properties to Cypher format"""
        props = {
            "weight": self.weight,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            **self.properties,
        }
        # Remove None values
        props = {k: v for k, v in props.items() if v is not None}

        # Format for Cypher (single quotes for strings)
        formatted_props = {}
        for k, v in props.items():
            if isinstance(v, str):
                formatted_props[k] = f"'{v}'"
            else:
                formatted_props[k] = v

        prop_strings = [f"{k}: {v}" for k, v in formatted_props.items()]
        return "{" + ", ".join(prop_strings) + "}"

    def to_cypher_create(self) -> str:
        """Generate Cypher CREATE statement for this edge"""
        props = self.to_cypher_properties()
        return f"""
        MATCH (a {{id: '{self.source_id}'}}), (b {{id: '{self.target_id}'}})
        CREATE (a)-[r:{self.relationship_type} {props}]->(b)
        RETURN r
        """


@dataclass
class CreatedEdge(BaseEdge):
    """CREATED relationship - User/Agent created entity"""

    confidence: float = 1.0
    timestamp: Optional[str] = None

    def __post_init__(self):
        self.relationship_type = RelationshipType.CREATED.value
        self.properties.update(
            {
                "confidence": self.confidence,
                "timestamp": self.timestamp or datetime.utcnow().isoformat(),
            }
        )
        super().__post_init__()


@dataclass
class LinkedToEdge(BaseEdge):
    """LINKED_TO relationship - Memory linked to macro/topic"""

    relevance: str = "medium"  # low, medium, high
    link_type: str = "semantic"  # semantic, causal, temporal

    def __post_init__(self):
        self.relationship_type = RelationshipType.LINKED_TO.value
        self.properties.update(
            {"relevance": self.relevance, "link_type": self.link_type}
        )
        super().__post_init__()


@dataclass
class TriggeredByEdge(BaseEdge):
    """TRIGGERED_BY relationship - Macro triggered by agent"""

    frequency: str = "manual"  # manual, daily, weekly, on_event
    automation_level: float = 0.0
    success_rate: float = 1.0

    def __post_init__(self):
        self.relationship_type = RelationshipType.TRIGGERED_BY.value
        self.properties.update(
            {
                "frequency": self.frequency,
                "automation_level": self.automation_level,
                "success_rate": self.success_rate,
            }
        )
        super().__post_init__()


@dataclass
class TaggedWithEdge(BaseEdge):
    """TAGGED_WITH relationship - Entity tagged with topic"""

    relevance: float = 1.0
    auto_tagged: bool = False
    confidence: float = 1.0

    def __post_init__(self):
        self.relationship_type = RelationshipType.TAGGED_WITH.value
        self.properties.update(
            {
                "relevance": self.relevance,
                "auto_tagged": self.auto_tagged,
                "confidence": self.confidence,
            }
        )
        super().__post_init__()


@dataclass
class DerivedFromEdge(BaseEdge):
    """DERIVED_FROM relationship - Memory derived from source"""

    extraction_confidence: float = 1.0
    extraction_method: str = "manual"
    source_section: Optional[str] = None

    def __post_init__(self):
        self.relationship_type = RelationshipType.DERIVED_FROM.value
        self.properties.update(
            {
                "extraction_confidence": self.extraction_confidence,
                "extraction_method": self.extraction_method,
                "source_section": self.source_section,
            }
        )
        super().__post_init__()


@dataclass
class MemberOfEdge(BaseEdge):
    """MEMBER_OF relationship - User member of team/organization"""

    role: str = "member"
    since: Optional[str] = None
    permissions: str = "read"
    active: bool = True

    def __post_init__(self):
        self.relationship_type = RelationshipType.MEMBER_OF.value
        self.properties.update(
            {
                "role": self.role,
                "since": self.since or datetime.utcnow().date().isoformat(),
                "permissions": self.permissions,
                "active": self.active,
            }
        )
        super().__post_init__()


@dataclass
class BelongsToEdge(BaseEdge):
    """BELONGS_TO relationship - Team belongs to organization"""

    department: Optional[str] = None
    budget_allocation: float = 0.0
    reporting_structure: str = "direct"

    def __post_init__(self):
        self.relationship_type = RelationshipType.BELONGS_TO.value
        self.properties.update(
            {
                "department": self.department,
                "budget_allocation": self.budget_allocation,
                "reporting_structure": self.reporting_structure,
            }
        )
        super().__post_init__()


@dataclass
class InfluencesEdge(BaseEdge):
    """INFLUENCES relationship - Cross-entity influence with weights"""

    influence_type: str = "general"  # prerequisite, causal, temporal, semantic
    strength: float = 0.5  # 0.0 to 1.0
    bidirectional: bool = False

    def __post_init__(self):
        self.relationship_type = RelationshipType.INFLUENCES.value
        self.properties.update(
            {
                "influence_type": self.influence_type,
                "strength": self.strength,
                "bidirectional": self.bidirectional,
            }
        )
        super().__post_init__()


@dataclass
class ParticipatedInEdge(BaseEdge):
    """PARTICIPATED_IN relationship - User participated in context"""

    role: str = "participant"  # primary, secondary, observer
    engagement: float = 0.5  # 0.0 to 1.0
    duration: Optional[int] = None  # Duration in seconds

    def __post_init__(self):
        self.relationship_type = RelationshipType.PARTICIPATED_IN.value
        self.properties.update(
            {
                "role": self.role,
                "engagement": self.engagement,
                "duration": self.duration,
            }
        )
        super().__post_init__()


@dataclass
class CreatedInEdge(BaseEdge):
    """CREATED_IN relationship - Entity created in context"""

    relevance: float = 1.0
    context_phase: str = "main"  # setup, main, conclusion

    def __post_init__(self):
        self.relationship_type = RelationshipType.CREATED_IN.value
        self.properties.update(
            {"relevance": self.relevance, "context_phase": self.context_phase}
        )
        super().__post_init__()


@dataclass
class SimilarToEdge(BaseEdge):
    """SIMILAR_TO relationship - Semantic similarity between entities"""

    similarity_score: float = 0.5  # 0.0 to 1.0
    similarity_type: str = "semantic"  # semantic, structural, temporal
    algorithm: str = "embedding"  # embedding, graph, manual

    def __post_init__(self):
        self.relationship_type = RelationshipType.SIMILAR_TO.value
        self.properties.update(
            {
                "similarity_score": self.similarity_score,
                "similarity_type": self.similarity_type,
                "algorithm": self.algorithm,
            }
        )
        super().__post_init__()


# Factory functions for creating edges
def create_created_edge(
    source_id: str,
    target_id: str,
    confidence: float = 1.0,
    timestamp: Optional[str] = None,
    weight: float = 1.0,
) -> CreatedEdge:
    """Factory function to create a CREATED edge"""
    return CreatedEdge(
        id="",  # Will be auto-generated
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.CREATED.value,
        confidence=confidence,
        timestamp=timestamp,
        weight=weight,
    )


def create_linked_to_edge(
    source_id: str,
    target_id: str,
    relevance: str = "medium",
    link_type: str = "semantic",
    weight: float = 1.0,
) -> LinkedToEdge:
    """Factory function to create a LINKED_TO edge"""
    return LinkedToEdge(
        id="",  # Will be auto-generated
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.LINKED_TO.value,
        relevance=relevance,
        link_type=link_type,
        weight=weight,
    )


def create_triggered_by_edge(
    source_id: str,
    target_id: str,
    frequency: str = "manual",
    automation_level: float = 0.0,
    weight: float = 1.0,
) -> TriggeredByEdge:
    """Factory function to create a TRIGGERED_BY edge"""
    return TriggeredByEdge(
        id="",  # Will be auto-generated
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.TRIGGERED_BY.value,
        frequency=frequency,
        automation_level=automation_level,
        weight=weight,
    )


def create_member_of_edge(
    source_id: str,
    target_id: str,
    role: str = "member",
    since: Optional[str] = None,
    permissions: str = "read",
    weight: float = 1.0,
) -> MemberOfEdge:
    """Factory function to create a MEMBER_OF edge"""
    return MemberOfEdge(
        id="",  # Will be auto-generated
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.MEMBER_OF.value,
        role=role,
        since=since,
        permissions=permissions,
        weight=weight,
    )


def create_influences_edge(
    source_id: str,
    target_id: str,
    influence_type: str = "general",
    strength: float = 0.5,
    weight: float = 1.0,
) -> InfluencesEdge:
    """Factory function to create an INFLUENCES edge"""
    return InfluencesEdge(
        id="",  # Will be auto-generated
        source_id=source_id,
        target_id=target_id,
        relationship_type=RelationshipType.INFLUENCES.value,
        influence_type=influence_type,
        strength=strength,
        weight=weight,
    )
