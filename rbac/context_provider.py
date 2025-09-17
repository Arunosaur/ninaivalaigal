from __future__ import annotations
from typing import Callable
from fastapi import Request, HTTPException, status

def install_subject_ctx_provider(app, provider: Callable):
    app.state.subject_ctx_provider = provider

def get_subject_ctx_dep(app):
    def _dep(request: Request):
        prov = getattr(app.state, "subject_ctx_provider", None)
        if prov is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="subject_ctx_provider not installed")
        return prov(request)
    return _dep
