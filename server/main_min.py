"""main min module."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/ping")
async def ping():
    """Health check endpoint returning pong response."""
    return {"msg": "pong"}
