#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

import structlog
from redis_client import RedisClient, redis_client

from .multipart_models import MultipartUploadSession

logger = structlog.get_logger(__name__)


class MultipartUploadSessionStore:
    """Redis-backed session persistence for multipart uploads."""

    def __init__(self, client: Optional[RedisClient] = None, ttl_seconds: int = 86400) -> None:
        self._client = client or redis_client
        self._ttl_seconds = ttl_seconds
        self._key_prefix = "uploads:multipart:"

    async def _redis(self):
        if not self._client.is_connected:
            await self._client.connect()
        if not self._client.redis:
            raise RuntimeError("Redis client unavailable")
        return self._client.redis

    def _key(self, session_id: str) -> str:
        return f"{self._key_prefix}{session_id}"

    async def save(self, session: MultipartUploadSession) -> None:
        redis = await self._redis()
        key = self._key(session.session_id)
        session.refresh(ttl_seconds=self._ttl_seconds)
        payload = json.dumps(session.to_dict())
        await redis.setex(key, self._ttl_seconds, payload)

    async def get(self, session_id: str) -> Optional[MultipartUploadSession]:
        redis = await self._redis()
        data = await redis.get(self._key(session_id))
        if not data:
            return None
        try:
            decoded = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("Multipart session payload corrupted", session_id=session_id)
            await redis.delete(self._key(session_id))
            return None
        return MultipartUploadSession.from_dict(decoded)

    async def delete(self, session_id: str) -> None:
        redis = await self._redis()
        await redis.delete(self._key(session_id))

    async def refresh(self, session_id: str) -> None:
        redis = await self._redis()
        await redis.expire(self._key(session_id), self._ttl_seconds)


class InMemoryMultipartUploadStore(MultipartUploadSessionStore):
    """In-memory store primarily used for unit tests."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[MultipartUploadSession, datetime]] = {}
        self._ttl_seconds = 86400

    async def save(self, session: MultipartUploadSession) -> None:  # type: ignore[override]
        session.refresh(ttl_seconds=self._ttl_seconds)
        self._store[session.session_id] = (session, datetime.utcnow() + timedelta(seconds=self._ttl_seconds))

    async def get(self, session_id: str) -> Optional[MultipartUploadSession]:  # type: ignore[override]
        record = self._store.get(session_id)
        if not record:
            return None
        session, expires = record
        if datetime.utcnow() > expires:
            del self._store[session_id]
            return None
        return session

    async def delete(self, session_id: str) -> None:  # type: ignore[override]
        self._store.pop(session_id, None)

    async def refresh(self, session_id: str) -> None:  # type: ignore[override]
        if session_id in self._store:
            session, _ = self._store[session_id]
            self._store[session_id] = (session, datetime.utcnow() + timedelta(seconds=self._ttl_seconds))
