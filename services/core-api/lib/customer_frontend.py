#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Customer Frontend Router

Serves Jinja2 templates for customer pages migrated from React/Vite.
US#825-839: Migration from React/Vite to Jinja2 templates
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

router = APIRouter(prefix="", tags=["customer-frontend"])  # No prefix for customer pages

# Template directory
template_dir = os.path.join(os.path.dirname(__file__), "templates", "customer")
templates = Jinja2Templates(directory=template_dir)


def get_customer_token_from_cookie(request: Request) -> Optional[str]:
    """Extract customer token from cookie."""
    return request.cookies.get("customer_token") or request.cookies.get("auth_token")


def verify_customer_token(token: str) -> Optional[dict]:
    """Verify customer JWT token and return payload."""
    try:
        import os

        from auth_service import JWT_ALGORITHM, JWT_SECRET

        secret = os.getenv("NINAIVALAIGAL_JWT_SECRET") or JWT_SECRET
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


@router.get("/login", response_class=HTMLResponse)
async def customer_login_page(request: Request):
    """
    Customer Login Page

    US#825: Migrate Customer Login from React/Vite to Jinja2

    Serves the customer login page as a Jinja2 template.
    """
    # Check if user is already authenticated via cookie
    token = get_customer_token_from_cookie(request)
    if token:
        payload = verify_customer_token(token)
        if payload:
            # Redirect to dashboard if already logged in
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def customer_login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Customer Login Submission

    Processes customer login form submission.
    US#825: Migrate Customer Login from React/Vite to Jinja2
    """
    try:
        # Authenticate user
        result = authenticate_user(email, password)

        if result and result.get("jwt_token"):
            # Create response with redirect
            response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)

            # Set cookie with token (for session-based auth)
            response.set_cookie(
                key="customer_token",
                value=result["jwt_token"],
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600 * 24 * 7,  # 7 days
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
        logger.error("customer_login_failed", error=str(e), email=email)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Login failed. Please check your credentials.",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


@router.get("/signup", response_class=HTMLResponse)
async def customer_signup_page(request: Request):
    """
    Customer Signup Page

    US#826: Migrate Customer Signup from React/Vite to Jinja2

    Serves the customer signup page as a Jinja2 template.
    """
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def customer_dashboard_page(request: Request):
    """
    Customer Dashboard

    US#827: Migrate Dashboard from React/Vite to Jinja2

    Serves the customer dashboard as a Jinja2 template.
    """
    # Check authentication
    token = get_customer_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    payload = verify_customer_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": payload})


@router.get("/memory-browser", response_class=HTMLResponse)
async def memory_browser_page(request: Request):
    """US#828: Memory Browser page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("memory-browser.html", {"request": request})


@router.get("/teams", response_class=HTMLResponse)
async def teams_page(request: Request):
    """US#829: Team Dashboard page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("teams.html", {"request": request})


@router.get("/teams/billing", response_class=HTMLResponse)
async def team_billing_page(request: Request):
    """US#830: Team Billing page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-billing.html", {"request": request})


@router.get("/teams/invoices", response_class=HTMLResponse)
async def team_invoices_page(request: Request):
    """US#831: Team Invoice List page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-invoices.html", {"request": request})


@router.get("/teams/payment-method", response_class=HTMLResponse)
async def payment_method_page(request: Request):
    """US#832: Team Payment Method page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("payment-method.html", {"request": request})


@router.get("/teams/usage", response_class=HTMLResponse)
async def team_usage_page(request: Request):
    """US#833: Team Usage page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-usage.html", {"request": request})


@router.get("/teams/create", response_class=HTMLResponse)
async def team_create_page(request: Request):
    """US#835: Team Create page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-create.html", {"request": request})


@router.get("/teams/invite", response_class=HTMLResponse)
async def team_invite_page(request: Request):
    """US#836: Team Invite page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-invite.html", {"request": request})


@router.get("/teams/upgrade", response_class=HTMLResponse)
async def team_upgrade_page(request: Request):
    """US#837: Team Upgrade page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("team-upgrade.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """
    Settings Page

    US#1057: PROF-002 - Settings Page Implementation

    Displays user settings for:
    - Notification preferences
    - Privacy settings
    - Account management
    - Security settings
    """
    token = get_customer_token_from_cookie(request)
    if not token:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    payload = verify_customer_token(token)
    if not payload:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Prepare user data and preferences
    user_data = {
        "id": payload.get("user_id"),
        "email": payload.get("email", ""),
        "name": payload.get("name", ""),
        "account_type": payload.get("account_type", "standard"),
        "two_factor_enabled": False,
    }

    # Default preferences
    preferences = {
        "email_notifications": True,
        "team_invites": True,
        "memory_updates": True,
        "profile_visibility": "team",
        "show_email": False,
        "data_sharing": True,
    }

    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user_data,
            "preferences": preferences,
        },
    )


@router.get("/teams/discount-nonprofit", response_class=HTMLResponse)
async def discount_nonprofit_page(request: Request):
    """US#838: Discount Non-Profit page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("discount-nonprofit.html", {"request": request})


@router.get("/injection-analytics", response_class=HTMLResponse)
async def injection_analytics_page(request: Request):
    """US#839: Injection Analytics page"""
    token = get_customer_token_from_cookie(request)
    if not token or not verify_customer_token(token):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("injection-analytics.html", {"request": request})


@router.get("/logout")
async def customer_logout(request: Request):
    """
    Customer Logout

    Logs out customer user and redirects to login page.
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="customer_token")
    response.delete_cookie(key="auth_token")
    return response
