# auto_recording.py - Automatic CCTV-style recording for mem0
# Records AI interactions automatically without manual 'remember' commands

import asyncio
from datetime import datetime

from database import DatabaseManager
from token_refresh import get_token_manager


class AutoRecorder:
    """
    Automatic CCTV-style recording system for mem0
    Records AI interactions and conversations automatically when contexts are active
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.active_contexts = {}  # context_name -> recording_state
        self.recording_buffer = {}  # context_name -> [messages]
        self.auto_save_interval = 30  # seconds

    async def start_recording(self, context_name: str, user_id: int = None, token: str = None) -> dict:
        """Start automatic recording for a context (CCTV ON)"""
        try:
            # Create or activate context with correct parameters
            self.db.create_context(name=context_name, user_id=user_id, scope="personal")
            context_id = f"{context_name}_{user_id or 'default'}"

            self.active_contexts[context_name] = {
                'context_id': context_id,
                'user_id': user_id,
                'started_at': datetime.utcnow(),
                'message_count': 0,
                'auto_save_enabled': True
            }

            self.recording_buffer[context_name] = []

            # Register session with token manager for graceful expiration handling
            if user_id and token:
                token_manager = get_token_manager()
                token_manager.register_active_session(user_id, context_name, token)

            # Start auto-save background task
            asyncio.create_task(self._auto_save_loop(context_name))

            return {
                "success": True,
                "message": f"🎥 CCTV Recording STARTED for context: {context_name}",
                "context_id": context_id,
                "auto_recording": True,
                "token_protection": bool(user_id and token)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start recording: {str(e)}"
            }

    async def stop_recording(self, context_name: str) -> dict:
        """Stop automatic recording for a context (CCTV OFF)"""
        try:
            if context_name not in self.active_contexts:
                return {
                    "success": False,
                    "error": f"Context '{context_name}' is not actively recording"
                }

            # Save any remaining buffered messages
            await self._flush_buffer(context_name)

            # Update database to set context as inactive
            session = self.db.get_session()
            try:
                from database import Context
                context = session.query(Context).filter_by(name=context_name).first()
                if context:
                    context.is_active = False
                    session.commit()
            finally:
                session.close()

            # Remove from active contexts
            recording_info = self.active_contexts.pop(context_name)
            self.recording_buffer.pop(context_name, None)

            return {
                "success": True,
                "message": f"🛑 CCTV Recording STOPPED for context: {context_name}",
                "messages_recorded": recording_info['message_count'],
                "duration": str(datetime.utcnow() - recording_info['started_at'])
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop recording: {str(e)}"
            }

    async def record_interaction(self, context_name: str, interaction_type: str,
                               content: str, metadata: dict = None) -> bool:
        """
        Automatically record an AI interaction (CCTV capture)
        
        Args:
            context_name: Active recording context
            interaction_type: 'user_message', 'ai_response', 'system_event'
            content: The actual content to record
            metadata: Additional context (file_path, cursor_position, etc.)
        """
        if context_name not in self.active_contexts:
            return False

        try:
            timestamp = datetime.utcnow()
            user_id = self.active_contexts[context_name].get('user_id')

            # Create memory entry
            memory_data = {
                "timestamp": timestamp.isoformat(),
                "type": interaction_type,
                "content": content,
                "metadata": metadata or {}
            }

            # Update token manager session activity and buffer memory
            if user_id:
                token_manager = get_token_manager()
                token_manager.update_session_activity(user_id, memory_data)

            # Add to buffer for batch processing
            self.recording_buffer[context_name].append(memory_data)

            # Increment message count and check for auto-save
            self.active_contexts[context_name]['message_count'] += 1

            # Auto-save every 10 messages or when AI responds
            AUTO_SAVE_THRESHOLD = 10
            if (self.active_contexts[context_name]['message_count'] % AUTO_SAVE_THRESHOLD == 0 or
                interaction_type in ['ai_response', 'system_event']):
                await self._flush_buffer_with_token_check(context_name)

            return True

        except Exception as e:
            print(f"Error recording interaction: {e}")
            return False

    async def get_recording_status(self) -> dict:
        """Get current CCTV recording status"""
        return {
            "active_contexts": len(self.active_contexts),
            "contexts": {
                name: {
                    "started_at": info['started_at'].isoformat(),
                    "messages_recorded": info['message_count'],
                    "user_id": info['user_id']
                }
                for name, info in self.active_contexts.items()
            }
        }

    async def recall_hierarchical(self, query: str, user_id: int,
                                context_name: str = None) -> dict:
        """
        Recall memories with hierarchical context search
        Personal -> Team -> Organization contexts
        """
        try:
            results = {
                "personal": [],
                "team": [],
                "organization": [],
                "query": query
            }

            # 1. Personal context memories
            if context_name:
                personal_memories = self.db.get_memories(context_name, user_id)
                results["personal"] = self._format_memories(personal_memories, "Personal")

            # 2. Team context memories
            user_teams = self.db.get_user_teams(user_id)
            for team in user_teams:
                team_contexts = self.db.get_team_contexts(team.id)
                for context in team_contexts:
                    if self._matches_query(context.name, query):
                        team_memories = self.db.get_memories(context.name)
                        results["team"].extend(
                            self._format_memories(team_memories, f"Team: {team.name}")
                        )

            # 3. Organization context memories
            user_orgs = self.db.get_user_organizations(user_id)
            for org in user_orgs:
                org_contexts = self.db.get_organization_contexts(org.id)
                for context in org_contexts:
                    if self._matches_query(context.name, query):
                        org_memories = self.db.get_memories(context.name)
                        results["organization"].extend(
                            self._format_memories(org_memories, f"Org: {org.name}")
                        )

            return results

        except Exception as e:
            return {
                "error": f"Failed to recall hierarchical memories: {str(e)}",
                "personal": [],
                "team": [],
                "organization": []
            }

    async def _auto_save_loop(self, context_name: str):
        """Background task to auto-save buffered messages"""
        while context_name in self.active_contexts:
            try:
                await asyncio.sleep(self.auto_save_interval)
                if context_name in self.recording_buffer:
                    await self._flush_buffer(context_name)
            except Exception as e:
                print(f"Auto-save error for {context_name}: {e}")

    async def _flush_buffer(self, context_name: str):
        """Save buffered messages to database"""
        if context_name not in self.recording_buffer:
            return

        buffer = self.recording_buffer[context_name]
        if not buffer:
            return

        try:
            context_info = self.active_contexts[context_name]

            for memory_data in buffer:
                self.db.add_memory(
                    context=context_name,
                    content=memory_data['content'],
                    memory_type=memory_data['type'],
                    source='auto_recording',
                    user_id=context_info['user_id'],
                    metadata=memory_data.get('metadata', {})
                )

            # Clear buffer after successful save
            self.recording_buffer[context_name] = []

        except Exception as e:
            print(f"Error flushing buffer for {context_name}: {e}")

    async def _flush_buffer_with_token_check(self, context_name: str):
        """Save buffered messages with token expiration protection"""
        if context_name not in self.recording_buffer:
            return

        buffer = self.recording_buffer[context_name]
        if not buffer:
            return

        try:
            context_info = self.active_contexts[context_name]
            user_id = context_info.get('user_id')

            # Check token status if user is authenticated
            if user_id:
                token_manager = get_token_manager()
                valid_token = token_manager.get_session_token(user_id)

                if not valid_token:
                    # Token expired/invalid - use emergency save
                    print(f"Token expired during recording for user {user_id}, using emergency save")
                    token_manager.flush_memory_buffer(user_id, self.db)
                    return

            # Normal flush with valid token
            await self._flush_buffer(context_name)

        except Exception as e:
            print(f"Error in token-aware buffer flush for {context_name}: {e}")
            # Fallback to regular flush
            await self._flush_buffer(context_name)

    def _format_memories(self, memories: list, source: str) -> list[dict]:
        """Format memories for hierarchical display"""
        formatted = []
        for memory in memories:
            formatted.append({
                "source": source,
                "content": memory.get('data', ''),
                "type": memory.get('type', 'unknown'),
                "created_at": memory.get('created_at', ''),
                "context": memory.get('context', '')
            })
        return formatted

    def _matches_query(self, text: str, query: str) -> bool:
        """Simple query matching for context search"""
        return query.lower() in text.lower()

# Global auto-recorder instance
auto_recorder = None

def get_auto_recorder(db_manager: DatabaseManager) -> AutoRecorder:
    """Get or create global auto-recorder instance"""
    global auto_recorder
    if auto_recorder is None:
        auto_recorder = AutoRecorder(db_manager)
    return auto_recorder
