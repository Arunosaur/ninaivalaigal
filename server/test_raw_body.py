from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/rawtest")
async def raw_test(request: Request):
    body = await request.body()
    return {"length": len(body)}
