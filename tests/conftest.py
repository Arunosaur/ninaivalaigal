import pytest

# We monkeypatch starlette.formparsers.MultiPartParser used by the adapter
# to avoid depending on Starlette internals and to feed our fake parts.


class FakeMultiPartParser:
    def __init__(self, headers=None, stream=None):
        # headers/stream are ignored for tests
        self._stream = stream

    async def parse(self):
        # The adapter passes request.stream(); get request from stream
        if hasattr(self._stream, "__request__"):
            req = self._stream.__request__
        else:
            # Try to get request from stream coroutine
            req = getattr(self._stream, "__request__", None)

        if req is None:
            return

        parts = getattr(req, "_parts", [])
        for p in parts:
            yield p


@pytest.fixture(autouse=True)
def patch_multipart_parser(monkeypatch):
    # Patch where the adapter imports it
    monkeypatch.setenv("STARLETTE_FAKE", "1")
    import server.security.multipart.starlette_adapter as adapter

    monkeypatch.setattr(adapter, "MultiPartParser", FakeMultiPartParser, raising=True)
    yield
