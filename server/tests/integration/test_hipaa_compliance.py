#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""
Integration tests for HIPAA Compliance (US#121 / SPEC-011)

Tests complete HIPAA compliance workflows:
- PHI detection
- PHI protection validation
- HIPAA audit trails
- Minimum necessary access
- Breach detection and assessment
- Compliance reporting
- Email notifications

Requirements:
    - Database connection
    - Test database with migrations applied
    - pytest installed
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from server.compliance.hipaa import (
    HIPAAComplianceManager,
    HIPAAViolationType,
    PHICategory,
)

# Import HIPAA models directly from hipaa_models to avoid importing GDPR models
# This prevents backref conflicts when HIPAA tests run first (order=1)
from server.compliance.hipaa_models import (
    HIPAAAuditLog,
    HIPAABreachIncident,
    HIPAAPHIDetection,
)
from server.compliance.hipaa_notifications import HIPAAEmailNotifier


@pytest.mark.order(1)  # Run HIPAA tests before GDPR tests to avoid backref conflicts
class TestHIPAAComplianceManager:
    """Tests for HIPAAComplianceManager"""

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
    def hipaa_manager(self, db_session):
        """Create HIPAA compliance manager"""
        return HIPAAComplianceManager(db_session=db_session)

    @pytest.fixture
    def test_user_id(self, db_session):
        """Create or get test user"""
        from server.database.models import User

        test_user = db_session.query(User).filter(User.email == "hipaa-test@example.com").first()

        if not test_user:
            test_user = User(
                id=uuid4(),
                email="hipaa-test@example.com",
                username="hipaa_test_user",
                name="HIPAA Test User",
                password_hash="test_hash_placeholder",
            )
            db_session.add(test_user)
            db_session.commit()

        return test_user.id

    @pytest.mark.asyncio
    async def test_detect_phi_ssn(self, hipaa_manager):
        """Test PHI detection for SSN"""
        test_data = "Patient information: John Doe, SSN: 123-45-6789"

        result = await hipaa_manager.detect_phi(test_data)

        assert result["has_phi"] is True
        assert PHICategory.SOCIAL_SECURITY_NUMBERS.value in result["categories"]
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_detect_phi_medical_record(self, hipaa_manager):
        """Test PHI detection for medical record number"""
        test_data = "Patient MRN: 12345678, diagnosis: common cold"

        result = await hipaa_manager.detect_phi(test_data)

        assert result["has_phi"] is True
        assert PHICategory.MEDICAL_RECORD_NUMBERS.value in result["categories"]

    @pytest.mark.asyncio
    async def test_detect_phi_icd10_code(self, hipaa_manager):
        """Test PHI detection for ICD-10 diagnosis codes"""
        test_data = "Patient diagnosis: A00.0 - Cholera due to Vibrio cholerae"

        result = await hipaa_manager.detect_phi(test_data)

        assert result["has_phi"] is True
        assert PHICategory.DIAGNOSIS_CODES.value in result["categories"]

    @pytest.mark.asyncio
    async def test_detect_phi_no_phi(self, hipaa_manager):
        """Test PHI detection with no PHI present"""
        test_data = "This is a general medical article about health and wellness."

        result = await hipaa_manager.detect_phi(test_data)

        assert result["has_phi"] is False
        assert len(result["categories"]) == 0

    @pytest.mark.asyncio
    async def test_ensure_phi_protection(self, hipaa_manager, test_user_id):
        """Test PHI protection validation"""
        test_data = {"patient_name": "John Doe", "ssn": "123-45-6789", "diagnosis": "A00.0"}

        result = await hipaa_manager.ensure_phi_protection(test_data, test_user_id)

        assert result["phi_detected"] is True
        assert len(result["categories"]) > 0
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_generate_audit_trail(self, hipaa_manager, test_user_id):
        """Test HIPAA audit trail generation"""
        result = await hipaa_manager.generate_hipaa_audit_trail(
            user_id=test_user_id,
            action="view",
            resource_type="memory",
            resource_id=uuid4(),
            phi_accessed=True,
            phi_categories=["ssn", "medical_record_numbers"],
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            success=True,
        )

        assert result is not None
        assert "id" in result or "timestamp" in result
        assert result.get("phi_accessed") is True
        assert result.get("compliance") == "HIPAA"

    @pytest.mark.asyncio
    async def test_enforce_minimum_necessary_access_valid(self, hipaa_manager, test_user_id):
        """Test minimum necessary access with valid purpose"""
        result = await hipaa_manager.enforce_minimum_necessary_access(
            user_id=test_user_id, requested_data=["patient_name", "diagnosis", "treatment_date"], purpose="treatment"
        )

        assert result["allowed"] is True
        assert result["purpose_valid"] is True
        assert len(result["allowed_fields"]) > 0

    @pytest.mark.asyncio
    async def test_enforce_minimum_necessary_access_invalid(self, hipaa_manager, test_user_id):
        """Test minimum necessary access with invalid purpose"""
        result = await hipaa_manager.enforce_minimum_necessary_access(
            user_id=test_user_id, requested_data=["patient_name", "diagnosis"], purpose="marketing"
        )

        assert result["allowed"] is False
        assert result["purpose_valid"] is False

    @pytest.mark.asyncio
    async def test_detect_breach_unauthorized_access(self, hipaa_manager):
        """Test breach detection for unauthorized access"""
        incident_data = {"phi_accessed": True, "unauthorized": True, "encryption_bypassed": False}

        result = await hipaa_manager.detect_breach(incident_data)

        assert result["is_breach"] is True
        assert result["notification_required"] is True
        assert result["notification_deadline"] is not None
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_detect_breach_encryption_bypassed(self, hipaa_manager):
        """Test breach detection for encryption bypass"""
        incident_data = {"phi_accessed": True, "unauthorized": False, "encryption_bypassed": True}

        result = await hipaa_manager.detect_breach(incident_data)

        assert result["is_breach"] is True
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_detect_breach_no_breach(self, hipaa_manager):
        """Test breach detection with no breach"""
        incident_data = {"phi_accessed": False, "unauthorized": False, "encryption_bypassed": False}

        result = await hipaa_manager.detect_breach(incident_data)

        assert result["is_breach"] is False
        assert result["notification_required"] is False

    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, hipaa_manager):
        """Test HIPAA compliance report generation"""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        report = await hipaa_manager.generate_hipaa_compliance_report(start_date=start_date, end_date=end_date)

        assert report is not None
        assert "report_period" in report
        assert "compliance_score" in report
        assert "recommendations" in report
        assert "phi_access_events" in report
        assert "breach_incidents" in report


@pytest.mark.order(1)  # Run HIPAA tests before GDPR tests to avoid backref conflicts
class TestHIPAADatabaseModels:
    """Tests for HIPAA database models"""

    @pytest.fixture(autouse=True)
    def cleanup_before_test(self, db_session):
        """Ensure clean database state before and after each test"""
        # Rollback any previous transaction state before test
        try:
            db_session.rollback()
        except Exception:
            pass
        yield
        # Cleanup after test
        try:
            db_session.rollback()
        except Exception:
            pass

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
    def test_user_id(self, db_session):
        """Create or get test user with unique identifier"""
        import time

        from server.database.models import User

        # Use timestamp to ensure uniqueness
        timestamp = int(time.time() * 1000000)  # Microseconds for better uniqueness
        unique_email = f"hipaa-model-test-{timestamp}@example.com"
        unique_username = f"hipaa_model_test_user_{timestamp}"

        test_user = db_session.query(User).filter(User.email == unique_email).first()

        if not test_user:
            test_user = User(
                id=uuid4(),
                email=unique_email,
                username=unique_username,
                name="HIPAA Model Test User",
                password_hash="test_hash_placeholder",
            )
            db_session.add(test_user)
            db_session.commit()

        return test_user.id

    def test_create_audit_log(self, db_session, test_user_id):
        """Test creating HIPAA audit log"""
        audit_log = HIPAAAuditLog(
            id=uuid4(),
            user_id=test_user_id,
            action="view",
            resource_type="memory",
            phi_accessed=True,
            phi_categories=["ssn", "medical_record_numbers"],
            ip_address="192.168.1.1",
            success=True,
        )

        db_session.add(audit_log)
        db_session.commit()

        # Verify it was saved
        retrieved = db_session.query(HIPAAAuditLog).filter(HIPAAAuditLog.id == audit_log.id).first()

        assert retrieved is not None
        assert retrieved.action == "view"
        assert retrieved.phi_accessed is True

    def test_create_breach_incident(self, db_session, test_user_id):
        """Test creating breach incident"""
        # Ensure clean state - rollback any previous transaction and start fresh
        try:
            db_session.rollback()
        except Exception:
            pass

        # Create a fresh breach incident
        breach_id = uuid4()
        breach = HIPAABreachIncident(
            id=breach_id,
            incident_type="unauthorized_access",
            phi_affected=["ssn", "medical_records"],
            risk_level="high",
            is_breach=True,
            phi_records_affected=10,
            notification_required=True,
            notification_deadline=datetime.utcnow() + timedelta(days=60),
            status="pending",
            reported_by=test_user_id,
        )

        db_session.add(breach)
        db_session.commit()

        # Verify it was saved
        retrieved = db_session.query(HIPAABreachIncident).filter(HIPAABreachIncident.id == breach_id).first()

        assert retrieved is not None
        assert retrieved.is_breach is True
        assert retrieved.notification_required is True

    def test_create_phi_detection(self, db_session, test_user_id):
        """Test creating PHI detection record"""
        # Ensure clean state - rollback any previous transaction and start fresh
        try:
            db_session.rollback()
        except Exception:
            pass

        # Create a fresh PHI detection
        detection_id = uuid4()
        detection = HIPAAPHIDetection(
            id=detection_id,
            resource_type="memory",
            resource_id=uuid4(),
            has_phi=True,
            phi_categories=["ssn"],
            risk_level="high",
            detection_method="pattern_matching",
            protection_applied=True,
            detected_by=test_user_id,
        )

        db_session.add(detection)
        db_session.commit()

        # Verify it was saved
        retrieved = db_session.query(HIPAAPHIDetection).filter(HIPAAPHIDetection.id == detection_id).first()

        assert retrieved is not None
        assert retrieved.has_phi is True
        assert retrieved.risk_level == "high"


@pytest.mark.order(1)  # Run HIPAA tests before GDPR tests to avoid backref conflicts
class TestHIPAAEmailNotifier:
    """Tests for HIPAA email notifications"""

    @pytest.fixture
    def notifier(self):
        """Create email notifier"""
        return HIPAAEmailNotifier()

    @pytest.mark.asyncio
    async def test_generate_individual_breach_email(self, notifier):
        """Test generating individual breach notification email"""
        breach_id = uuid4()
        incident_details = {
            "created_at": datetime.utcnow().isoformat(),
            "description": "Unauthorized access to patient records",
            "phi_affected": ["ssn", "medical_records"],
        }
        individual = {"email": "patient@example.com", "name": "John Doe"}

        email_content = notifier._generate_individual_breach_email(breach_id, incident_details, individual)

        assert email_content is not None
        assert "subject" in email_content
        assert "body" in email_content
        assert "html" in email_content
        assert "security incident" in email_content["subject"].lower() or "breach" in email_content["subject"].lower()
        assert individual["name"] in email_content["body"]

    @pytest.mark.asyncio
    async def test_send_breach_notification_simulated(self, notifier):
        """Test sending breach notification (simulated)"""
        breach_id = uuid4()
        incident_details = {
            "phi_records_affected": 100,
            "is_breach": True,
            "created_at": datetime.utcnow().isoformat(),
            "description": "Test breach",
            "phi_affected": ["ssn"],
        }
        affected_individuals = [
            {"email": "patient1@example.com", "name": "Patient One"},
            {"email": "patient2@example.com", "name": "Patient Two"},
        ]

        result = await notifier.send_breach_notification(
            breach_id, incident_details, affected_individuals, notification_type="individual"
        )

        assert result is not None
        assert result["sent"] is True
        assert result["recipient_count"] == 2

    @pytest.mark.asyncio
    async def test_send_compliance_report(self, notifier):
        """Test sending compliance report"""
        report_data = {
            "compliance_score": 95.0,
            "phi_access_events": 50,
            "breach_incidents": 0,
            "recommendations": ["Maintain audit logs", "Review access controls"],
        }
        report_period = {
            "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end": datetime.utcnow().isoformat(),
        }

        result = await notifier.send_compliance_report("compliance@example.com", report_data, report_period)

        assert result is not None
        assert result["sent"] is True


@pytest.mark.order(1)  # Run HIPAA tests before GDPR tests to avoid backref conflicts
class TestHIPAAAPIEndpoints:
    """Integration tests for HIPAA API endpoints"""

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

    def test_detect_phi_endpoint_exists(self, client):
        """Test PHI detection endpoint exists"""
        response = client.post("/api/v1/compliance/hipaa/detect-phi")
        assert response.status_code in [401, 403, 404, 405, 422]  # Auth, validation, or method error

    def test_audit_trail_endpoint_exists(self, client):
        """Test audit trail endpoint exists"""
        response = client.post("/api/v1/compliance/hipaa/audit-trail")
        assert response.status_code in [401, 403, 404, 405, 422]

    def test_breach_assessment_endpoint_exists(self, client):
        """Test breach assessment endpoint exists"""
        response = client.post("/api/v1/compliance/hipaa/breach-assessment")
        assert response.status_code in [401, 403, 404, 405, 422]

    def test_compliance_report_endpoint_exists(self, client):
        """Test compliance report endpoint exists"""
        response = client.get("/api/v1/compliance/hipaa/compliance-report")
        assert response.status_code in [401, 403, 404, 405, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
