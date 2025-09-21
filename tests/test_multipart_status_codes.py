from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.testclient import TestClient


def build_upload_app():
    app = FastAPI()

    @app.post("/upload-text")
    async def upload_text(file: UploadFile = File(...)):
        # Simulate validation pipeline decisions:
        if file.content_type not in ("text/plain", "application/json"):
            raise HTTPException(status_code=415, detail="unsupported media type")
        data = await file.read()
        if len(data) > 1024 * 1024:
            raise HTTPException(status_code=413, detail="too large")
        return {"ok": True}

    return app


def test_unsupported_media_type_415():
    app = build_upload_app()
    c = TestClient(app)
    data = {"file": ("x.bin", b"\x00\x01", "application/octet-stream")}
    r = c.post("/upload-text", files=data)
    assert r.status_code == 415


def test_payload_too_large_413():
    app = build_upload_app()
    c = TestClient(app)
    big = b"a" * (1024 * 1024 + 1)
    data = {"file": ("x.txt", big, "text/plain")}
    r = c.post("/upload-text", files=data)
    assert r.status_code == 413


def test_malformed_400():
    app = build_upload_app()
    c = TestClient(app)
    # No file -> 400
    r = c.post("/upload-text", files={})
    assert r.status_code in (400, 422)
