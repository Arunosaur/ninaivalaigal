"""
SPEC-060 Apache AGE Node Models
Python dataclass models for property graph nodes with Redis integration
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class NodeType(Enum):
    """Enumeration of supported node types in the property graph"""
    USER = "User"
    MEMORY = "Memory"
    MACRO = "Macro"
    AGENT = "Agent"
    TOPIC = "Topic"
    SOURCE = "Source"
    CONTEXT = "Context"
    TEAM = "Team"
    ORGANIZATION = "Organization"


class MemoryType(Enum):
    """Types of memory nodes"""
    CORE = "core"
    ARCHITECTURE = "architecture"
    CONVERSATION = "conversation"
    DOCUMENTATION = "documentation"
    CODE = "code"
    INSIGHT = "insight"


class AgentType(Enum):
    """Types of agent nodes"""
    AI_ASSISTANT = "ai_assistant"
    AUTOMATION = "automation"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"


@dataclass
class BaseNode:
    """Base class for all graph nodes"""
    id: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_cypher_properties(self) -> str:
        """Convert node properties to Cypher format"""
        props = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            **self.properties
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


@dataclass
class UserNode:
    """User node in the property graph"""
    id: str
    label: str
    name: str
    email: str
    role: str = "user"
    team_id: Optional[str] = field(default=None)
    organization_id: Optional[str] = field(default=None)
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        self.label = NodeType.USER.value
        self.properties.update({
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "team_id": self.team_id,
            "organization_id": self.organization_id
        })

    def to_cypher_properties(self) -> str:
        """Convert node properties to Cypher format"""
        props = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            **self.properties
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


@dataclass
class MemoryNode:
    """Memory node in the property graph"""
    id: str
    label: str
    title: str
    content: str
    memory_type: MemoryType = MemoryType.CORE
    user_id: Optional[str] = field(default=None)
    context_id: Optional[str] = field(default=None)
    relevance_score: float = 0.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = field(default=None)
    updated_at: Optional[datetime] = field(default=None)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        self.label = NodeType.MEMORY.value
        self.properties.update({
            "title": self.title,
            "content": self.content[:1000],  # Truncate for graph storage
            "type": self.memory_type.value,
            "user_id": self.user_id,
            "context_id": self.context_id,
            "relevance_score": self.relevance_score
        })

    def to_cypher_properties(self) -> str:
        """Convert node properties to Cypher format"""
        props = {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            **self.properties
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


@dataclass
class MacroNode(BaseNode):
    """Macro node in the property graph"""
    name: str
    description: str
    tag: str
    automation_level: float = 0.0
    trigger_frequency: str = "manual"
    user_id: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.MACRO.value
        self.properties.update({
            "name": self.name,
            "description": self.description,
            "tag": self.tag,
            "automation_level": self.automation_level,
            "trigger_frequency": self.trigger_frequency,
            "user_id": self.user_id
        })


@dataclass
class AgentNode(BaseNode):
    """Agent node in the property graph"""
    name: str
    agent_type: AgentType = AgentType.AI_ASSISTANT
    capabilities: str = ""
    version: str = "1.0"
    active: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.AGENT.value
        self.properties.update({
            "name": self.name,
            "type": self.agent_type.value,
            "capabilities": self.capabilities,
            "version": self.version,
            "active": self.active
        })


@dataclass
class TopicNode(BaseNode):
    """Topic node in the property graph"""
    label_name: str  # Renamed to avoid conflict with base label
    category: str
    description: Optional[str] = field(default=None)
    weight: float = 1.0
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.TOPIC.value
        self.properties.update({
            "label": self.label_name,
            "category": self.category,
            "description": self.description,
            "weight": self.weight
        })


@dataclass
class SourceNode(BaseNode):
    """Source node in the property graph"""
    kind: str  # GitHub, Documentation, API, etc.
    ref: str   # Reference identifier
    url: Optional[str] = field(default=None)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.SOURCE.value
        self.properties.update({
            "kind": self.kind,
            "ref": self.ref,
            "url": self.url,
            "metadata": str(self.metadata) if self.metadata else None
        })


@dataclass
class ContextNode(BaseNode):
    """Context node in the property graph"""
    name: str
    context_type: str  # coding, discussion, planning, etc.
    duration: Optional[int] = field(default=None)  # Duration in seconds
    user_count: int = 1
    active: bool = True
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.CONTEXT.value
        self.properties.update({
            "name": self.name,
            "type": self.context_type,
            "duration": self.duration,
            "user_count": self.user_count,
            "active": self.active
        })


@dataclass
class TeamNode(BaseNode):
    """Team node in the property graph"""
    name: str
    description: str
    organization_id: Optional[str] = field(default=None)
    member_count: int = 0
    department: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.TEAM.value
        self.properties.update({
            "name": self.name,
            "description": self.description,
            "organization_id": self.organization_id,
            "member_count": self.member_count,
            "department": self.department
        })


@dataclass
class OrganizationNode(BaseNode):
    """Organization node in the property graph"""
    name: str
    description: str
    domain: Optional[str] = field(default=None)
    size: str = "small"  # small, medium, large, enterprise
    industry: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__post_init__()
        self.label = NodeType.ORGANIZATION.value
        self.properties.update({
            "name": self.name,
            "description": self.description,
            "domain": self.domain,
            "size": self.size,
            "industry": self.industry
        })


# Factory functions for creating nodes
def create_user_node(
    user_id: str,
    name: str,
    email: str,
    role: str = "user",
    team_id: Optional[str] = None,
    organization_id: Optional[str] = None
) -> UserNode:
    """Factory function to create a user node"""
    return UserNode(
        id=user_id,
        label=NodeType.USER.value,
        name=name,
        email=email,
        role=role,
        team_id=team_id,
        organization_id=organization_id
    )


def create_memory_node(
    memory_id: str,
    title: str,
    content: str,
    memory_type: MemoryType = MemoryType.CORE,
    user_id: Optional[str] = None,
    context_id: Optional[str] = None,
    relevance_score: float = 0.0
) -> MemoryNode:
    """Factory function to create a memory node"""
    return MemoryNode(
        id=memory_id,
        label=NodeType.MEMORY.value,
        title=title,
        content=content,
        memory_type=memory_type,
        user_id=user_id,
        context_id=context_id,
        relevance_score=relevance_score
    )


def create_macro_node(
    macro_id: str,
    name: str,
    description: str,
    tag: str,
    automation_level: float = 0.0,
    trigger_frequency: str = "manual",
    user_id: Optional[str] = None
) -> MacroNode:
    """Factory function to create a macro node"""
    return MacroNode(
        id=macro_id,
        label=NodeType.MACRO.value,
        name=name,
        description=description,
        tag=tag,
        automation_level=automation_level,
        trigger_frequency=trigger_frequency,
        user_id=user_id
    )


def create_agent_node(
    agent_id: str,
    name: str,
    agent_type: AgentType = AgentType.AI_ASSISTANT,
    capabilities: str = "",
    version: str = "1.0",
    active: bool = True
) -> AgentNode:
    """Factory function to create an agent node"""
    return AgentNode(
        id=agent_id,
        label=NodeType.AGENT.value,
        name=name,
        agent_type=agent_type,
        capabilities=capabilities,
        version=version,
        active=active
    )
