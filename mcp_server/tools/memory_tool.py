async def mcp_memory_write(payload):
    return {"status": "ok", "payload": payload}


async def mcp_memory_query(payload):
    return {"results": []}


async def mcp_memory_share(payload):
    return {"status": "shared", "payload": payload}
