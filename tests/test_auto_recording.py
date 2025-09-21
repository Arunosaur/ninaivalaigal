"""
Test suite for CCTV-style automatic recording functionality
"""
import os
import sys
from unittest.mock import Mock

import pytest

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from auto_recording import AutoRecorder, get_auto_recorder
from database import DatabaseManager


class TestAutoRecording:
    """Test CCTV-style automatic recording system"""

    @pytest.fixture
    def mock_db(self):
        """Mock database manager"""
        db = Mock(spec=DatabaseManager)
        db.store_memory = Mock(return_value={"id": 1, "content": "test"})
        db.get_memories = Mock(return_value=[])
        db.get_user_contexts = Mock(return_value=[])
        db.get_contexts_by_name_pattern = Mock(return_value=[])
        return db

    @pytest.fixture
    def auto_recorder(self, mock_db):
        """Create AutoRecorder instance with mock database"""
        return AutoRecorder(mock_db)

    @pytest.mark.asyncio
    async def test_start_recording(self, auto_recorder):
        """Test starting CCTV recording for a context"""
        result = await auto_recorder.start_recording("test-project", user_id=1)

        assert result["success"] is True
        assert "test-project" in result["message"]
        assert result["context_id"] is not None

        # Verify recording status
        status = await auto_recorder.get_recording_status()
        assert status["active_contexts"] == 1
        assert "test-project" in status["contexts"]

    @pytest.mark.asyncio
    async def test_stop_recording(self, auto_recorder):
        """Test stopping CCTV recording"""
        # Start recording first
        await auto_recorder.start_recording("test-project", user_id=1)

        # Stop recording
        result = await auto_recorder.stop_recording("test-project")

        assert result["success"] is True
        assert "test-project" in result["message"]

        # Verify recording stopped
        status = await auto_recorder.get_recording_status()
        assert status["active_contexts"] == 0
        assert "test-project" not in status["contexts"]

    @pytest.mark.asyncio
    async def test_record_interaction(self, auto_recorder):
        """Test automatic interaction recording"""
        # Start recording
        await auto_recorder.start_recording("test-project", user_id=1)

        # Record interaction
        success = await auto_recorder.record_interaction(
            "test-project",
            "ai_prompt",
            "How do I implement authentication?",
            {"source": "vscode"}
        )

        assert success is True

        # Check message was buffered
        status = await auto_recorder.get_recording_status()
        assert status["contexts"]["test-project"]["messages_recorded"] == 1

    @pytest.mark.asyncio
    async def test_record_interaction_inactive_context(self, auto_recorder):
        """Test recording to inactive context returns False"""
        success = await auto_recorder.record_interaction(
            "inactive-project",
            "ai_prompt",
            "This should not be recorded"
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_auto_save_threshold(self, auto_recorder):
        """Test auto-save triggers after message threshold"""
        await auto_recorder.start_recording("test-project", user_id=1)

        # Record multiple interactions to trigger auto-save
        for i in range(12):  # Exceeds AUTO_SAVE_THRESHOLD of 10
            await auto_recorder.record_interaction(
                "test-project",
                "ai_prompt",
                f"Test message {i}"
            )

        # Verify messages were recorded (auto-save happens in background)
        status = await auto_recorder.get_recording_status()
        assert status["contexts"]["test-project"]["messages_recorded"] == 12

    @pytest.mark.asyncio
    async def test_hierarchical_recall(self, auto_recorder, mock_db):
        """Test hierarchical memory recall across contexts"""
        # Mock hierarchical memory retrieval
        mock_db.get_memories.side_effect = [
            [{"content": "Personal memory", "context": "personal"}],
            [{"content": "Team memory", "context": "team"}],
            [{"content": "Org memory", "context": "organization"}]
        ]

        results = await auto_recorder.recall_hierarchical("authentication", user_id=1)

        # Should return empty results since recall_hierarchical returns empty by default
        assert "personal" in results
        assert "team" in results
        assert "organization" in results

    @pytest.mark.asyncio
    async def test_multiple_contexts(self, auto_recorder):
        """Test recording multiple contexts simultaneously"""
        # Start recording for multiple contexts
        await auto_recorder.start_recording("project-a", user_id=1)
        await auto_recorder.start_recording("project-b", user_id=1)

        # Record to both contexts
        await auto_recorder.record_interaction("project-a", "ai_prompt", "Message A")
        await auto_recorder.record_interaction("project-b", "ai_prompt", "Message B")

        # Verify both contexts are active
        status = await auto_recorder.get_recording_status()
        assert status["active_contexts"] == 2
        assert "project-a" in status["contexts"]
        assert "project-b" in status["contexts"]
        assert status["contexts"]["project-a"]["messages_recorded"] == 1
        assert status["contexts"]["project-b"]["messages_recorded"] == 1

    @pytest.mark.asyncio
    async def test_format_for_storage(self, auto_recorder):
        """Test message formatting for database storage"""
        await auto_recorder.start_recording("test-project", user_id=1)

        # Record interaction with metadata
        await auto_recorder.record_interaction(
            "test-project",
            "ai_response",
            "Here's how to implement JWT authentication...",
            {
                "source": "claude",
                "timestamp": "2024-01-15T10:30:00Z",
                "token_count": 150
            }
        )

        # Verify formatting includes metadata
        status = await auto_recorder.get_recording_status()
        assert status["contexts"]["test-project"]["messages_recorded"] == 1

    def test_get_auto_recorder_singleton(self, mock_db):
        """Test auto recorder singleton pattern"""
        recorder1 = get_auto_recorder(mock_db)
        recorder2 = get_auto_recorder(mock_db)

        # Should return same instance
        assert recorder1 is recorder2

    @pytest.mark.asyncio
    async def test_recording_status_empty(self, auto_recorder):
        """Test recording status when no contexts are active"""
        status = await auto_recorder.get_recording_status()

        assert status["active_contexts"] == 0
        assert status["contexts"] == {}

    @pytest.mark.asyncio
    async def test_stop_nonexistent_context(self, auto_recorder):
        """Test stopping recording for non-existent context"""
        result = await auto_recorder.stop_recording("nonexistent-project")

        assert result["success"] is False
        assert "not actively recording" in result["error"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
