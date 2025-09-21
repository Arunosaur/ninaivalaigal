from __future__ import annotations

import re
from typing import Any

BLOCKLIST_FIELDS = {
    "authorization",
    "auth",
    "access_token",
    "refresh_token",
    "password",
    "secret",
    "api_key",
    "token",
    "set-cookie",
    "cookie",
    "client_secret",
    "private_key",
    "pem",
    "prompt",
    "content",
}

GENERIC_TOKEN = re.compile(r"\b[A-Za-z0-9_\-]{24,}\b")


def _mask_value(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (int, float, bool)):
        return v
    s = str(v)
    if len(s) <= 8:
        return "<MASKED>"
    return f"{s[:2]}…<MASKED>…{s[-2:]}"


def _scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: (
                "<BLOCKED>"
                if k.lower().replace("-", "_") in BLOCKLIST_FIELDS
                else _scrub(v)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    if isinstance(obj, str):
        if GENERIC_TOKEN.search(obj):
            return GENERIC_TOKEN.sub("<MASKED_TOKEN>", obj)
        return obj
    return obj


def safe_log_dict(d: dict[str, Any]) -> dict[str, Any]:
    try:
        return _scrub(dict(d))
    except Exception:
        return {"_error": "log_scrub_failed"}
