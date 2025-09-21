from __future__ import annotations


class FakePart:
    def __init__(self, headers: dict, chunks: list[bytes]):
        self.headers = headers
        self._chunks = chunks

    async def stream(self):
        for c in self._chunks:
            yield c


class FakeStream:
    def __init__(self, request):
        self.__request__ = request


class FakeRequest:
    def __init__(self, parts: list[FakePart], headers: dict | None = None):
        self.headers = headers or {}
        self._parts = parts

    def stream(self):
        # Return a fake stream object with request reference
        return FakeStream(self)
