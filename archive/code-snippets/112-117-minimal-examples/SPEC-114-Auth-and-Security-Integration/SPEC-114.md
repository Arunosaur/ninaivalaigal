# SPEC-114: Auth & Security Integration
**Project:** Medhasys / Ninaivalaigal
**Status:** Draft
**Owner:** Platform & Security
**Last Updated:** 2025-10-11

### auth_router.py
```py
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/auth")

@router.get("/login")
def login():
    return RedirectResponse(url="/auth/callback")

@router.get("/callback")
def callback(request: Request):
    return {"message": "Callback received"}

@router.post("/refresh")
def refresh():
    return {"access_token": "new_token"}
```
