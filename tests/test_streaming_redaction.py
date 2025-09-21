import asyncio

from server.security.middleware.streaming_redaction import StreamingRedactor


def simple_detector(text: str) -> str:
    return text.replace("SECRET_TOKEN", "<MASK>")


async def agen(chunks):
    for c in chunks:
        yield c


def test_streaming_redactor_across_boundaries():
    sr = StreamingRedactor(detector_fn=simple_detector, overlap=6)
    chunks = [b"hello SECR", b"ET_TOKEN world"]
    out = asyncio.get_event_loop().run_until_complete(
        _collect(sr.redact_stream(agen(chunks)))
    )
    assert b"<MASK>" in b"".join(out)


async def _collect(ait):
    result = []
    async for x in ait:
        result.append(x)
    return result
