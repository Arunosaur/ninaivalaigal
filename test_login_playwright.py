#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Playwright test for mem0 login page
Tests the UI functionality and debugging browser issues
"""

import asyncio

from playwright.async_api import async_playwright


async def test_login_page():
    """Test the login page with Playwright"""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to False to see browser
        context = await browser.new_context()
        page = await context.new_page()

        print("🚀 Testing mem0 login page with Playwright...")

        try:
            # Navigate to login page
            print("📍 Navigating to http://localhost:8000/login")
            response = await page.goto("http://localhost:8000/login")

            print(f"✅ Response status: {response.status}")
            print(f"✅ Response URL: {response.url}")

            # Wait for page to load
            await page.wait_for_load_state("networkidle")

            # Check if login form exists
            login_form = await page.query_selector("#login-form")
            if login_form:
                print("✅ Login form found")
            else:
                print("❌ Login form not found")

            # Check page title
            title = await page.title()
            print(f"📄 Page title: {title}")

            # Check for mem0 heading
            heading = await page.query_selector("h1")
            if heading:
                heading_text = await heading.text_content()
                print(f"📝 Main heading: {heading_text}")

            # Test form interaction
            print("\n🧪 Testing form interaction...")

            # Fill in test credentials
            await page.fill("#email", "john.developer@example.com")
            await page.fill("#password", "password123")

            print("✅ Form fields filled")

            # Take screenshot
            await page.screenshot(path="login_test_screenshot.png")
            print("📸 Screenshot saved as login_test_screenshot.png")

            # Test form submission (but don't actually submit)
            print("✅ Form ready for submission")

            # Check network requests
            print("\n🌐 Network requests:")

            # Listen for network events
            def log_request(request):
                print(f"  → {request.method} {request.url}")

            def log_response(response):
                print(f"  ← {response.status} {response.url}")

            page.on("request", log_request)
            page.on("response", log_response)

            # Refresh to see network activity
            await page.reload()
            await page.wait_for_load_state("networkidle")

            print("\n✅ Playwright test completed successfully!")

        except Exception as e:
            print(f"❌ Error during test: {e}")

        finally:
            await browser.close()


async def test_signup_page():
    """Test the signup page as well"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("\n🚀 Testing mem0 signup page...")

        try:
            # Navigate to signup page
            print("📍 Navigating to http://localhost:8000/")
            response = await page.goto("http://localhost:8000/")

            print(f"✅ Response status: {response.status}")

            # Wait for page to load
            await page.wait_for_load_state("networkidle")

            # Check for account type buttons
            individual_btn = await page.query_selector("#individual-btn")
            org_btn = await page.query_selector("#organization-btn")

            if individual_btn and org_btn:
                print("✅ Account type selection found")

                # Test account type switching
                await page.click("#individual-btn")
                await page.wait_for_timeout(500)

                individual_form = await page.query_selector("#individual-form")
                if individual_form:
                    is_visible = await individual_form.is_visible()
                    print(f"✅ Individual form visible: {is_visible}")

            # Take screenshot
            await page.screenshot(path="signup_test_screenshot.png")
            print("📸 Screenshot saved as signup_test_screenshot.png")

        except Exception as e:
            print(f"❌ Error during signup test: {e}")

        finally:
            await browser.close()


async def main():
    """Run all tests"""
    print("🎯 mem0 UI Testing with Playwright")
    print("=" * 50)

    # Test both pages
    await test_login_page()
    await test_signup_page()

    print("\n" + "=" * 50)
    print("✅ All Playwright tests completed!")
    print("\nIf you saw the browser open and pages load correctly,")
    print("then the issue might be browser cache or URL confusion.")
    print("\nTry:")
    print("1. Hard refresh (Cmd+Shift+R)")
    print("2. Clear browser cache")
    print("3. Try incognito/private mode")
    print("4. Check the exact URL in address bar")


if __name__ == "__main__":
    asyncio.run(main())
