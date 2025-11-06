#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Admin Frontend Router

Serves Jinja2 templates for admin console pages migrated from React/Vite.
US#821-839: Migration from React/Vite to Jinja2 templates
"""

import os
from typing import Optional

import jwt
import structlog
from auth_service import authenticate_user
from fastapi import APIRouter, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-frontend"])

# Template directory
template_dir = os.path.join(os.path.dirname(__file__), "templates", "admin")
templates = Jinja2Templates(directory=template_dir)


def get_admin_token_from_cookie(request: Request) -> Optional[str]:
    """Extract admin token from cookie."""
    return request.cookies.get("admin_token")


def verify_admin_token(token: str) -> Optional[dict]:
    """Verify admin JWT token and return payload."""
    try:
        import os

        from auth_service import JWT_ALGORITHM, JWT_SECRET

        secret = os.getenv("NINAIVALAIGAL_JWT_SECRET") or JWT_SECRET
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Admin Login Page

    US#821: Migrate Admin Login from React/Vite to Jinja2

    Serves the admin login page as a Jinja2 template.
    """
    # Check if user is already authenticated via cookie
    token = get_admin_token_from_cookie(request)
    if token:
        payload = verify_admin_token(token)
        if payload:
            email = payload.get("email", "")
            admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
            if email in admin_emails:
                # Redirect to analytics if already logged in
                return RedirectResponse(url="/admin/analytics", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def admin_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Admin Login Submission

    Processes admin login form submission.
    US#821: Migrate Admin Login from React/Vite to Jinja2
    """
    try:
        # Authenticate user
        result = authenticate_user(email, password)

        if result and result.get("jwt_token"):
            # Verify admin access
            admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
            user_email = result.get("email", email)

            if user_email not in admin_emails:
                return templates.TemplateResponse(
                    "login.html",
                    {
                        "request": request,
                        "error": "Access denied. Admin access required.",
                    },
                    status_code=status.HTTP_403_FORBIDDEN,
                )

            # Create response with redirect
            response = RedirectResponse(url="/admin/analytics", status_code=status.HTTP_302_FOUND)

            # Set cookie with token (for session-based auth)
            response.set_cookie(
                key="admin_token",
                value=result["jwt_token"],
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600 * 24,  # 24 hours
            )

            return response
        else:
            # Login failed
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "error": "Invalid email or password. Please try again.",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
    except HTTPException as e:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": e.detail or "Login failed. Please check your credentials.",
            },
            status_code=e.status_code,
        )
    except Exception as e:
        logger.error("admin_login_failed", error=str(e), email=email)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Login failed. Please check your credentials.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics_page(request: Request):
    """
    Admin Analytics Dashboard

    US#822: Migrate Analytics Dashboard from React/Vite to Jinja2

    Serves the admin analytics dashboard as a Jinja2 template.
    """
    # Check authentication
    token = get_admin_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    payload = verify_admin_token(token)
    if not payload:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    email = payload.get("email", "")
    admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
    if email not in admin_emails:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("analytics.html", {"request": request})


@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    """
    Admin User Management

    US#823: Migrate User Management from React/Vite to Jinja2

    Serves the admin user management page as a Jinja2 template.
    """
    # Check authentication
    token = get_admin_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    payload = verify_admin_token(token)
    if not payload:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    email = payload.get("email", "")
    admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
    if email not in admin_emails:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("users.html", {"request": request})


@router.get("/teams", response_class=HTMLResponse)
async def admin_teams_page(request: Request):
    """
    Admin Team Management

    US#824: Migrate Team Management from React/Vite to Jinja2

    Serves the admin team management page as a Jinja2 template.
    """
    # Check authentication
    token = get_admin_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    payload = verify_admin_token(token)
    if not payload:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    email = payload.get("email", "")
    admin_emails = ["admin@ninaivalaigal.com", "swami@ninaivalaigal.com"]
    if email not in admin_emails:
        return RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("teams.html", {"request": request})


@router.get("/logout")
async def admin_logout(request: Request):
    """
    Admin Logout

    Logs out admin user and redirects to login page.
    """
    response = RedirectResponse(url="/admin/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="admin_token")
    return response
