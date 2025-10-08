"""
Agentic UI Test: Signup Flow

This test uses an LLM agent to interact with the signup page.
The agent decides what to click/type based on the DOM and goal.

Benefits:
- No brittle selectors
- Agent adapts if button text changes
- Test expresses intent ("sign up") rather than fixed script
"""

import asyncio
import json
import os

import pytest
from openai import OpenAI
from playwright.async_api import async_playwright

from .utils.playwright_helpers import get_simplified_dom, wait_for_navigation_or_change
from .utils.prompts import SYSTEM_PROMPT, get_user_prompt


class AgenticSignupTest:
    """Agentic test for signup flow."""

    def __init__(self):
        """Initialize the agentic test."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.max_steps = 10

    async def agent_decide(self, dom_snapshot: str, goal: str) -> dict:
        """
        Ask the agent: what should I do next?

        Returns:
            {"action": "click|type|assert", "target": "selector", "value": "..."}
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": get_user_prompt(dom_snapshot, goal)},
                ],
            )

            decision = json.loads(response.choices[0].message.content)
            return decision
        except Exception as e:
            print(f"Agent decision error: {e}")
            return {"action": "fail", "target": "", "value": str(e)}

    async def run_test(self, url: str, goal: str):
        """
        Run the agentic test.

        Args:
            url: Starting URL
            goal: What we're trying to achieve
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            await page.goto(url)

            for step in range(self.max_steps):
                # Get simplified DOM for agent
                dom = await get_simplified_dom(page)

                # Ask agent what to do
                decision = await self.agent_decide(dom, goal)
                print(f"[Agent Step {step}] Decision: {decision}")

                # Execute action
                if decision["action"] == "click":
                    try:
                        await page.click(decision["target"])
                        await wait_for_navigation_or_change(page)
                    except Exception as e:
                        print(f"Click failed: {e}")

                elif decision["action"] == "type":
                    try:
                        await page.fill(decision["target"], decision["value"])
                    except Exception as e:
                        print(f"Type failed: {e}")

                elif decision["action"] == "assert":
                    # Check if assertion passes
                    content = await page.content()
                    if decision["value"] in content:
                        print(f"✅ Goal achieved! {decision}")
                        await browser.close()
                        return True
                    else:
                        print(f"❌ Assertion failed: {decision['value']} not found")

                elif decision["action"] == "fail":
                    print(f"❌ Agent failed: {decision['value']}")
                    break

            await browser.close()
            return False


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - skipping agentic test",
)
async def test_signup_flow_agentic():
    """
    Agentic test: Sign up as a new user and confirm welcome message appears.

    This test will:
    1. Navigate to /signup
    2. Let agent fill out form
    3. Let agent click submit
    4. Verify success message appears
    """
    tester = AgenticSignupTest()
    result = await tester.run_test(
        url="http://localhost:13390/signup",
        goal=(
            "Sign up as a new user with email test@example.com " "and confirm that a success or welcome message appears"
        ),
    )

    assert result, "Agentic signup test failed to achieve goal"


if __name__ == "__main__":
    # Run standalone
    tester = AgenticSignupTest()
    result = asyncio.run(
        tester.run_test(
            url="http://localhost:13390/signup",
            goal="Sign up as a new user and confirm that a success message appears",
        )
    )
    print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
