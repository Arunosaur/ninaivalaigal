"""
Test suite for FastAPI CCTV recording endpoints
"""
import os
import subprocess
import time

import pytest
import requests


class TestFastAPIEndpoints:
    """Test CCTV FastAPI endpoints"""

    BASE_URL = "http://localhost:8000"

    @classmethod
    def setup_class(cls):
        """Start FastAPI server for testing"""
        env = os.environ.copy()
        os.environ["NINAIVALAIGAL_DATABASE_URL"] = "sqlite:///test.db"
        os.environ["NINAIVALAIGAL_JWT_SECRET"] = "test-secret-key"

        cls.server_process = subprocess.Popen(
            ["python", "server/main.py"],
            cwd="/Users/asrajag/Workspace/mem0",
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        time.sleep(3)

        # Verify server is running
        try:
            response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
            if response.status_code != 200:
                raise Exception("Server not responding")
        except:
            cls.teardown_class()
            raise Exception("Failed to start FastAPI server")

    @classmethod
    def teardown_class(cls):
        """Stop FastAPI server"""
        if hasattr(cls, "server_process"):
            cls.server_process.terminate()
            cls.server_process.wait()

    def test_start_recording_endpoint(self):
        """Test POST /context/start endpoint"""
        response = requests.post(
            f"{self.BASE_URL}/context/start", json={"context": "test-fastapi-context"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "🎥 CCTV Recording STARTED" in data["message"]
        assert data["context"] == "test-fastapi-context"
        assert data["auto_recording"] is True

    def test_recording_status_endpoint(self):
        """Test GET /context/status endpoint"""
        # Start recording first
        requests.post(
            f"{self.BASE_URL}/context/start", json={"context": "status-test-context"}
        )

        response = requests.get(f"{self.BASE_URL}/context/status")

        assert response.status_code == 200
        data = response.json()
        assert "🎥 CCTV Active" in data["recording_status"]
        assert data["active_contexts"] >= 1
        assert "status-test-context" in data["contexts"]

    def test_stop_recording_endpoint(self):
        """Test POST /context/stop endpoint"""
        # Start recording first
        requests.post(
            f"{self.BASE_URL}/context/start", json={"context": "stop-test-context"}
        )

        response = requests.post(
            f"{self.BASE_URL}/context/stop", json={"context": "stop-test-context"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "🛑" in data["message"]
        assert data["context"] == "stop-test-context"
        assert "messages_recorded" in data

    def test_record_interaction_endpoint(self):
        """Test POST /memory/record endpoint"""
        # Start recording first
        requests.post(
            f"{self.BASE_URL}/context/start", json={"context": "record-test-context"}
        )

        response = requests.post(
            f"{self.BASE_URL}/memory/record",
            json={
                "context": "record-test-context",
                "interaction_type": "ai_prompt",
                "content": "How do I implement authentication?",
                "metadata": {"source": "test"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "🎥 Interaction recorded automatically" in data["message"]
        assert data["context"] == "record-test-context"
        assert data["type"] == "ai_prompt"

    def test_record_interaction_inactive_context(self):
        """Test recording to inactive context returns appropriate response"""
        response = requests.post(
            f"{self.BASE_URL}/memory/record",
            json={
                "context": "inactive-context",
                "interaction_type": "ai_prompt",
                "content": "This should not be recorded",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "not actively recording" in data["message"]
        assert data["recording_active"] is False

    def test_hierarchical_recall_endpoint(self):
        """Test GET /memory/recall endpoint"""
        response = requests.get(
            f"{self.BASE_URL}/memory/recall",
            params={"query": "authentication", "context": "test-context"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "authentication"
        assert data["context"] == "test-context"
        assert "results" in data
        assert "personal" in data["results"]
        assert "team" in data["results"]
        assert "organization" in data["results"]
        assert "total_memories" in data

    def test_stop_all_recordings_endpoint(self):
        """Test stopping all recordings without specifying context"""
        # Start multiple recordings
        requests.post(f"{self.BASE_URL}/context/start", json={"context": "context-1"})
        requests.post(f"{self.BASE_URL}/context/start", json={"context": "context-2"})

        response = requests.post(f"{self.BASE_URL}/context/stop")

        assert response.status_code == 200
        data = response.json()
        assert "🛑 Stopped recording" in data["message"]
        assert "stopped_contexts" in data

    def test_health_endpoint(self):
        """Test server health endpoint"""
        response = requests.get(f"{self.BASE_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_invalid_context_start(self):
        """Test starting recording with invalid parameters"""
        response = requests.post(
            f"{self.BASE_URL}/context/start", json={}  # Missing context parameter
        )

        # Should handle gracefully
        assert response.status_code in [400, 422, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
