# SPDX-License-Identifier: Proprietary
"""Unit tests covering signup and login flows for password handling."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

CORE_API_DIR = Path(__file__).resolve().parents[2]
core_api_str = str(CORE_API_DIR)
if core_api_str not in sys.path:
    sys.path.insert(0, core_api_str)

try:  # pragma: no cover - ensure optional deps present
    # Import local auth.py using importlib to avoid shared/contracts/auth conflict
    import importlib.util
    import sys as _sys

    _auth_spec = importlib.util.spec_from_file_location("local_auth_test", CORE_API_DIR / "auth.py")
    auth = importlib.util.module_from_spec(_auth_spec)
    _sys.modules["local_auth_test"] = auth
    _auth_spec.loader.exec_module(auth)

    from utils import password as password_utils  # noqa: E402
except (ModuleNotFoundError, AttributeError) as exc:  # pragma: no cover
    pytest.skip(f"Auth modules unavailable: {exc}", allow_module_level=True)


class _FakeSession:
    """Minimal SQLAlchemy-like session used for auth tests."""

    def __init__(self, user: SimpleNamespace | None = None) -> None:
        self._user = user
        self.closed = False
        self.rolled_back = False
        self.committed = False

    # ORM query shim ---------------------------------------------------------------------------------
    class _Query:
        def __init__(self, user: SimpleNamespace | None) -> None:
            self._user = user

        def filter_by(self, **_: object) -> _FakeSession._Query:  # type: ignore[name-defined]
            return self

        def first(self) -> SimpleNamespace | None:
            return self._user

    def query(self, *_: object) -> _Query:
        return self._Query(self._user)

    # Session book-keeping --------------------------------------------------------------------------
    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class _FakeDB:
    def __init__(self, user: SimpleNamespace | None = None) -> None:
        self._session = _FakeSession(user)
        self.created_payload: dict[str, object] | None = None
        self.requested_email: str | None = None

    def get_session(self) -> _FakeSession:
        return self._session

    def get_user_by_email(self, email: str):
        self.requested_email = email
        return None

    def create_user(self, **payload: object):
        self.created_payload = payload
        return SimpleNamespace(
            id=uuid4(),
            email=payload.get("email"),
            name=payload.get("name"),
            account_type=payload.get("account_type", "individual"),
            personal_contexts_limit=payload.get("personal_contexts_limit"),
            email_verified=False,
        )


@pytest.mark.usefixtures("_ensure_jwt_secret")
class TestSignupFlow:
    @pytest.fixture(autouse=True)
    def _reset_get_db(self, monkeypatch: pytest.MonkeyPatch):
        fake_db = _FakeDB()
        monkeypatch.setattr(auth, "get_db", lambda: fake_db)
        self.fake_db = fake_db

    def test_signup_hashes_password(self):
        signup = auth.IndividualUserSignup(
            email="user@example.com",
            password="PlainPass123!",  # pragma: allowlist secret
            full_name="Test User",
        )

        result = auth.create_individual_user(signup)
        assert result["user_id"]
        assert self.fake_db.requested_email == signup.email
        assert self.fake_db.created_payload is not None
        stored_hash = self.fake_db.created_payload["password_hash"]  # pragma: allowlist secret
        assert isinstance(stored_hash, str)
        assert stored_hash != signup.password
        assert password_utils.verify_password(signup.password, stored_hash)


@pytest.mark.usefixtures("_ensure_jwt_secret")
class TestAuthenticateUser:
    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch: pytest.MonkeyPatch):
        password = "CorrectPass123!"  # pragma: allowlist secret
        self.user = SimpleNamespace(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_utils.hash_password(password),  # pragma: allowlist secret
            is_active=True,
            name="Person",
            account_type="individual",
            role="user",
            email_verified=True,
            personal_contexts_limit=5,
            is_system_admin=False,
            last_login=None,
        )
        fake_db = _FakeDB(user=self.user)
        monkeypatch.setattr(auth, "get_db", lambda: fake_db)
        monkeypatch.setattr(
            auth, "get_user_roles_for_token", lambda *_: {"roles": {"global": "MEMBER"}, "teams": {}, "org_id": None}
        )
        self.fake_db = fake_db
        self.correct_password = password

    def test_authenticate_user_returns_payload_when_password_matches(self):
        result = auth.authenticate_user(self.user.email, self.correct_password)
        assert result is not None
        assert result["email"] == self.user.email
        assert result["role"] == "user"
        assert "jwt_token" in result
        assert self.fake_db._session.committed is True
        assert self.user.last_login is not None

    def test_authenticate_user_returns_none_for_wrong_password(self):
        result = auth.authenticate_user(self.user.email, "WrongPassword!")
        assert result is None

    def test_authenticate_user_returns_none_when_user_missing(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(self.fake_db, "_session", _FakeSession(user=None))
        result = auth.authenticate_user(self.user.email, self.correct_password)
        assert result is None


@pytest.fixture
def _ensure_jwt_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NINAIVALAIGAL_JWT_SECRET", "test-secret")
    monkeypatch.setenv("NINAIVALAIGAL_JWT_EXPIRATION_HOURS", "24")
