#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Usage Metering Middleware
# Developer D - January 2025
#
# BILL-002: FastAPI middleware for automatic usage tracking

"""
FastAPI middleware for automatic usage tracking.

Captures usage events from API requests:
- Storage: Memory/context uploads
- Retrievals: Memory recall operations
- Tokens: Text processing/embedding operations
"""

import time
import uuid
from decimal import Decimal
from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from server.billing.models import BillingAccount, BillingPeriod
from server.billing.usage_metering import (
    AccountType,
    UsageMeteringService,
    calculate_storage_gb_month,
    calculate_tokens_from_text,
    create_idempotency_key,
)
from server.database import get_db


class UsageMeteringMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic usage tracking.

    Features:
    - Automatic usage capture from API requests
    - Performance optimized (<5ms overhead)
    - Idempotent logging
    - Error handling (failures don't block requests)
    """

    def __init__(
        self,
        app: ASGIApp,
        enabled: bool = True,
        track_storage: bool = True,
        track_retrievals: bool = True,
        track_tokens: bool = True,
    ):
        """
        Initialize usage metering middleware.

        Args:
            app: FastAPI application
            enabled: Enable/disable middleware
            track_storage: Track storage usage
            track_retrievals: Track retrieval usage
            track_tokens: Track token usage
        """
        super().__init__(app)
        self.enabled = enabled
        self.track_storage = track_storage
        self.track_retrievals = track_retrievals
        self.track_tokens = track_tokens

        # Endpoints that track storage
        self.storage_endpoints = {
            "/api/v1/memory",
            "/api/v1/context",
            "/api/v1/upload",
        }

        # Endpoints that track retrievals
        self.retrieval_endpoints = {
            "/api/v1/memory/search",
            "/api/v1/memory/recall",
            "/api/v1/context/retrieve",
        }

        # Endpoints that track tokens
        self.token_endpoints = {
            "/api/v1/text/process",
            "/api/v1/embedding",
            "/api/v1/ai/chat",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and track usage.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response
        """
        if not self.enabled:
            return await call_next(request)

        # Track request start time for performance
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000

        # Track usage asynchronously (don't block response)
        try:
            await self._track_usage(request, response, duration_ms)
        except Exception as e:
            # Log error but don't fail request
            # In production, use proper logging
            print(f"Usage tracking error: {e}")  # noqa: T201

        return response

    async def _track_usage(self, request: Request, response: Response, duration_ms: float):
        """
        Track usage based on request.

        Args:
            request: FastAPI request
            response: Response object
            duration_ms: Request duration in milliseconds
        """
        # Skip if not successful
        if response.status_code >= 400:
            return

        # Get billing account from request
        billing_account = await self._get_billing_account(request)
        if not billing_account:
            return

        # Get current billing period
        # Use dependency injection for database session
        db = next(get_db())

        try:
            metering_service = UsageMeteringService(db)
            billing_period = metering_service.get_current_billing_period(billing_account.id)

            if not billing_period:
                # Create billing period if doesn't exist
                from datetime import datetime, timedelta

                now = datetime.utcnow()
                billing_period = BillingPeriod(
                    billing_account_id=billing_account.id,
                    period_start=now.replace(day=1),
                    period_end=(now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
                    status="active",
                )
                db.add(billing_period)
                db.commit()
                db.refresh(billing_period)

            path = request.url.path
            method = request.method

            # Track storage usage
            if self.track_storage and self._is_storage_endpoint(path, method):
                await self._track_storage_usage(
                    metering_service, billing_account.id, billing_period.id, request, response
                )

            # Track retrieval usage
            if self.track_retrievals and self._is_retrieval_endpoint(path, method):
                await self._track_retrieval_usage(
                    metering_service, billing_account.id, billing_period.id, request, response
                )

            # Track token usage
            if self.track_tokens and self._is_token_endpoint(path, method):
                await self._track_token_usage(
                    metering_service, billing_account.id, billing_period.id, request, response
                )
        finally:
            db.close()

    async def _get_billing_account(self, request: Request) -> Optional[BillingAccount]:
        """
        Get billing account from request.

        Tries to extract from:
        1. User context (current_user)
        2. Team context (team_id in path/query)
        3. Organization context (org_id in path/query)
        """
        # Try to get from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        if not user:
            return None

        # Use dependency injection for database session
        db = next(get_db())

        try:
            from server.billing.models import AccountType
            from server.billing.usage_metering import UsageMeteringService

            metering_service = UsageMeteringService(db)

            # Try team context first
            team_id = request.path_params.get("team_id") or request.query_params.get("team_id")
            if team_id:
                try:
                    team_uuid = uuid.UUID(team_id) if isinstance(team_id, str) else team_id
                    account = metering_service.get_billing_account(AccountType.TEAM, team_uuid)
                    if account:
                        return account
                except (ValueError, TypeError):
                    pass

            # Try organization context
            org_id = request.path_params.get("org_id") or request.query_params.get("org_id")
            if org_id:
                try:
                    org_uuid = uuid.UUID(org_id) if isinstance(org_id, str) else org_id
                    account = metering_service.get_billing_account(AccountType.ORGANIZATION, org_uuid)
                    if account:
                        return account
                except (ValueError, TypeError):
                    pass

            # Fallback to user account
            account = metering_service.get_billing_account(AccountType.USER, user.id)
            return account
        finally:
            db.close()

    def _is_storage_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint tracks storage"""
        if method not in ["POST", "PUT"]:
            return False
        return any(path.startswith(endpoint) for endpoint in self.storage_endpoints)

    def _is_retrieval_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint tracks retrievals"""
        if method != "GET":
            return False
        return any(path.startswith(endpoint) for endpoint in self.retrieval_endpoints)

    def _is_token_endpoint(self, path: str, method: str) -> bool:
        """Check if endpoint tracks tokens"""
        return any(path.startswith(endpoint) for endpoint in self.token_endpoints)

    async def _track_storage_usage(
        self,
        metering_service: UsageMeteringService,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        request: Request,
        response: Response,
    ):
        """Track storage usage from request"""
        try:
            # Get content length from request
            content_length = request.headers.get("content-length")
            if not content_length:
                return

            file_size_bytes = int(content_length)
            storage_gb = calculate_storage_gb_month(file_size_bytes)

            # Create idempotency key
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            idempotency_key = create_idempotency_key(billing_account_id, "storage_upload", request_id)

            metering_service.record_storage_usage(
                billing_account_id=billing_account_id,
                billing_period_id=billing_period_id,
                storage_gb=storage_gb,
                metadata={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            # Log but don't fail
            print(f"Storage tracking error: {e}")  # noqa: T201

    async def _track_retrieval_usage(
        self,
        metering_service: UsageMeteringService,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        request: Request,
        response: Response,
    ):
        """Track retrieval usage from request"""
        try:
            # Count as 1 retrieval operation
            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            idempotency_key = create_idempotency_key(billing_account_id, "retrieval", request_id)

            metering_service.record_retrieval_usage(
                billing_account_id=billing_account_id,
                billing_period_id=billing_period_id,
                retrieval_count=1,
                metadata={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            print(f"Retrieval tracking error: {e}")  # noqa: T201

    async def _track_token_usage(
        self,
        metering_service: UsageMeteringService,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        request: Request,
        response: Response,
    ):
        """Track token usage from request"""
        try:
            # Try to get request body
            body = await request.body()
            if not body:
                return

            # Estimate tokens from body
            text = body.decode("utf-8", errors="ignore")
            token_count = calculate_tokens_from_text(text)

            if token_count == 0:
                return

            request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
            idempotency_key = create_idempotency_key(billing_account_id, "token_processing", request_id)

            metering_service.record_token_usage(
                billing_account_id=billing_account_id,
                billing_period_id=billing_period_id,
                token_count=token_count,
                metadata={
                    "path": request.url.path,
                    "method": request.method,
                    "request_id": request_id,
                },
                idempotency_key=idempotency_key,
            )
        except Exception as e:
            print(f"Token tracking error: {e}")  # noqa: T201
