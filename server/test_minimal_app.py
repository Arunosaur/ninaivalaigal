#!/usr/bin/env python3
"""
Minimal FastAPI app to test POST endpoint functionality
This will help us isolate if the issue is in our main app or FastAPI itself
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel

# Create minimal app
app = FastAPI(title="Minimal Test App")


class TestLogin(BaseModel):
    email: str
    password: str


@app.get("/")
async def root():
    return {"message": "Minimal app working"}


@app.post("/test-post-simple")
async def test_post_simple():
    print("🔥 MINIMAL: Simple POST reached")
    return {"status": "ok", "message": "Simple POST works"}


@app.post("/test-post-body")
async def test_post_body(data: dict):
    print(f"🔥 MINIMAL: Dict body POST reached: {data}")
    return {"status": "ok", "received": data}


@app.post("/test-post-model")
async def test_post_model(login: TestLogin):
    print(f"🔥 MINIMAL: Model POST reached: {login.email}")
    return {"status": "ok", "email": login.email}


@app.post("/test-post-raw")
async def test_post_raw(request: Request):
    print("🔥 MINIMAL: Raw POST reached")
    body = await request.json()
    print(f"🔥 MINIMAL: Raw body: {body}")
    return {"status": "ok", "body": body}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting minimal test app on port 8888...")
    uvicorn.run(
        "test_minimal_app:app",
        host="0.0.0.0",
        port=8888,
        reload=True,
        log_level="debug",
    )
