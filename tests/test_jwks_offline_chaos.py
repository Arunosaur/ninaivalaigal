import pytest


@pytest.mark.parametrize("mode", ["jwks"])
def test_jwks_offline_graceful_degradation(monkeypatch, mode):
    # Simulate JWKS mode and offline URL
    monkeypatch.setenv(
        "NINAI_JWKS_URL", "https://127.0.0.1:65533/.well-known/jwks.json"
    )
    monkeypatch.setenv("NINAI_ALLOWED_ALGS", "RS256")
    monkeypatch.setenv(
        "NINAI_NEGATIVE_KID_TTL", "300"
    )  # cache bad kid to prevent thundering herd

    # Your resolver should fail fast, apply backoff, and NOT crash the app.
    # Replace with a call into your JWT resolver if exposed as a function.
    # This is a placeholder assertion to be replaced with project call.
    # Example:
    #   ok, err = resolve_token("Bearer <badrs256token>")
    #   assert ok is False
    #   assert "jwks" in err.lower()
    assert True
