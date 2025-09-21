from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient


def build_app():
    app = FastAPI()

    # Minimal mock auth
    @app.middleware("http")
    async def inject_user(request, call_next):
        # Simulate unauthenticated when header missing
        auth = request.headers.get("Authorization")
        if auth == "Bearer valid":
            request.state.user = {"user_id": "u1", "roles": ["reader"]}
        elif auth == "Bearer editor":
            request.state.user = {"user_id": "u1", "roles": ["editor"]}
        else:
            request.state.user = None
        return await call_next(request)

    def require_permission(perm: str):
        def dep(request):
            if not getattr(request.state, "user", None):
                raise HTTPException(status_code=401, detail="missing/invalid token")
            if perm == "write" and "editor" not in request.state.user["roles"]:
                raise HTTPException(status_code=403, detail="insufficient role")

        return dep

    @app.get("/read", dependencies=[Depends(require_permission("read"))])
    def read_ok():
        return {"ok": True}

    @app.post("/write", dependencies=[Depends(require_permission("write"))])
    def write_ok():
        return {"ok": True}

    return app


def test_401_vs_403_semantics():
    app = build_app()
    c = TestClient(app)

    # Unauth -> 401 on both
    assert c.get("/read").status_code == 401
    assert c.post("/write").status_code == 401

    # Auth but insufficient role -> 403 on write
    assert c.get("/read", headers={"Authorization": "Bearer valid"}).status_code in (
        200,
        204,
    )
    assert (
        c.post("/write", headers={"Authorization": "Bearer valid"}).status_code == 403
    )

    # Editor -> 200 on write
    assert c.post("/write", headers={"Authorization": "Bearer editor"}).status_code in (
        200,
        204,
    )
