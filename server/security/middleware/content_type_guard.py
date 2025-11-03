#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Content-Type and payload size guard middleware for ASGI apps."""

from __future__ import annotations

import typing as t

from starlette.types import ASGIApp, Message, Receive, Scope, Send

HttpScope = Scope


class ContentTypeGuardMiddleware:
    """Reject disallowed content types and guard against oversized request bodies."""

    def __init__(
        self,
        app: ASGIApp,
        allowed_prefixes: t.Iterable[str] | None = None,
        max_body_bytes: int = 10 * 1024 * 1024,
        reject_disallowed: bool = True,
    ) -> None:
        self.app = app
        self.allowed_prefixes = tuple(allowed_prefixes or ("text/", "application/json"))
        self.max_body_bytes = max_body_bytes
        self.reject_disallowed = reject_disallowed

    async def __call__(self, scope: HttpScope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        content_type = headers.get("content-type", "")

        if self.reject_disallowed and not self._is_allowed_type(content_type):
            await self._reject(send, 415, "Unsupported Media Type")
            await self._drain_body(receive)
            return

        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    await self._reject(send, 413, "Payload Too Large")
                    await self._drain_body(receive)
                    return
            except ValueError:
                # Ignore malformed header; fall back to streaming guard.
                pass

        total_bytes = 0
        max_bytes = self.max_body_bytes

        async def guarded_receive() -> Message:
            nonlocal total_bytes
            message = await receive()

            if message["type"] != "http.request":
                return message

            body = message.get("body", b"") or b""
            total_bytes += len(body)

            if max_bytes > 0 and total_bytes > max_bytes:
                # Stop request processing by returning empty body and signalling end.
                return {"type": "http.request", "body": b"", "more_body": False}

            return message

        await self.app(scope, guarded_receive, send)

    def _is_allowed_type(self, content_type: str) -> bool:
        if not content_type:
            return True
        return any(content_type.startswith(prefix) for prefix in self.allowed_prefixes)

    async def _reject(self, send: Send, status: int, reason: str) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [(b"content-type", b"text/plain; charset=utf-8")],
            }
        )
        await send({"type": "http.response.body", "body": reason.encode("utf-8"), "more_body": False})

    async def _drain_body(self, receive: Receive) -> None:
        while True:
            message = await receive()
            if message.get("type") != "http.request" or not message.get("more_body"):
                break
