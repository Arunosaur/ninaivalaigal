"""
Security Audit and Alert Management

Centralized security event monitoring and alerting system.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .redaction.audit import redaction_audit_logger


class SecurityEventType(Enum):
    """Types of security events"""
    FAILED_LOGIN = "failed_login"
    PERMISSION_DENIED = "permission_denied"
    HIGH_ENTROPY_DETECTION = "high_entropy_detection"
    CROSS_ORG_ATTEMPT = "cross_org_attempt"
    ADMIN_ACTION = "admin_action"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    POLICY_VIOLATION = "policy_violation"


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityAlert:
    """Security alert data structure"""
    id: str
    timestamp: datetime
    severity: AlertSeverity
    event_type: SecurityEventType
    title: str
    message: str
    user_id: Optional[int]
    context_id: Optional[int]
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SecurityAlertManager:
    """Manage security-related alerts and notifications"""
    
    def __init__(self):
        self.recent_events = []  # Store recent security events
        self.alert_thresholds = {
            'failed_logins_per_minute': 10,
            'permission_denials_per_minute': 50,
            'high_entropy_detections_per_hour': 100,
            'cross_org_attempts_per_hour': 5,
            'admin_actions_per_hour': 20,
            'rate_limit_violations_per_hour': 100
        }
    
    def _start_monitoring(self):
        """Start background monitoring task"""
        async def monitor():
            while True:
                await asyncio.sleep(60)  # Check every minute
                await self.check_security_thresholds()
        
        self._monitoring_task = asyncio.create_task(monitor())
    
    async def log_security_event(self, 
                                event_type: SecurityEventType,
                                user_id: Optional[int] = None,
                                context_id: Optional[int] = None,
                                metadata: Optional[Dict[str, Any]] = None):
        """Log a security event for monitoring"""
        
        event = {
            'timestamp': datetime.utcnow(),
            'event_type': event_type,
            'user_id': user_id,
            'context_id': context_id,
            'metadata': metadata or {}
        }
        
        self.recent_events.append(event)
        
        # Keep only recent events (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.recent_events = [
            e for e in self.recent_events 
            if e['timestamp'] > cutoff_time
        ]
        
        # Check for immediate alerts
        await self._check_immediate_alerts(event)
    
    async def _check_immediate_alerts(self, event: Dict[str, Any]):
        """Check for alerts that should trigger immediately"""
        
        event_type = event['event_type']
        user_id = event.get('user_id')
        
        # Critical events that trigger immediate alerts
        if event_type == SecurityEventType.CROSS_ORG_ATTEMPT:
            await self._send_alert(
                severity=AlertSeverity.CRITICAL,
                event_type=event_type,
                title='Cross-Organization Access Attempt',
                message=f'User {user_id} attempted cross-org access',
                user_id=user_id,
                metadata=event.get('metadata', {})
            )
        
        elif event_type == SecurityEventType.ADMIN_ACTION:
            # Log admin actions for audit
            await self._send_alert(
                severity=AlertSeverity.MEDIUM,
                event_type=event_type,
                title='Admin Action Performed',
                message=f'Admin action by user {user_id}',
                user_id=user_id,
                metadata=event.get('metadata', {})
            )
    
    async def check_security_thresholds(self):
        """Check security metrics against thresholds"""
        current_time = datetime.utcnow()
        
        # Check failed login attempts (last minute)
        failed_logins = self._count_events_in_window(
            SecurityEventType.FAILED_LOGIN, 
            minutes=1
        )
        
        if failed_logins > self.alert_thresholds['failed_logins_per_minute']:
            await self._send_alert(
                severity=AlertSeverity.HIGH,
                event_type=SecurityEventType.FAILED_LOGIN,
                title='High Failed Login Rate',
                message=f'{failed_logins} failed logins in the last minute',
                metadata={'failed_logins': failed_logins}
            )
        
        # Check permission denials (last minute)
        permission_denials = self._count_events_in_window(
            SecurityEventType.PERMISSION_DENIED,
            minutes=1
        )
        
        if permission_denials > self.alert_thresholds['permission_denials_per_minute']:
            await self._send_alert(
                severity=AlertSeverity.MEDIUM,
                event_type=SecurityEventType.PERMISSION_DENIED,
                title='High Permission Denial Rate',
                message=f'{permission_denials} permission denials in the last minute',
                metadata={'permission_denials': permission_denials}
            )
        
        # Check cross-org access attempts (last hour)
        cross_org_attempts = self._count_events_in_window(
            SecurityEventType.CROSS_ORG_ATTEMPT,
            hours=1
        )
        
        if cross_org_attempts > self.alert_thresholds['cross_org_attempts_per_hour']:
            await self._send_alert(
                severity=AlertSeverity.CRITICAL,
                event_type=SecurityEventType.CROSS_ORG_ATTEMPT,
                title='Multiple Cross-Organization Access Attempts',
                message=f'{cross_org_attempts} cross-org access attempts in the last hour',
                metadata={'cross_org_attempts': cross_org_attempts}
            )
        
        # Check high entropy detections (last hour)
        entropy_detections = self._count_events_in_window(
            SecurityEventType.HIGH_ENTROPY_DETECTION,
            hours=1
        )
        
        if entropy_detections > self.alert_thresholds['high_entropy_detections_per_hour']:
            await self._send_alert(
                severity=AlertSeverity.MEDIUM,
                event_type=SecurityEventType.HIGH_ENTROPY_DETECTION,
                title='High Number of Secret Detections',
                message=f'{entropy_detections} high-entropy secrets detected in the last hour',
                metadata={'entropy_detections': entropy_detections}
            )
    
    def _count_events_in_window(self, event_type: SecurityEventType, 
                               minutes: int = 0, hours: int = 0) -> int:
        """Count events of a specific type within a time window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes, hours=hours)
        
        return len([
            event for event in self.recent_events
            if (event['event_type'] == event_type and 
                event['timestamp'] > cutoff_time)
        ])
    
    async def _send_alert(self, 
                         severity: AlertSeverity,
                         event_type: SecurityEventType,
                         title: str,
                         message: str,
                         user_id: Optional[int] = None,
                         context_id: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """Send security alert"""
        
        import uuid
        
        alert = SecurityAlert(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            severity=severity,
            event_type=event_type,
            title=title,
            message=message,
            user_id=user_id,
            context_id=context_id,
            metadata=metadata or {}
        )
        
        self.active_alerts.append(alert)
        
        # Log the alert
        print(f"SECURITY ALERT [{severity.value.upper()}]: {title} - {message}")
        
        # In production, this would send notifications via:
        # - Slack webhook
        # - Email
        # - PagerDuty
        # - SMS
        
        # Store in database for audit trail
        await self._store_alert(alert)
    
    async def _store_alert(self, alert: SecurityAlert):
        """Store alert in database (placeholder)"""
        # This would integrate with the database manager
        alert_data = {
            'id': alert.id,
            'timestamp': alert.timestamp.isoformat(),
            'severity': alert.severity.value,
            'event_type': alert.event_type.value,
            'title': alert.title,
            'message': alert.message,
            'user_id': alert.user_id,
            'context_id': alert.context_id,
            'metadata': json.dumps(alert.metadata),
            'resolved': alert.resolved
        }
        
        # Would insert into alert_events table
        pass
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[SecurityAlert]:
        """Get active (unresolved) alerts"""
        alerts = [alert for alert in self.active_alerts if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    async def resolve_alert(self, alert_id: str, resolved_by: Optional[int] = None):
        """Mark an alert as resolved"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                
                # Update in database
                await self._store_alert(alert)
                break
    
    def get_security_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get security statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.recent_events
            if event['timestamp'] > cutoff_time
        ]
        
        stats = {
            'total_events': len(recent_events),
            'events_by_type': {},
            'events_by_hour': {},
            'unique_users_involved': len(set(
                event.get('user_id') for event in recent_events 
                if event.get('user_id')
            )),
            'active_alerts': len(self.get_active_alerts()),
            'critical_alerts': len(self.get_active_alerts(AlertSeverity.CRITICAL)),
            'time_period_hours': hours
        }
        
        # Count events by type
        for event in recent_events:
            event_type = event['event_type'].value
            stats['events_by_type'][event_type] = stats['events_by_type'].get(event_type, 0) + 1
        
        # Count events by hour
        for event in recent_events:
            hour_key = event['timestamp'].strftime('%Y-%m-%d %H:00')
            stats['events_by_hour'][hour_key] = stats['events_by_hour'].get(hour_key, 0) + 1
        
        return stats


# Global security alert manager instance - create without auto-monitoring
security_alert_manager = SecurityAlertManager()
# Disable auto-monitoring to avoid event loop issues during import
security_alert_manager._monitoring_task = None
