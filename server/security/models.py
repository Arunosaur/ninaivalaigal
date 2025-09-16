"""
Database models for security and redaction audit system
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
import uuid
from datetime import datetime

from ..database import Base


class RedactionAudit(Base):
    """Audit trail for redaction operations"""
    __tablename__ = "redaction_audits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    request_id = Column(String(255), nullable=True)
    redaction_applied = Column(Boolean, nullable=False)
    redaction_type = Column(String(100), nullable=True)
    sensitivity_tier = Column(String(50), nullable=True)
    patterns_matched = Column(JSONB, nullable=True)
    entropy_score = Column(Float, nullable=True)
    original_length = Column(Integer, nullable=True)
    redacted_length = Column(Integer, nullable=True)
    processing_time_ms = Column(Float, nullable=True)
    confidence_scores = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    context = relationship("Context", foreign_keys=[context_id])


class AlertEvent(Base):
    """Security alert events"""
    __tablename__ = "alert_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(String(20), nullable=False)
    event_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    metadata = Column(JSONB, nullable=True)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    context = relationship("Context", foreign_keys=[context_id])
    resolver = relationship("User", foreign_keys=[resolved_by])


class SecurityEvent(Base):
    """Detailed security event tracking"""
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    context_id = Column(Integer, ForeignKey("contexts.id"), nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    context = relationship("Context", foreign_keys=[context_id])


# Add security-related fields to existing models via mixins
class SecurityMixin:
    """Mixin to add security fields to existing models"""
    sensitivity_tier = Column(String(50), default='internal')
    redaction_applied = Column(Boolean, default=False)
    original_entropy_score = Column(Float, nullable=True)
    redaction_audit_id = Column(UUID(as_uuid=True), ForeignKey("redaction_audits.id"), nullable=True)


class ContextSecurityMixin:
    """Security mixin for context models"""
    sensitivity_tier = Column(String(50), default='internal')
    auto_classified = Column(Boolean, default=False)
    classification_confidence = Column(Float, nullable=True)
    last_sensitivity_review = Column(DateTime(timezone=True), nullable=True)
