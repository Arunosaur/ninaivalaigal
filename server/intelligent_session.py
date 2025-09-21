"""
Intelligent Session Management - SPEC-045 Implementation
Redis-backed adaptive session management with behavioral intelligence
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any

import structlog
from redis_client import RedisClient, get_redis_client
from relevance_engine import RelevanceEngine, get_relevance_engine

logger = structlog.get_logger(__name__)

class SessionConfig:
    """Configuration for intelligent session management"""

    def __init__(self):
        self.base_timeout_minutes = int(os.getenv('SESSION_BASE_TIMEOUT', '30'))
        self.max_timeout_minutes = int(os.getenv('SESSION_MAX_TIMEOUT', '480'))  # 8 hours
        self.min_timeout_minutes = int(os.getenv('SESSION_MIN_TIMEOUT', '5'))   # 5 minutes
        self.renewal_threshold = float(os.getenv('SESSION_RENEWAL_THRESHOLD', '0.8'))  # 80% of timeout

        # Intelligence multipliers
        self.multipliers = {
            'activity_high': 1.5,      # Very active users
            'activity_medium': 1.0,    # Normal activity
            'activity_low': 0.7,       # Low activity users
            'role_admin': 2.0,         # Admin users
            'role_premium': 1.5,       # Premium users
            'role_regular': 1.0,       # Regular users
            'context_important': 1.3,  # Working with important memories
            'context_normal': 1.0,     # Normal context
            'security_high_risk': 0.6, # High risk activities
            'security_normal': 1.0,    # Normal security level
            'security_trusted': 1.2    # Trusted environment
        }

class IntelligentSessionManager:
    """Redis-backed intelligent session management system"""

    def __init__(self, redis_client: RedisClient, relevance_engine: RelevanceEngine):
        self.redis = redis_client
        self.relevance = relevance_engine
        self.config = SessionConfig()

    def _make_session_key(self, session_id: str) -> str:
        """Generate Redis key for session data"""
        return f"session:{session_id}"

    def _make_session_meta_key(self, session_id: str) -> str:
        """Generate Redis key for session metadata"""
        return f"session:meta:{session_id}"

    def _make_activity_key(self, session_id: str) -> str:
        """Generate Redis key for activity tracking"""
        return f"session:activity:{session_id}"

    def _make_user_session_key(self, user_id: str) -> str:
        """Generate Redis key for user session history"""
        return f"session:user:{user_id}"

    def _make_renewal_key(self, session_id: str) -> str:
        """Generate Redis key for renewal recommendations"""
        return f"session:renewal:{session_id}"

    async def calculate_intelligent_timeout(self,
                                          user_id: str,
                                          session_data: dict[str, Any]) -> int:
        """Calculate intelligent session timeout based on user behavior"""
        try:
            base_timeout = self.config.base_timeout_minutes * 60  # Convert to seconds

            # Get user activity level
            activity_level = await self._get_user_activity_level(user_id)
            activity_multiplier = self.config.multipliers.get(f'activity_{activity_level}', 1.0)

            # Get user role
            user_role = session_data.get('user_role', 'regular')
            role_multiplier = self.config.multipliers.get(f'role_{user_role}', 1.0)

            # Get context importance (integration with SPEC-031)
            context_level = await self._get_context_importance(user_id)
            context_multiplier = self.config.multipliers.get(f'context_{context_level}', 1.0)

            # Get security risk level
            security_level = await self._get_security_risk_level(user_id, session_data)
            security_multiplier = self.config.multipliers.get(f'security_{security_level}', 1.0)

            # Calculate intelligent timeout
            intelligent_timeout = base_timeout * (
                activity_multiplier *
                role_multiplier *
                context_multiplier *
                security_multiplier
            )

            # Apply bounds
            max_timeout = self.config.max_timeout_minutes * 60
            min_timeout = self.config.min_timeout_minutes * 60
            intelligent_timeout = max(min_timeout, min(max_timeout, intelligent_timeout))

            logger.debug("Intelligent timeout calculated",
                        user_id=user_id,
                        base_timeout=base_timeout,
                        activity_multiplier=activity_multiplier,
                        role_multiplier=role_multiplier,
                        context_multiplier=context_multiplier,
                        security_multiplier=security_multiplier,
                        final_timeout=intelligent_timeout)

            return int(intelligent_timeout)

        except Exception as e:
            logger.error("Error calculating intelligent timeout", user_id=user_id, error=str(e))
            return self.config.base_timeout_minutes * 60  # Fallback to base timeout

    async def _get_user_activity_level(self, user_id: str) -> str:
        """Determine user activity level based on recent behavior"""
        try:
            if not self.redis.is_connected:
                return 'medium'

            # Get user session history
            user_key = self._make_user_session_key(user_id)
            user_data = await self.redis.redis.get(user_key)

            if not user_data:
                return 'medium'  # Default for new users

            data = json.loads(user_data)
            recent_sessions = data.get('recent_sessions', [])

            if not recent_sessions:
                return 'medium'

            # Calculate activity score based on recent sessions
            now = datetime.utcnow()
            activity_score = 0

            for session in recent_sessions[-10:]:  # Last 10 sessions
                session_time = datetime.fromisoformat(session.get('created_at', now.isoformat()))
                hours_ago = (now - session_time).total_seconds() / 3600

                if hours_ago < 24:  # Last 24 hours
                    activity_score += session.get('activity_count', 0) / (hours_ago + 1)

            # Classify activity level
            if activity_score > 50:
                return 'high'
            elif activity_score > 20:
                return 'medium'
            else:
                return 'low'

        except Exception as e:
            logger.error("Error getting user activity level", user_id=user_id, error=str(e))
            return 'medium'

    async def _get_context_importance(self, user_id: str) -> str:
        """Determine context importance using SPEC-031 relevance data"""
        try:
            if not self.relevance:
                return 'normal'

            # Get user's recent relevant memories
            relevant_memories = await self.relevance.get_top_memories(user_id, limit=10)

            if not relevant_memories:
                return 'normal'

            # Calculate average relevance score
            total_score = sum(score for _, score in relevant_memories)
            avg_score = total_score / len(relevant_memories)

            # High average relevance indicates important context
            if avg_score > 0.8:
                return 'important'
            else:
                return 'normal'

        except Exception as e:
            logger.error("Error getting context importance", user_id=user_id, error=str(e))
            return 'normal'

    async def _get_security_risk_level(self, user_id: str, session_data: dict[str, Any]) -> str:
        """Assess security risk level for the session"""
        try:
            risk_factors = 0

            # Check for suspicious patterns
            user_agent = session_data.get('user_agent', '')
            ip_address = session_data.get('ip_address', '')

            # Simple risk assessment (can be enhanced)
            if not user_agent or 'bot' in user_agent.lower():
                risk_factors += 1

            if not ip_address or ip_address.startswith('10.') or ip_address.startswith('192.168.'):
                # Internal/private IP might be more trusted
                risk_factors -= 1

            # Check session creation time (late night sessions might be riskier)
            created_at = session_data.get('created_at')
            if created_at:
                session_time = datetime.fromisoformat(created_at)
                hour = session_time.hour
                if hour < 6 or hour > 22:  # Late night/early morning
                    risk_factors += 0.5

            # Classify risk level
            if risk_factors >= 2:
                return 'high_risk'
            elif risk_factors <= -1:
                return 'trusted'
            else:
                return 'normal'

        except Exception as e:
            logger.error("Error assessing security risk", user_id=user_id, error=str(e))
            return 'normal'

    async def create_intelligent_session(self,
                                       user_id: str,
                                       session_id: str,
                                       session_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new intelligent session with Redis backing"""
        try:
            if not self.redis.is_connected:
                raise Exception("Redis not connected")

            # Calculate intelligent timeout
            timeout_seconds = await self.calculate_intelligent_timeout(user_id, session_data)

            # Prepare session data
            enhanced_session_data = {
                **session_data,
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'timeout_seconds': timeout_seconds,
                'activity_count': 0,
                'intelligent_features': {
                    'adaptive_timeout': True,
                    'activity_tracking': True,
                    'context_awareness': True,
                    'security_monitoring': True
                }
            }

            # Store session in Redis
            session_key = self._make_session_key(session_id)
            await self.redis.redis.setex(session_key, timeout_seconds, json.dumps(enhanced_session_data))

            # Create session metadata
            meta_data = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': enhanced_session_data['created_at'],
                'original_timeout': timeout_seconds,
                'intelligence_applied': True,
                'features_enabled': list(enhanced_session_data['intelligent_features'].keys())
            }

            meta_key = self._make_session_meta_key(session_id)
            await self.redis.redis.setex(meta_key, timeout_seconds + 3600, json.dumps(meta_data))  # Meta lasts 1h longer

            # Initialize activity tracking
            activity_key = self._make_activity_key(session_id)
            activity_data = {
                'session_id': session_id,
                'activities': [],
                'total_count': 0,
                'last_update': datetime.utcnow().isoformat()
            }
            await self.redis.redis.setex(activity_key, 86400, json.dumps(activity_data))  # 24 hours

            # Update user session history
            await self._update_user_session_history(user_id, session_id, enhanced_session_data)

            logger.info("Intelligent session created",
                       user_id=user_id,
                       session_id=session_id,
                       timeout_minutes=timeout_seconds/60,
                       features=list(enhanced_session_data['intelligent_features'].keys()))

            return {
                'session_id': session_id,
                'timeout_seconds': timeout_seconds,
                'timeout_minutes': timeout_seconds / 60,
                'intelligent_features': enhanced_session_data['intelligent_features'],
                'created_at': enhanced_session_data['created_at']
            }

        except Exception as e:
            logger.error("Error creating intelligent session",
                        user_id=user_id,
                        session_id=session_id,
                        error=str(e))
            raise

    async def track_session_activity(self, session_id: str, activity_type: str, metadata: dict[str, Any] = None):
        """Track user activity for intelligent session management"""
        try:
            if not self.redis.is_connected:
                return

            # Update session last activity
            session_key = self._make_session_key(session_id)
            session_data = await self.redis.redis.get(session_key)

            if session_data:
                data = json.loads(session_data)
                data['last_activity'] = datetime.utcnow().isoformat()
                data['activity_count'] = data.get('activity_count', 0) + 1

                # Update session with new activity
                await self.redis.redis.setex(session_key, data['timeout_seconds'], json.dumps(data))

            # Track detailed activity
            activity_key = self._make_activity_key(session_id)
            activity_data = await self.redis.redis.get(activity_key)

            if activity_data:
                activities = json.loads(activity_data)

                new_activity = {
                    'type': activity_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': metadata or {}
                }

                activities['activities'].append(new_activity)
                activities['total_count'] += 1
                activities['last_update'] = datetime.utcnow().isoformat()

                # Keep only last 100 activities to manage memory
                if len(activities['activities']) > 100:
                    activities['activities'] = activities['activities'][-100:]

                await self.redis.redis.setex(activity_key, 86400, json.dumps(activities))

            logger.debug("Session activity tracked",
                        session_id=session_id,
                        activity_type=activity_type,
                        metadata=metadata)

        except Exception as e:
            logger.error("Error tracking session activity",
                        session_id=session_id,
                        error=str(e))

    async def get_session_analytics(self, session_id: str) -> dict[str, Any]:
        """Get comprehensive session analytics"""
        try:
            if not self.redis.is_connected:
                return {"error": "Redis not connected"}

            # Get session data
            session_key = self._make_session_key(session_id)
            session_data = await self.redis.redis.get(session_key)

            if not session_data:
                return {"error": "Session not found"}

            session = json.loads(session_data)

            # Get session metadata
            meta_key = self._make_session_meta_key(session_id)
            meta_data = await self.redis.redis.get(meta_key)
            meta = json.loads(meta_data) if meta_data else {}

            # Get activity data
            activity_key = self._make_activity_key(session_id)
            activity_data = await self.redis.redis.get(activity_key)
            activities = json.loads(activity_data) if activity_data else {'activities': [], 'total_count': 0}

            # Calculate session duration
            created_at = datetime.fromisoformat(session['created_at'])
            last_activity = datetime.fromisoformat(session['last_activity'])
            duration_minutes = (last_activity - created_at).total_seconds() / 60

            # Calculate remaining time
            timeout_seconds = session['timeout_seconds']
            elapsed_seconds = (datetime.utcnow() - last_activity).total_seconds()
            remaining_seconds = max(0, timeout_seconds - elapsed_seconds)

            analytics = {
                'session_id': session_id,
                'user_id': session['user_id'],
                'created_at': session['created_at'],
                'last_activity': session['last_activity'],
                'duration_minutes': round(duration_minutes, 2),
                'timeout_minutes': timeout_seconds / 60,
                'remaining_minutes': round(remaining_seconds / 60, 2),
                'activity_count': session.get('activity_count', 0),
                'intelligent_features': session.get('intelligent_features', {}),
                'recent_activities': activities['activities'][-10:],  # Last 10 activities
                'session_health': {
                    'active': remaining_seconds > 0,
                    'renewal_recommended': remaining_seconds < (timeout_seconds * self.config.renewal_threshold),
                    'expires_at': (last_activity + timedelta(seconds=timeout_seconds)).isoformat()
                }
            }

            return analytics

        except Exception as e:
            logger.error("Error getting session analytics", session_id=session_id, error=str(e))
            return {"error": str(e)}

    async def get_renewal_recommendation(self, session_id: str) -> dict[str, Any]:
        """Get intelligent session renewal recommendation"""
        try:
            analytics = await self.get_session_analytics(session_id)

            if "error" in analytics:
                return analytics

            remaining_minutes = analytics['remaining_minutes']
            activity_count = analytics['activity_count']
            duration_minutes = analytics['duration_minutes']

            # Calculate renewal recommendation
            should_renew = False
            renewal_reason = []
            confidence = 0.0

            if remaining_minutes < 5:  # Less than 5 minutes remaining
                should_renew = True
                renewal_reason.append("Session expiring soon")
                confidence += 0.4

            if activity_count > 10:  # High activity
                should_renew = True
                renewal_reason.append("High user activity detected")
                confidence += 0.3

            if duration_minutes > 60:  # Long session
                should_renew = True
                renewal_reason.append("Extended work session")
                confidence += 0.2

            # Check for important context (SPEC-031 integration)
            user_id = analytics['user_id']
            context_importance = await self._get_context_importance(user_id)
            if context_importance == 'important':
                should_renew = True
                renewal_reason.append("Working with important memories")
                confidence += 0.1

            recommendation = {
                'session_id': session_id,
                'should_renew': should_renew,
                'confidence': min(1.0, confidence),
                'reasons': renewal_reason,
                'remaining_minutes': remaining_minutes,
                'recommended_action': 'renew' if should_renew else 'continue',
                'renewal_urgency': 'high' if remaining_minutes < 2 else 'medium' if remaining_minutes < 10 else 'low'
            }

            # Cache recommendation
            renewal_key = self._make_renewal_key(session_id)
            await self.redis.redis.setex(renewal_key, 3600, json.dumps(recommendation))

            return recommendation

        except Exception as e:
            logger.error("Error getting renewal recommendation", session_id=session_id, error=str(e))
            return {"error": str(e)}

    async def renew_session_intelligently(self, session_id: str) -> dict[str, Any]:
        """Intelligently renew a session with updated timeout"""
        try:
            if not self.redis.is_connected:
                raise Exception("Redis not connected")

            # Get current session
            session_key = self._make_session_key(session_id)
            session_data = await self.redis.redis.get(session_key)

            if not session_data:
                raise Exception("Session not found")

            session = json.loads(session_data)
            user_id = session['user_id']

            # Recalculate intelligent timeout based on current behavior
            new_timeout = await self.calculate_intelligent_timeout(user_id, session)

            # Update session data
            session['last_activity'] = datetime.utcnow().isoformat()
            session['timeout_seconds'] = new_timeout
            session['renewed_at'] = datetime.utcnow().isoformat()
            session['renewal_count'] = session.get('renewal_count', 0) + 1

            # Store renewed session
            await self.redis.redis.setex(session_key, new_timeout, json.dumps(session))

            # Track renewal activity
            await self.track_session_activity(session_id, 'session_renewed', {
                'new_timeout_minutes': new_timeout / 60,
                'renewal_count': session['renewal_count']
            })

            logger.info("Session renewed intelligently",
                       session_id=session_id,
                       user_id=user_id,
                       new_timeout_minutes=new_timeout/60,
                       renewal_count=session['renewal_count'])

            return {
                'session_id': session_id,
                'renewed': True,
                'new_timeout_minutes': new_timeout / 60,
                'expires_at': (datetime.utcnow() + timedelta(seconds=new_timeout)).isoformat(),
                'renewal_count': session['renewal_count']
            }

        except Exception as e:
            logger.error("Error renewing session", session_id=session_id, error=str(e))
            raise

    async def _update_user_session_history(self, user_id: str, session_id: str, session_data: dict[str, Any]):
        """Update user's session history for intelligence learning"""
        try:
            user_key = self._make_user_session_key(user_id)
            user_data = await self.redis.redis.get(user_key)

            if user_data:
                data = json.loads(user_data)
            else:
                data = {
                    'user_id': user_id,
                    'recent_sessions': [],
                    'total_sessions': 0,
                    'preferences': {}
                }

            # Add current session to history
            session_summary = {
                'session_id': session_id,
                'created_at': session_data['created_at'],
                'timeout_seconds': session_data['timeout_seconds'],
                'activity_count': session_data.get('activity_count', 0)
            }

            data['recent_sessions'].append(session_summary)
            data['total_sessions'] += 1
            data['last_updated'] = datetime.utcnow().isoformat()

            # Keep only last 50 sessions
            if len(data['recent_sessions']) > 50:
                data['recent_sessions'] = data['recent_sessions'][-50:]

            # Store for 30 days
            await self.redis.redis.setex(user_key, 2592000, json.dumps(data))

        except Exception as e:
            logger.error("Error updating user session history", user_id=user_id, error=str(e))

# Global session manager instance
session_manager = None

async def get_session_manager() -> IntelligentSessionManager:
    """Dependency injection for session manager"""
    global session_manager

    if session_manager is None:
        redis_client = await get_redis_client()
        relevance_engine = await get_relevance_engine()
        session_manager = IntelligentSessionManager(redis_client, relevance_engine)

    return session_manager

# Convenience functions for common operations
async def create_intelligent_session(user_id: str, session_id: str, session_data: dict[str, Any]) -> dict[str, Any]:
    """Create an intelligent session"""
    manager = await get_session_manager()
    return await manager.create_intelligent_session(user_id, session_id, session_data)

async def track_activity(session_id: str, activity_type: str, metadata: dict[str, Any] = None):
    """Track session activity"""
    manager = await get_session_manager()
    await manager.track_session_activity(session_id, activity_type, metadata)

async def get_session_analytics(session_id: str) -> dict[str, Any]:
    """Get session analytics"""
    manager = await get_session_manager()
    return await manager.get_session_analytics(session_id)
