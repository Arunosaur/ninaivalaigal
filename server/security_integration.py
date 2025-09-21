"""
Security Integration Module

Integrates the security middleware with existing RBAC system and FastAPI application.
"""

import os

from fastapi import FastAPI, Request
from rbac_middleware import RBACContext
from security import RedactionEngine, RedactionMiddleware, SecurityHeadersMiddleware
from security.audit import SecurityEventType, security_alert_manager
from security.middleware import EnhancedRateLimiter
from security.middleware.rate_limiting import RateLimitMiddleware
from security.redaction.config import ContextSensitivity, redaction_config


class SecurityManager:
    """Central security manager for the application"""

    def __init__(self):
        self.redaction_engine = RedactionEngine()
        self.rate_limiter = EnhancedRateLimiter()
        self.enabled = os.getenv('SECURITY_ENABLED', 'true').lower() == 'true'

    def configure_app_security(self, app: FastAPI, development_mode: bool = False):
        """Configure security middleware for FastAPI application"""

        if not self.enabled:
            return

        # Add security headers middleware
        if development_mode:
            from .security.middleware.security_headers import DevelopmentSecurityHeaders
            app.add_middleware(DevelopmentSecurityHeaders)
        else:
            app.add_middleware(SecurityHeadersMiddleware)

        # Add rate limiting middleware
        app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)

        # Add redaction middleware
        app.add_middleware(RedactionMiddleware, enabled=redaction_config.enabled)

        # Add security event handlers
        self._add_security_event_handlers(app)

    def _add_security_event_handlers(self, app: FastAPI):
        """Add security event handlers to the application"""

        @app.middleware("http")
        async def security_event_middleware(request: Request, call_next):
            """Middleware to log security events"""

            try:
                response = await call_next(request)

                # Log failed authentication attempts
                if request.url.path.startswith('/auth/') and response.status_code == 401:
                    await security_alert_manager.log_security_event(
                        SecurityEventType.FAILED_LOGIN,
                        metadata={
                            'endpoint': request.url.path,
                            'ip_address': request.client.host if request.client else 'unknown',
                            'user_agent': request.headers.get('user-agent', 'unknown')
                        }
                    )

                # Log permission denials
                elif response.status_code == 403:
                    rbac_context = getattr(request.state, 'rbac_context', None)
                    user_id = rbac_context.user_id if rbac_context else None

                    await security_alert_manager.log_security_event(
                        SecurityEventType.PERMISSION_DENIED,
                        user_id=user_id,
                        metadata={
                            'endpoint': request.url.path,
                            'method': request.method,
                            'user_role': rbac_context.user_role.value if rbac_context else 'unknown'
                        }
                    )

                return response

            except Exception as e:
                # Log any security-related exceptions
                await security_alert_manager.log_security_event(
                    SecurityEventType.SUSPICIOUS_PATTERN,
                    metadata={
                        'error': str(e),
                        'endpoint': request.url.path,
                        'method': request.method
                    }
                )
                raise

    async def redact_sensitive_data(self,
                                   text: str,
                                   context_tier: ContextSensitivity | None = None,
                                   rbac_context: RBACContext | None = None) -> str:
        """
        Redact sensitive data from text with RBAC context awareness.
        
        Args:
            text: Text to redact
            context_tier: Sensitivity tier (optional)
            rbac_context: RBAC context for user-aware redaction
            
        Returns:
            Redacted text
        """

        if not self.enabled or not redaction_config.enabled:
            return text

        # Determine sensitivity tier based on RBAC context if not provided
        if not context_tier and rbac_context:
            context_tier = self._determine_tier_from_rbac(rbac_context)

        # Use default tier if still not determined
        tier = context_tier or redaction_config.default_tier

        # Apply redaction
        result = self.redaction_engine.redact(text, tier)

        # Log redaction event if any secrets were found
        if result.total_secrets_found > 0:
            await security_alert_manager.log_security_event(
                SecurityEventType.HIGH_ENTROPY_DETECTION,
                user_id=rbac_context.user_id if rbac_context else None,
                metadata={
                    'secrets_found': result.total_secrets_found,
                    'sensitivity_tier': tier.value,
                    'entropy_score': result.entropy_score
                }
            )

        return result.redacted_text

    def _determine_tier_from_rbac(self, rbac_context: RBACContext) -> ContextSensitivity:
        """Determine sensitivity tier based on RBAC context"""

        from .rbac.permissions import Role

        # Map user roles to sensitivity tiers
        role_tier_mapping = {
            Role.SYSTEM: ContextSensitivity.RESTRICTED,
            Role.OWNER: ContextSensitivity.CONFIDENTIAL,
            Role.ADMIN: ContextSensitivity.CONFIDENTIAL,
            Role.MAINTAINER: ContextSensitivity.INTERNAL,
            Role.MEMBER: ContextSensitivity.INTERNAL,
            Role.VIEWER: ContextSensitivity.PUBLIC
        }

        return role_tier_mapping.get(rbac_context.user_role, ContextSensitivity.INTERNAL)

    async def check_cross_org_access(self,
                                    rbac_context: RBACContext,
                                    target_org_id: int) -> bool:
        """
        Check for cross-organization access attempts and log security events.
        
        Args:
            rbac_context: User's RBAC context
            target_org_id: Organization being accessed
            
        Returns:
            True if access is allowed, False otherwise
        """

        user_org_id = rbac_context.organization_id

        # Allow system users to access any organization
        from .rbac.permissions import Role
        if rbac_context.user_role == Role.SYSTEM:
            return True

        # Check if user is trying to access different organization
        if user_org_id and user_org_id != target_org_id:
            # Log cross-org access attempt
            await security_alert_manager.log_security_event(
                SecurityEventType.CROSS_ORG_ATTEMPT,
                user_id=rbac_context.user_id,
                metadata={
                    'user_org_id': user_org_id,
                    'target_org_id': target_org_id,
                    'user_role': rbac_context.user_role.value
                }
            )
            return False

        return True

    async def log_admin_action(self,
                              rbac_context: RBACContext,
                              action: str,
                              target_resource: str,
                              metadata: dict | None = None):
        """Log administrative actions for audit purposes"""

        await security_alert_manager.log_security_event(
            SecurityEventType.ADMIN_ACTION,
            user_id=rbac_context.user_id,
            metadata={
                'action': action,
                'target_resource': target_resource,
                'user_role': rbac_context.user_role.value,
                'organization_id': rbac_context.organization_id,
                **(metadata or {})
            }
        )

    def get_security_status(self) -> dict:
        """Get current security system status"""

        return {
            'security_enabled': self.enabled,
            'redaction_enabled': redaction_config.enabled,
            'rate_limiting_enabled': True,
            'security_headers_enabled': True,
            'audit_logging_enabled': redaction_config.audit_enabled,
            'active_alerts': len(security_alert_manager.get_active_alerts()),
            'critical_alerts': len(security_alert_manager.get_active_alerts()),
            'recent_events': len(security_alert_manager.recent_events)
        }


# Global security manager instance
security_manager = SecurityManager()


# Utility functions for easy integration
async def redact_text(text: str,
                     sensitivity_tier: ContextSensitivity | None = None,
                     rbac_context: RBACContext | None = None) -> str:
    """Convenience function for text redaction"""
    return await security_manager.redact_sensitive_data(text, sensitivity_tier, rbac_context)


async def check_cross_org_access(rbac_context: RBACContext, target_org_id: int) -> bool:
    """Convenience function for cross-org access checks"""
    return await security_manager.check_cross_org_access(rbac_context, target_org_id)


async def log_admin_action(rbac_context: RBACContext, action: str,
                          target_resource: str, metadata: dict | None = None):
    """Convenience function for logging admin actions"""
    await security_manager.log_admin_action(rbac_context, action, target_resource, metadata)


def configure_security(app: FastAPI, development_mode: bool = False):
    """Configure security for FastAPI application"""
    security_manager.configure_app_security(app, development_mode)
