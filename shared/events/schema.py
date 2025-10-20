# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""
Event Schema Definitions
SPEC-100: Event-Driven Architecture
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EventMetadata(BaseModel):
    """Standard metadata for all events"""

    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    correlation_id: UUID = Field(default_factory=uuid4)
    causation_id: Optional[UUID] = None  # ID of event that caused this event


class Event(BaseModel):
    """
    Standard event structure for all events in the system.

    This provides a consistent format for event-driven communication
    across all microservices.
    """

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"
    source_service: str
    payload: Dict[str, Any]
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    class Config:
        """Pydantic configuration for Event model"""

        json_encoders = {datetime: lambda v: v.isoformat(), UUID: lambda v: str(v)}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for Redis storage"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "source_service": self.source_service,
            "payload": self.payload,
            "metadata": {
                "user_id": str(self.metadata.user_id) if self.metadata.user_id else None,
                "organization_id": str(self.metadata.organization_id) if self.metadata.organization_id else None,
                "team_id": str(self.metadata.team_id) if self.metadata.team_id else None,
                "correlation_id": str(self.metadata.correlation_id),
                "causation_id": str(self.metadata.causation_id) if self.metadata.causation_id else None,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary (Redis retrieval)"""
        metadata_dict = data.get("metadata", {})

        # Convert string UUIDs back to UUID objects
        if metadata_dict.get("user_id"):
            metadata_dict["user_id"] = UUID(metadata_dict["user_id"])
        if metadata_dict.get("organization_id"):
            metadata_dict["organization_id"] = UUID(metadata_dict["organization_id"])
        if metadata_dict.get("team_id"):
            metadata_dict["team_id"] = UUID(metadata_dict["team_id"])
        if metadata_dict.get("correlation_id"):
            metadata_dict["correlation_id"] = UUID(metadata_dict["correlation_id"])
        if metadata_dict.get("causation_id"):
            metadata_dict["causation_id"] = UUID(metadata_dict["causation_id"])

        return cls(
            event_id=UUID(data["event_id"]),
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version=data["version"],
            source_service=data["source_service"],
            payload=data["payload"],
            metadata=EventMetadata(**metadata_dict),
        )


# Specific event payloads


class UserCreatedPayload(BaseModel):
    """Payload for user.created event"""

    user_id: UUID
    email: str
    name: str
    created_at: datetime


class MemoryCreatedPayload(BaseModel):
    """Payload for memory.created event"""

    memory_id: UUID
    user_id: UUID
    content: str
    context_id: Optional[UUID] = None
    created_at: datetime


class SubscriptionCreatedPayload(BaseModel):
    """Payload for subscription.created event"""

    subscription_id: UUID
    organization_id: UUID
    plan_id: str
    status: str
    created_at: datetime
