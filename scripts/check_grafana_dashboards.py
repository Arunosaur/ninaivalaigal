#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Check Grafana dashboards using Playwright to diagnose "No data" issues
"""

import json
import time

from playwright.sync_api import sync_playwright


def check_grafana():
    print("🎭 Checking Grafana dashboards with Playwright...")
    print("")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser for debugging
        context = browser.new_context()
        page = context.new_page()

        try:
            # Navigate to Grafana
            print("📍 Navigating to Grafana login...")
            page.goto("http://localhost:3001/login", timeout=30000)
            time.sleep(2)

            # Login
            print("🔐 Logging in...")
            username_input = page.locator('input[name="user"]')
            password_input = page.locator('input[name="password"]')
            submit_button = page.locator('button[type="submit"]')

            username_input.fill("admin")
            password_input.fill("admin")
            submit_button.click()

            # Wait for login to complete (redirects to home)
            page.wait_for_url("**/?orgId=**", timeout=15000)
            time.sleep(3)

            # Go to dashboards page
            print("📊 Navigating to dashboards...")
            page.goto("http://localhost:3001/dashboards", timeout=30000)
            time.sleep(5)

            # Check for dashboards
            dashboard_links = page.locator('a[href*="/d/"]').all()
            print(f"   Found {len(dashboard_links)} dashboard links")

            if len(dashboard_links) == 0:
                print("   ⚠️  No dashboards found!")
                print("   Page content:")
                print(page.content()[:500])
                browser.close()
                return

            # List dashboards
            for i, dash in enumerate(dashboard_links[:5], 1):
                try:
                    title = dash.inner_text().strip()
                    href = dash.get_attribute("href")
                    print(f"   {i}. {title} ({href})")
                except:
                    pass

            # Open first dashboard
            print("")
            print("🔍 Opening first dashboard...")
            dashboard_links[0].click()
            page.wait_for_load_state("networkidle", timeout=20000)
            time.sleep(8)  # Wait for panels to load

            # Check for "No data" messages
            no_data_elements = page.locator("text=/No data/i").all()
            print(f"   Found {len(no_data_elements)} 'No data' messages")

            # Check panel errors
            error_elements = page.locator('[class*="error"]').all()
            print(f"   Found {len(error_elements)} error elements")

            # Check network requests
            print("")
            print("📡 Checking network requests...")

            # Intercept network requests to see what queries are being made
            requests_made = []

            def handle_request(request):
                if "prometheus" in request.url.lower() or "api/datasources/proxy" in request.url:
                    requests_made.append({"url": request.url, "method": request.method})

            page.on("request", handle_request)

            # Refresh the dashboard
            page.reload(wait_until="networkidle", timeout=20000)
            time.sleep(5)

            print(f"   Made {len(requests_made)} Prometheus-related requests")
            for req in requests_made[:3]:
                print(f"   • {req['method']} {req['url'][:80]}...")

            # Check datasource status
            print("")
            print("🔍 Checking datasource configuration...")
            page.goto("http://localhost:3001/connections/datasources", timeout=15000)
            time.sleep(3)

            prometheus_link = page.locator('a:has-text("Prometheus")')
            if prometheus_link.count() > 0:
                print("   Found Prometheus datasource")
                prometheus_link.first().click()
                time.sleep(3)

                # Check datasource URL
                url_input = page.locator('input[placeholder*="URL"]').first()
                if url_input.count() > 0:
                    url_value = url_input.input_value()
                    print(f"   Datasource URL: {url_value}")
                else:
                    # Try alternative selector
                    url_input = page.locator('input[name="url"]')
                    if url_input.count() > 0:
                        url_value = url_input.first().input_value()
                        print(f"   Datasource URL: {url_value}")

                # Test connection
                test_buttons = page.locator('button:has-text("Test")').all()
                save_test_buttons = page.locator('button:has-text("Save & Test")').all()

                test_button = None
                if len(save_test_buttons) > 0:
                    test_button = save_test_buttons[0]
                elif len(test_buttons) > 0:
                    test_button = test_buttons[0]

                if test_button:
                    print("   Testing connection...")
                    test_button.click()
                    time.sleep(5)

                    # Check for success/error message
                    page_content = page.content()
                    if "working" in page_content.lower() or "success" in page_content.lower():
                        print("   ✅ Datasource connection successful")
                    elif "error" in page_content.lower() or "fail" in page_content.lower():
                        error_text = (
                            page.locator("text=/error|fail/i").first().inner_text()
                            if page.locator("text=/error|fail/i").count() > 0
                            else "Connection failed"
                        )
                        print(f"   ❌ Datasource connection failed:")
                        print(f"      {error_text[:200]}")
                    else:
                        print("   ⚠️  Could not determine connection status")

            # Go back to dashboard and check Explore
            print("")
            print("🔬 Testing query in Explore...")
            page.goto("http://localhost:3001/explore", timeout=15000)
            time.sleep(3)

            # Select Prometheus datasource
            datasource_dropdown = page.locator('[aria-label*="Data source"]').first()
            if datasource_dropdown.count() > 0:
                datasource_dropdown.click()
                time.sleep(1)
                page.locator("text=Prometheus").click()
                time.sleep(2)

            # Enter query
            query_input = page.locator('textarea[placeholder*="metrics"]').first()
            if query_input.count() > 0:
                query_input.fill("http_requests_total")
                time.sleep(2)

                # Run query
                run_button = page.locator('button:has-text("Run query")')
                if run_button.count() > 0:
                    run_button.click()
                    time.sleep(5)

                    # Check results
                    no_data = page.locator("text=/No data/i")
                    if no_data.count() > 0:
                        print("   ❌ Query returned 'No data'")
                        print("   This means Prometheus datasource is not working correctly")
                    else:
                        print("   ✅ Query returned data!")

            # Take screenshot for debugging
            print("")
            print("📸 Taking screenshot...")
            page.screenshot(path="/tmp/grafana-debug.png")
            print("   Saved to /tmp/grafana-debug.png")

            print("")
            print("✅ Playwright check complete")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            page.screenshot(path="/tmp/grafana-error.png")
            print("   Error screenshot saved to /tmp/grafana-error.png")

        finally:
            print("")
            print("⏸️  Keeping browser open for 10 seconds for inspection...")
            time.sleep(10)
            browser.close()


if __name__ == "__main__":
    check_grafana()
