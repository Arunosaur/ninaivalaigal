# SPDX-License-Identifier: Proprietary
"""Integration tests that hit the running Core API with PgBouncer-backed PostgreSQL.

These exercises the real signup/login endpoints while asserting database state
through the PgBouncer transaction pool configured in `.env.dev`.
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Callable, Dict, Optional

import pytest
import requests
from dotenv import load_dotenv

from tests.config import CORE_API_BASE_URL

try:  # psycopg is optional for unit-only workflows
    import psycopg
    from psycopg.rows import dict_row
except ModuleNotFoundError:  # pragma: no cover
    pytest.skip("psycopg package unavailable", allow_module_level=True)


_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env.dev", override=False)

_CORE_API_DIR = _REPO_ROOT / "services" / "core-api"
if _CORE_API_DIR.exists():
    core_api_path = str(_CORE_API_DIR)
    if core_api_path not in sys.path:
        sys.path.insert(0, core_api_path)

try:
    from utils import password as password_utils  # type: ignore # noqa: E402
except ModuleNotFoundError as exc:  # pragma: no cover
    pytest.skip(f"Core API utilities unavailable: {exc}", allow_module_level=True)


def _resolve_database_url() -> Optional[str]:
    """Build a connection string that routes through PgBouncer transaction mode."""

    direct_url = os.getenv("DATABASE_URL") or os.getenv("NINAIVALAIGAL_DATABASE_URL")
    if direct_url:
        return direct_url

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("PGBOUNCER_TX_PORT") or os.getenv("PGBOUNCER_PORT") or "6432"
    user = os.getenv("NINA_DB_USER") or os.getenv("POSTGRES_USER")
    password = os.getenv("NINA_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB")

    if not all([user, password, database]):
        return None

    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


_DATABASE_URL = _resolve_database_url()
if not _DATABASE_URL:
    pytest.skip("PgBouncer DATABASE_URL details not configured in environment", allow_module_level=True)


@pytest.fixture(scope="module")
def _db_checker() -> str:
    """Ensure the PgBouncer connection is reachable before running tests."""

    try:
        with psycopg.connect(_DATABASE_URL) as conn:  # type: ignore[arg-type]
            conn.execute("SELECT 1")
    except Exception as exc:  # pragma: no cover - environment specific
        pytest.skip(f"PgBouncer database unreachable: {exc}")
    return _DATABASE_URL


@pytest.fixture
def fetch_user_from_db(_db_checker: str) -> Callable[[str], Optional[Dict[str, object]]]:
    """Return helper that fetches a user row by email via PgBouncer."""

    def _fetch(email: str) -> Optional[Dict[str, object]]:
        with psycopg.connect(_db_checker, autocommit=True) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT id, email, password_hash, last_login, created_at FROM users WHERE email = %s",
                    (email,),
                )
                return cur.fetchone()

    return _fetch


def _api_post(path: str, payload: Dict[str, object]) -> requests.Response:
    url = f"{CORE_API_BASE_URL.rstrip('/')}{path}"
    try:
        response = requests.post(url, json=payload, timeout=10)
    except requests.exceptions.ConnectionError as exc:  # pragma: no cover - environment specific
        pytest.skip(f"Core API not reachable at {url}: {exc}")
    except requests.exceptions.Timeout as exc:  # pragma: no cover
        pytest.skip(f"Core API timed out at {url}: {exc}")
    return response


@pytest.mark.integration
class TestAuthPgBouncer:
    def test_signup_persists_bcrypt_hash(self, fetch_user_from_db: Callable[[str], Optional[Dict[str, object]]]):
        email = f"pgbouncer-user-{uuid.uuid4().hex[:8]}@test.com"
        password = "PgBouncerPass123!"  # pragma: allowlist secret

        signup_response = _api_post(
            "/auth/signup/individual",
            {"email": email, "password": password, "name": "PgBouncer User"},  # pragma: allowlist secret
        )

        assert signup_response.status_code == 201, signup_response.text
        user_row = fetch_user_from_db(email)
        assert user_row is not None, "User record not found via PgBouncer"

        stored_hash = user_row["password_hash"]
        assert isinstance(stored_hash, str)
        assert stored_hash != password
        assert password_utils.verify_password(password, stored_hash)

    def test_login_updates_last_login(self, fetch_user_from_db: Callable[[str], Optional[Dict[str, object]]]):
        email = f"pgbouncer-login-{uuid.uuid4().hex[:8]}@test.com"
        password = "PgBouncerLogin123!"  # pragma: allowlist secret

        signup_response = _api_post(
            "/auth/signup/individual",
            {"email": email, "password": password, "name": "PgBouncer Login"},  # pragma: allowlist secret
        )
        assert signup_response.status_code == 201, signup_response.text

        before = fetch_user_from_db(email)
        assert before is not None
        assert before["last_login"] is None

        login_response = _api_post(
            "/auth/login",
            {"email": email, "password": password},  # pragma: allowlist secret
        )
        assert login_response.status_code == 200, login_response.text

        after = fetch_user_from_db(email)
        assert after is not None
        assert after["last_login"] is not None
        assert password_utils.verify_password(password, after["password_hash"])
