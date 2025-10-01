"""
Agentic UI Testing for Signup Flow

Uses LLM agent to interact with the signup page and verify the flow works.
Agent decides actions dynamically based on DOM state and goal.
"""

import asyncio
import os

from openai import OpenAI
from playwright.async_api import async_playwright

# Set up LLM client (uses OpenAI API; can replace with local LLM)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def agent_decide(dom_snapshot: str, goal: str) -> dict:
    """
    Ask the agent: what should I do next?

    Args:
        dom_snapshot: Current DOM/rendered UI state
        goal: What we're trying to achieve

    Returns:
        {"action": "click|type|assert", "target": "selector", "value": "..."}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a QA testing agent. "
                    "You interact with web UIs. "
                    "Given the DOM and a goal, decide what to do next.\n"
                    '{"action": "click|type|assert", "target": "selector", "value": "..."}'
                ),
            },
            {
                "role": "user",
                "content": (
                    f"DOM:\n{dom_snapshot}\n\nGoal: {goal}\n\n"
                    "What should I do next? Reply in JSON with: "
                    "{{'action': 'click|type|assert', 'target': 'selector', 'value': '...'}}"
                ),
            },
        ],
    )
    try:
        import json

        decision = json.loads(response.choices[0].message.content)
        return decision
    except Exception:
        return {"action": "assert", "target": "body", "value": "fail"}


async def run_agentic_signup():
    """
    Run agentic signup test.

    Goal: "Sign up as a new user, then confirm that a welcome message appears"
    """
    goal = "Sign up as a new user and confirm that a welcome token appears in the dashboard"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("http://localhost:13390/signup")

        for step in range(10):  # limit to 10 agent steps
            dom = await page.content()
            decision = await agent_decide(dom, goal)

            print(f"[Agent Step {step}] Decision: {decision}")

            if decision["action"] == "click":
                await page.click(decision["target"])
            elif decision["action"] == "type":
                await page.fill(decision["target"], decision["value"])
            elif decision["action"] == "assert":
                assert decision["value"] in dom
                print(f"✅ Goal achieved! {decision}")
                break

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_agentic_signup())
