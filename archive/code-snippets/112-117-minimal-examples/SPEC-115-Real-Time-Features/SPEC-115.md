# SPEC-115: Real-Time Features (WebSockets & SSE)
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Platform Engineering
**Last Updated:** 2025-10-11

### realtime.py
```py
from fastapi import FastAPI, WebSocket
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("Connected")
    while True:
        data = await ws.receive_text()
        await ws.send_text(f"Echo: {data}")

@app.get("/sse")
async def sse_endpoint():
    async def event_stream():
        for i in range(3):
            yield f"data: event {i}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```
