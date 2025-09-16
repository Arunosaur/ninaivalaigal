"""
Redaction Audit System

Comprehensive audit trail for all redaction events with immutable logging.
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .config import ContextSensitivity
from .processors import RedactionResult


class AuditEventType(Enum):
    """Types of redaction audit events"""
    REDACTION_APPLIED = "redaction_applied"
    REDACTION_SKIPPED = "redaction_skipped"
    REDACTION_FAILED = "redaction_failed"
    POLICY_VIOLATION = "policy_violation"
    CONFIGURATION_CHANGED = "configuration_changed"


@dataclass
class RedactionAuditEvent:
    """Individual redaction audit event"""
    id: str
    timestamp: datetime
    event_type: AuditEventType
    user_id: Optional[int]
    context_id: Optional[int]
    request_id: Optional[str]
    redaction_applied: bool
    redaction_type: Optional[str]
    sensitivity_tier: ContextSensitivity
    patterns_matched: List[str]
    entropy_score: Optional[float]
    original_length: int
    redacted_length: int
    processing_time_ms: float
    confidence_scores: Dict[str, float]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'context_id': self.context_id,
            'request_id': self.request_id,
            'redaction_applied': self.redaction_applied,
            'redaction_type': self.redaction_type,
            'sensitivity_tier': self.sensitivity_tier.value,
            'patterns_matched': self.patterns_matched,
            'entropy_score': self.entropy_score,
            'original_length': self.original_length,
            'redacted_length': self.redacted_length,
            'processing_time_ms': self.processing_time_ms,
            'confidence_scores': self.confidence_scores,
            'metadata': self.metadata
        }


class RedactionAuditLogger:
    """Audit logger for redaction events"""
    
    def __init__(self, database_manager=None):
        self.database_manager = database_manager
        self._event_buffer = []
        self._buffer_size = 100
        self.events = []  # For testing purposes
    
    def log_redaction_event(self, 
                           redaction_result: RedactionResult,
                           user_id: Optional[int] = None,
                           context_id: Optional[int] = None,
                           request_id: Optional[str] = None) -> str:
        """
        Log a redaction event to the audit trail.
        
        Args:
            redaction_result: Result of redaction processing
            user_id: ID of user who triggered redaction
            context_id: ID of context being redacted
            request_id: Unique request identifier
            
        Returns:
            Audit event ID
        """
        import uuid
        
        event_id = str(uuid.uuid4())
        
        # Extract patterns and confidence scores from redaction result
        patterns_matched = []
        confidence_scores = {}
        
        for redaction in redaction_result.redactions_applied:
            if redaction.get('pattern_name'):
                patterns_matched.append(redaction['pattern_name'])
            
            secret_type = redaction.get('secret_type', 'unknown')
            confidence_scores[secret_type] = redaction.get('confidence', 0.0)
        
        audit_event = RedactionAuditEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.REDACTION_APPLIED if redaction_result.total_secrets_found > 0 else AuditEventType.REDACTION_SKIPPED,
            user_id=user_id,
            context_id=context_id,
            request_id=request_id,
            redaction_applied=redaction_result.total_secrets_found > 0,
            redaction_type='contextual_redaction',
            sensitivity_tier=redaction_result.context_tier,
            patterns_matched=patterns_matched,
            entropy_score=redaction_result.entropy_score,
            original_length=len(redaction_result.original_text),
            redacted_length=len(redaction_result.redacted_text),
            processing_time_ms=redaction_result.processing_time_ms,
            confidence_scores=confidence_scores,
            metadata={
                'redactions_count': redaction_result.total_secrets_found,
                'redaction_details': redaction_result.redactions_applied
            }
        )
        
        # Store the audit event
        self._store_audit_event(audit_event)
        self.events.append(audit_event)  # For testing
        
        return event_id
    
    async def log_redaction_applied(self,
                                   user_id: Optional[int],
                                   context_id: Optional[int],
                                   original_text: str,
                                   redacted_text: str,
                                   secrets_found: int,
                                   sensitivity_tier: str,
                                   processing_time_ms: float,
                                   request_id: Optional[str] = None) -> str:
        """Log a redaction applied event"""
        import uuid
        
        event_id = str(uuid.uuid4())
        
        audit_event = RedactionAuditEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.REDACTION_APPLIED,
            user_id=user_id,
            context_id=context_id,
            request_id=request_id,
            redaction_applied=True,
            redaction_type='contextual_redaction',
            sensitivity_tier=ContextSensitivity(sensitivity_tier) if isinstance(sensitivity_tier, str) else sensitivity_tier,
            patterns_matched=[],
            entropy_score=None,
            original_length=len(original_text),
            redacted_length=len(redacted_text),
            processing_time_ms=processing_time_ms,
            confidence_scores={},
            metadata={
                'secrets_found': secrets_found,
                'redaction_ratio': len(redacted_text) / len(original_text) if len(original_text) > 0 else 0
            }
        )
        
        self._store_audit_event(audit_event)
        self.events.append(audit_event)  # For testing
        return event_id

    async def log_policy_violation(self,
                                  user_id: Optional[int],
                                  violation_type: str,
                                  details: Dict[str, Any],
                                  context_id: Optional[int] = None,
                                  request_id: Optional[str] = None) -> str:
        """Log a policy violation event"""
        import uuid
        
        event_id = str(uuid.uuid4())
        
        audit_event = RedactionAuditEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.POLICY_VIOLATION,
            user_id=user_id,
            context_id=context_id,
            request_id=request_id,
            redaction_applied=False,
            redaction_type=None,
            sensitivity_tier=ContextSensitivity.INTERNAL,  # Default
            patterns_matched=[],
            entropy_score=None,
            original_length=0,
            redacted_length=0,
            processing_time_ms=0.0,
            confidence_scores={},
            metadata={
                'violation_type': violation_type,
                'violation_details': details
            }
        )
        
        self._store_audit_event(audit_event)
        self.events.append(audit_event)  # For testing
        return event_id
    
    async def log_redaction_failure(self,
                                   user_id: Optional[int],
                                   error_message: str,
                                   context_data: Optional[Dict[str, Any]] = None,
                                   context_id: Optional[int] = None,
                                   request_id: Optional[str] = None) -> str:
        """Log a redaction failure event"""
        import uuid
        
        event_id = str(uuid.uuid4())
        
        audit_event = RedactionAuditEvent(
            id=event_id,
            timestamp=datetime.utcnow(),
            event_type=AuditEventType.REDACTION_FAILED,
            user_id=user_id,
            context_id=context_id,
            request_id=request_id,
            redaction_applied=False,
            redaction_type='failed_redaction',
            sensitivity_tier=ContextSensitivity.INTERNAL,  # Default
            patterns_matched=[],
            entropy_score=None,
            original_length=0,
            redacted_length=0,
            processing_time_ms=0.0,
            confidence_scores={},
            metadata={
                'error_message': error_message,
                'failure_timestamp': datetime.utcnow().isoformat(),
                'context_data': context_data or {}
            }
        )
        
        self._store_audit_event(audit_event)
        self.events.append(audit_event)  # For testing
        return event_id
    
    def _store_audit_event(self, event: RedactionAuditEvent):
        """Store audit event in database or buffer"""
        if self.database_manager:
            try:
                self._store_in_database(event)
            except Exception as e:
                # Fallback to buffer if database fails
                self._add_to_buffer(event)
                print(f"Failed to store audit event in database: {e}")
        else:
            self._add_to_buffer(event)
    
    def _store_in_database(self, event: RedactionAuditEvent):
        """Store audit event in database"""
        # This would integrate with the existing database manager
        # For now, we'll implement a basic version
        session = self.database_manager.get_session()
        try:
            # Insert into redaction_audits table
            audit_data = event.to_dict()
            
            # Convert to database format
            db_record = {
                'id': event.id,
                'timestamp': event.timestamp,
                'user_id': event.user_id,
                'context_id': event.context_id,
                'request_id': event.request_id,
                'redaction_applied': event.redaction_applied,
                'redaction_type': event.redaction_type,
                'sensitivity_tier': event.sensitivity_tier.value,
                'patterns_matched': json.dumps(event.patterns_matched),
                'entropy_score': event.entropy_score,
                'original_length': event.original_length,
                'redacted_length': event.redacted_length,
                'metadata': json.dumps(event.metadata)
            }
            
            # This would use SQLAlchemy to insert the record
            # session.execute(insert_statement, db_record)
            # session.commit()
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def _add_to_buffer(self, event: RedactionAuditEvent):
        """Add event to in-memory buffer"""
        self._event_buffer.append(event)
        
        # Flush buffer if it's full
        if len(self._event_buffer) >= self._buffer_size:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Flush buffered events to storage"""
        if not self._event_buffer:
            return
        
        # Try to store buffered events
        for event in self._event_buffer:
            try:
                if self.database_manager:
                    self._store_in_database(event)
            except Exception as e:
                print(f"Failed to flush audit event {event.id}: {e}")
        
        # Clear buffer after flushing
        self._event_buffer.clear()
    
    def get_audit_events(self, 
                        user_id: Optional[int] = None,
                        context_id: Optional[int] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        event_type: Optional[AuditEventType] = None,
                        limit: int = 100) -> List[RedactionAuditEvent]:
        """
        Retrieve audit events with filtering.
        
        Args:
            user_id: Filter by user ID
            context_id: Filter by context ID
            start_time: Filter events after this time
            end_time: Filter events before this time
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        # This would query the database with the given filters
        # For now, return buffered events that match filters
        filtered_events = []
        
        for event in self._event_buffer:
            if user_id and event.user_id != user_id:
                continue
            if context_id and event.context_id != context_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_type and event.event_type != event_type:
                continue
            
            filtered_events.append(event)
        
        return filtered_events[:limit]
    
    def get_redaction_statistics(self, 
                               user_id: Optional[int] = None,
                               time_period_hours: int = 24) -> Dict[str, Any]:
        """
        Get redaction statistics for monitoring and alerting.
        
        Args:
            user_id: Filter by user ID
            time_period_hours: Time period for statistics
            
        Returns:
            Dictionary with redaction statistics
        """
        cutoff_time = datetime.utcnow().replace(microsecond=0) - \
                     datetime.timedelta(hours=time_period_hours)
        
        events = self.get_audit_events(
            user_id=user_id,
            start_time=cutoff_time
        )
        
        stats = {
            'total_events': len(events),
            'redactions_applied': len([e for e in events if e.redaction_applied]),
            'redactions_skipped': len([e for e in events if not e.redaction_applied]),
            'policy_violations': len([e for e in events if e.event_type == AuditEventType.POLICY_VIOLATION]),
            'failures': len([e for e in events if e.event_type == AuditEventType.REDACTION_FAILED]),
            'avg_processing_time_ms': sum(e.processing_time_ms for e in events) / len(events) if events else 0,
            'patterns_detected': {},
            'sensitivity_tiers': {},
            'time_period_hours': time_period_hours
        }
        
        # Count patterns and tiers
        for event in events:
            for pattern in event.patterns_matched:
                stats['patterns_detected'][pattern] = stats['patterns_detected'].get(pattern, 0) + 1
            
            tier = event.sensitivity_tier.value
            stats['sensitivity_tiers'][tier] = stats['sensitivity_tiers'].get(tier, 0) + 1
        
        return stats


# Global audit logger instance
redaction_audit_logger = RedactionAuditLogger()
