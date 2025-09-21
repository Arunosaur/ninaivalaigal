#!/usr/bin/env python3
"""
Token refresh and graceful expiration handling for mem0
Prevents memory loss during active recording sessions
"""

import asyncio
from datetime import datetime, timedelta

import jwt
from auth import JWT_ALGORITHM, JWT_EXPIRATION_HOURS, JWT_SECRET


class TokenManager:
    """Manages JWT token refresh and graceful expiration handling"""

    def __init__(self):
        self.refresh_buffer_hours = 2  # Refresh tokens 2 hours before expiration
        self.active_sessions = {}  # user_id -> session_info

    def is_token_near_expiry(self, token: str) -> bool:
        """Check if token will expire within refresh buffer time"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            exp_timestamp = payload.get("exp")
            if not exp_timestamp:
                return True

            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            buffer_time = datetime.utcnow() + timedelta(hours=self.refresh_buffer_hours)

            return exp_datetime <= buffer_time

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return True

    def create_refreshed_token(self, old_token: str) -> str | None:
        """Create a new token with extended expiration based on old token data"""
        try:
            # Decode old token (ignoring expiration for refresh)
            payload = jwt.decode(
                old_token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False},
            )

            # Create new payload with fresh expiration
            new_payload = {
                "user_id": payload.get("user_id"),
                "email": payload.get("email"),
                "account_type": payload.get("account_type"),
                "role": payload.get("role"),
                "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            }

            # Generate new token
            new_token = jwt.encode(new_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
            return new_token

        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None

    def register_active_session(self, user_id: int, context_name: str, token: str):
        """Register an active recording session to prevent memory loss"""
        self.active_sessions[user_id] = {
            "context_name": context_name,
            "token": token,
            "started_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "memory_buffer": [],
        }

    def update_session_activity(self, user_id: int, memory_data: dict = None):
        """Update session activity and buffer memory if provided"""
        if user_id in self.active_sessions:
            self.active_sessions[user_id]["last_activity"] = datetime.utcnow()
            if memory_data:
                self.active_sessions[user_id]["memory_buffer"].append(memory_data)

    def get_session_token(self, user_id: int) -> str | None:
        """Get current valid token for user session, refreshing if needed"""
        if user_id not in self.active_sessions:
            return None

        session = self.active_sessions[user_id]
        current_token = session["token"]

        # Check if token needs refresh
        if self.is_token_near_expiry(current_token):
            refreshed_token = self.create_refreshed_token(current_token)
            if refreshed_token:
                session["token"] = refreshed_token
                return refreshed_token
            else:
                # Token refresh failed - preserve memory buffer
                print(
                    f"Token refresh failed for user {user_id}, preserving memory buffer"
                )
                return None

        return current_token

    def flush_memory_buffer(self, user_id: int, db_manager) -> bool:
        """Flush buffered memories to database before token expires"""
        if user_id not in self.active_sessions:
            return False

        session = self.active_sessions[user_id]
        memory_buffer = session.get("memory_buffer", [])
        context_name = session.get("context_name")

        if not memory_buffer or not context_name:
            return True

        try:
            # Save all buffered memories
            for memory_data in memory_buffer:
                db_manager.add_memory(
                    context=context_name,
                    content=memory_data.get("content", ""),
                    memory_type=memory_data.get("type", "auto_save"),
                    source="token_expiry_save",
                    user_id=user_id,
                    metadata=memory_data.get("metadata", {}),
                )

            # Clear buffer after successful save
            session["memory_buffer"] = []
            print(
                f"Flushed {len(memory_buffer)} memories for user {user_id} before token expiry"
            )
            return True

        except Exception as e:
            print(f"Error flushing memory buffer for user {user_id}: {e}")
            return False

    def cleanup_expired_sessions(self, db_manager):
        """Clean up expired sessions and save any remaining memories"""
        expired_users = []

        for user_id, session in self.active_sessions.items():
            token = session["token"]

            try:
                # Check if token is actually expired (not just near expiry)
                jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            except jwt.ExpiredSignatureError:
                # Token expired - flush memories and mark for cleanup
                self.flush_memory_buffer(user_id, db_manager)
                expired_users.append(user_id)
            except jwt.InvalidTokenError:
                # Invalid token - mark for cleanup
                expired_users.append(user_id)

        # Remove expired sessions
        for user_id in expired_users:
            del self.active_sessions[user_id]
            print(f"Cleaned up expired session for user {user_id}")


# Global token manager instance
token_manager = TokenManager()


def get_token_manager() -> TokenManager:
    """Get global token manager instance"""
    return token_manager


async def auto_refresh_tokens(db_manager):
    """Background task to automatically refresh tokens and save memories"""
    while True:
        try:
            token_manager.cleanup_expired_sessions(db_manager)

            # Check all active sessions for refresh needs
            for user_id, session in list(token_manager.active_sessions.items()):
                current_token = session["token"]

                if token_manager.is_token_near_expiry(current_token):
                    # Try to refresh token
                    new_token = token_manager.create_refreshed_token(current_token)
                    if new_token:
                        session["token"] = new_token
                        print(f"Auto-refreshed token for user {user_id}")
                    else:
                        # Refresh failed - save memories before expiry
                        token_manager.flush_memory_buffer(user_id, db_manager)
                        print(
                            f"Token refresh failed for user {user_id}, memories saved"
                        )

            # Sleep for 30 minutes before next check
            await asyncio.sleep(1800)

        except Exception as e:
            print(f"Error in auto-refresh task: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes on error
