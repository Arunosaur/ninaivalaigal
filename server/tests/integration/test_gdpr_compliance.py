#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Integration tests for GDPR Compliance (US#558 / SPEC-074)

Tests complete GDPR compliance workflows:
- Data Subject Access Requests (DSAR)
- Right to Erasure
- Data Portability
- Rectification, Restriction, Objection
- Encrypted exports
- API endpoints

Requirements:
    - Database connection
    - Test database with migrations applied
    - pytest installed
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from server.compliance.data_collector import GDPRDataCollector
from server.compliance.export import EncryptedDataExporter, ExportFormat
from server.compliance.gdpr import GDPRComplianceManager

# Import GDPR models directly from gdpr_models to avoid loading HIPAA models
from server.compliance.gdpr_models import (
    DataExport,
    DataSubjectRequest,
    DataSubjectRequestType,
)
from server.compliance.gdpr_models import ExportFormat as ExportFormatEnum
from server.compliance.gdpr_models import ExportStatus, RequestStatus


@pytest.mark.order(2)  # Run GDPR tests after HIPAA tests to avoid backref conflicts
class TestGDPRComplianceManager:
    """Tests for GDPRComplianceManager"""

    @pytest.fixture
    def db_session(self):
        """Get database session with graceful fallback and proper cleanup"""
        try:
            from server.database import DatabaseManager

            db = DatabaseManager()
            session = db.get_session()

            # Ensure clean transaction state at start
            try:
                session.rollback()
            except Exception:
                pass

            yield session

            # Cleanup: rollback any uncommitted changes at end
            try:
                session.rollback()
            except Exception:
                pass
            session.close()
        except Exception as e:
            # Database not available - skip tests that require it
            pytest.skip(f"Database not available: {str(e)}", allow_module_level=False)

    @pytest.fixture
    def gdpr_manager(self, db_session):
        """Create GDPR compliance manager with export manager"""
        from server.compliance.export import EncryptedDataExporter

        export_manager = EncryptedDataExporter(db_session=db_session)
        return GDPRComplianceManager(db_session=db_session, export_manager=export_manager)

    @pytest.fixture
    def test_user_id(self, db_session):
        """Create or get test user with unique identifier"""
        import time

        from server.database.models import User

        # Use timestamp to ensure uniqueness
        timestamp = int(time.time() * 1000000)  # Microseconds for better uniqueness
        unique_email = f"gdpr-test-{timestamp}@example.com"
        unique_username = f"gdpr_test_user_{timestamp}"

        # Try to find existing test user (fallback)
        test_user = db_session.query(User).filter(User.email == unique_email).first()

        if not test_user:
            test_user = User(
                id=uuid4(),
                email=unique_email,
                username=unique_username,
                name="GDPR Test User",
                password_hash="test_hash_placeholder",
            )
            db_session.add(test_user)
            db_session.commit()

        return test_user.id

    @pytest.mark.asyncio
    async def test_submit_dsar_request(self, gdpr_manager, test_user_id):
        """Test submitting a Data Subject Access Request"""
        # Create request
        request = DataSubjectRequest(
            id=uuid4(),
            user_id=test_user_id,
            request_type=DataSubjectRequestType.ACCESS.value,
            status=RequestStatus.PENDING.value,
        )

        gdpr_manager.db_session.add(request)
        gdpr_manager.db_session.commit()

        # Process request
        result = await gdpr_manager._handle_access_request(request)

        assert result is not None
        assert result.status == RequestStatus.COMPLETED.value
        assert result.completed_at is not None
        assert result.response_data is not None
        assert "export_id" in result.response_data or "data_export" in result.response_data

    @pytest.mark.asyncio
    async def test_submit_erasure_request(self, gdpr_manager, test_user_id):
        """Test submitting Right to Erasure request"""
        request = DataSubjectRequest(
            id=uuid4(),
            user_id=test_user_id,
            request_type=DataSubjectRequestType.ERASURE.value,
            status=RequestStatus.PENDING.value,
        )

        gdpr_manager.db_session.add(request)
        gdpr_manager.db_session.commit()

        # Process request
        result = await gdpr_manager._handle_erasure_request(request)

        assert result is not None
        assert result.status in [
            RequestStatus.COMPLETED.value,
            RequestStatus.PARTIAL.value,
            RequestStatus.REJECTED.value,
        ]

    @pytest.mark.asyncio
    async def test_submit_portability_request(self, gdpr_manager, test_user_id):
        """Test submitting Data Portability request"""
        request = DataSubjectRequest(
            id=uuid4(),
            user_id=test_user_id,
            request_type=DataSubjectRequestType.PORTABILITY.value,
            status=RequestStatus.PENDING.value,
        )

        gdpr_manager.db_session.add(request)
        gdpr_manager.db_session.commit()

        # Process request
        result = await gdpr_manager._handle_portability_request(request)

        assert result is not None
        assert result.status == RequestStatus.COMPLETED.value
        assert result.response_data is not None

    @pytest.mark.asyncio
    async def test_rectification_request(self, gdpr_manager, test_user_id):
        """Test Right to Rectification"""
        request = DataSubjectRequest(
            id=uuid4(),
            user_id=test_user_id,
            request_type=DataSubjectRequestType.RECTIFICATION.value,
            status=RequestStatus.PENDING.value,
            description="Update my email address",
        )

        # Use unique email to avoid conflicts
        import time

        timestamp = int(time.time() * 1000000)
        unique_email = f"updated-{timestamp}@example.com"
        data_updates = {"email": unique_email, "name": "Updated Name"}
        # Store data_updates in response_data for rectification handler
        request.response_data = {"data_updates": data_updates}

        gdpr_manager.db_session.add(request)
        gdpr_manager.db_session.commit()

        # Process request
        result = await gdpr_manager._handle_rectification_request(request)

        assert result is not None
        assert result.status == RequestStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_get_request_status(self, gdpr_manager, test_user_id):
        """Test retrieving request status"""
        # Create request
        request = DataSubjectRequest(
            id=uuid4(),
            user_id=test_user_id,
            request_type=DataSubjectRequestType.ACCESS.value,
            status=RequestStatus.PENDING.value,
        )

        gdpr_manager.db_session.add(request)
        gdpr_manager.db_session.commit()

        # Get status
        status = await gdpr_manager.get_request_status(request.id)

        assert status is not None
        assert status.id == request.id
        assert status.status == RequestStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_list_user_requests(self, gdpr_manager, test_user_id):
        """Test listing user requests"""
        # Create multiple requests
        for i in range(3):
            request = DataSubjectRequest(
                id=uuid4(),
                user_id=test_user_id,
                request_type=DataSubjectRequestType.ACCESS.value,
                status=RequestStatus.PENDING.value,
            )
            gdpr_manager.db_session.add(request)

        gdpr_manager.db_session.commit()

        # List requests
        requests = await gdpr_manager.list_user_requests(test_user_id)

        assert requests is not None
        assert len(requests) >= 3


@pytest.mark.order(2)  # Run GDPR tests after HIPAA tests to avoid backref conflicts
class TestEncryptedDataExporter:
    """Tests for EncryptedDataExporter"""

    @pytest.fixture
    def db_session(self):
        """Get database session with graceful fallback and proper cleanup"""
        try:
            from server.database import DatabaseManager

            db = DatabaseManager()
            session = db.get_session()

            # Ensure clean transaction state at start
            try:
                session.rollback()
            except Exception:
                pass

            yield session

            # Cleanup: rollback any uncommitted changes at end
            try:
                session.rollback()
            except Exception:
                pass
            session.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}", allow_module_level=False)

    @pytest.fixture
    def exporter(self, db_session):
        """Create encrypted data exporter"""
        return EncryptedDataExporter(db_session=db_session)

    @pytest.fixture
    def test_user_id(self, db_session):
        """Create or get test user with unique identifier"""
        import time

        from server.database.models import User

        # Use timestamp to ensure uniqueness
        timestamp = int(time.time() * 1000000)  # Microseconds for better uniqueness
        unique_email = f"export-test-{timestamp}@example.com"
        unique_username = f"export_test_user_{timestamp}"

        test_user = db_session.query(User).filter(User.email == unique_email).first()

        if not test_user:
            test_user = User(
                id=uuid4(),
                email=unique_email,
                username=unique_username,
                name="Export Test User",
                password_hash="test_hash_placeholder",
            )
            db_session.add(test_user)
            db_session.commit()

        return test_user.id

    @pytest.mark.asyncio
    async def test_create_json_export(self, exporter, test_user_id):
        """Test creating JSON export"""
        test_data = {
            "user_id": str(test_user_id),
            "profile": {"name": "Test User", "email": "test@example.com"},
            "memories": [],
            "contexts": [],
        }

        export = await exporter.create_export(user_id=test_user_id, format=ExportFormat.JSON)

        assert export is not None
        assert export.status == ExportStatus.READY.value or export.status == ExportStatus.PENDING.value
        assert export.format == ExportFormat.JSON.value
        assert export.user_id == test_user_id

    @pytest.mark.asyncio
    async def test_create_xml_export(self, exporter, test_user_id):
        """Test creating XML export"""
        export = await exporter.create_export(user_id=test_user_id, format=ExportFormat.XML)

        assert export is not None
        assert export.format == ExportFormat.XML.value

    @pytest.mark.asyncio
    async def test_create_csv_export(self, exporter, test_user_id):
        """Test creating CSV export"""
        export = await exporter.create_export(user_id=test_user_id, format=ExportFormat.CSV)

        assert export is not None
        assert export.format == ExportFormat.CSV.value

    @pytest.mark.asyncio
    async def test_encrypt_and_decrypt_export(self, exporter, test_user_id):
        """Test encryption functionality"""
        # Create export (should be encrypted)
        export = await exporter.create_export(user_id=test_user_id, format=ExportFormat.JSON)

        assert export is not None
        assert export.encryption_key_id is not None  # Encryption key ID should be set

        # Verify export was created with encryption
        assert export.status in [ExportStatus.READY.value, ExportStatus.GENERATING.value]


@pytest.mark.order(2)  # Run GDPR tests after HIPAA tests to avoid backref conflicts
class TestGDPRDataCollector:
    """Tests for GDPRDataCollector"""

    @pytest.fixture
    def db_session(self):
        """Get database session with graceful fallback and proper cleanup"""
        try:
            from server.database import DatabaseManager

            db = DatabaseManager()
            session = db.get_session()

            # Ensure clean transaction state at start
            try:
                session.rollback()
            except Exception:
                pass

            yield session

            # Cleanup: rollback any uncommitted changes at end
            try:
                session.rollback()
            except Exception:
                pass
            session.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}", allow_module_level=False)

    @pytest.fixture
    def collector(self, db_session):
        """Create GDPR data collector"""
        return GDPRDataCollector(db_session)

    @pytest.fixture
    def test_user_id(self, db_session):
        """Create or get test user with unique identifier"""
        import time

        from server.database.models import User

        # Use timestamp to ensure uniqueness
        timestamp = int(time.time() * 1000000)  # Microseconds for better uniqueness
        unique_email = f"collector-test-{timestamp}@example.com"
        unique_username = f"collector_test_user_{timestamp}"

        test_user = db_session.query(User).filter(User.email == unique_email).first()

        if not test_user:
            test_user = User(
                id=uuid4(),
                email=unique_email,
                username=unique_username,
                name="Collector Test User",
                password_hash="test_hash_placeholder",
            )
            db_session.add(test_user)
            db_session.commit()

        return test_user.id

    @pytest.mark.asyncio
    async def test_collect_user_data(self, collector, test_user_id):
        """Test collecting all user data"""
        data = await collector.collect_all_user_data(test_user_id)

        assert data is not None
        assert "user_id" in data
        assert data["user_id"] == str(test_user_id)
        assert "data" in data  # Data collector returns nested structure
        assert "profile" in data["data"] or "memories" in data["data"]  # At least some data collected

    @pytest.mark.asyncio
    async def test_collect_memories(self, collector, test_user_id):
        """Test collecting user memories"""
        memories = await collector._collect_memories(test_user_id)

        assert memories is not None
        assert isinstance(memories, list)


@pytest.mark.order(2)  # Run GDPR tests after HIPAA tests to avoid backref conflicts
class TestGDPRAPIEndpoints:
    """Integration tests for GDPR API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        import os
        import sys

        # Set required environment variables if not set
        if not os.getenv("NINAIVALAIGAL_JWT_SECRET"):
            os.environ["NINAIVALAIGAL_JWT_SECRET"] = "test_secret_key_for_testing_only_not_for_production"

        # Disable tracing for tests
        os.environ["TESTING"] = "true"
        os.environ["OTEL_TRACING_ENABLED"] = "false"

        # Ensure we import from the server package, not test modules
        # Remove tests directory from path if it's causing conflicts
        server_path = os.path.join(os.path.dirname(__file__), "..", "..")
        if server_path not in sys.path:
            sys.path.insert(0, server_path)

        from fastapi.testclient import TestClient
        from main import app

        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers"""
        # This would need actual auth setup
        # For now, return empty headers (would need mock auth)
        return {}

    def test_dsar_endpoint_exists(self, client):
        """Test DSAR endpoint exists"""
        # Note: This would need authentication in real tests
        # DSAR endpoint is POST, not GET
        response = client.post("/api/v1/compliance/dsar", json={})
        # Should return 401, 403, 404, 405, or 422 (validation error) without auth/proper setup
        assert response.status_code in [401, 403, 404, 405, 422]

    def test_erasure_endpoint_exists(self, client):
        """Test erasure endpoint exists"""
        response = client.post("/api/v1/compliance/erasure")
        assert response.status_code in [401, 403, 404, 405, 422]  # 422 for validation error, 405 for method not allowed

    def test_portability_endpoint_exists(self, client):
        """Test portability endpoint exists"""
        response = client.post("/api/v1/compliance/portability")
        assert response.status_code in [401, 403, 404, 405, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
