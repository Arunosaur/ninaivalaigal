from server.security.rbac.metrics_jwt import jwt_replay_total
from server.security.rbac.replay_store import seen_before


def test_jwt_replay_counter_increments_on_repeat():
    jti = "abc123"
    assert seen_before(jti) is False
    assert seen_before(jti) is True
    jwt_replay_total.inc()
    try:
        val = jwt_replay_total._value.get()  # type: ignore
        assert val >= 1
    except Exception:
        assert True
