#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Hybrid Agentic UI Test: Signup Flow
Supports both OpenAI API and Ollama (local LLM)

Strategy:
- Development: Use OpenAI API (fast, reliable)
- CI/Nightly: Use Ollama (free, no API costs)
- Fallback: Ollama when OpenAI budget exhausted
"""

import asyncio
import json
import os

import pytest


class LLMProvider:
    """Abstract LLM provider for agentic tests"""

    @staticmethod
    def create():
        """Factory: Auto-detect and create appropriate LLM provider"""
        if os.getenv("OPENAI_API_KEY") and os.getenv("USE_OLLAMA") != "true":
            print("🔵 Using OpenAI API")
            return OpenAIProvider()
        else:
            print("🟢 Using Ollama (local)")
            return OllamaProvider()


class OpenAIProvider:
    """OpenAI API provider"""

    def __init__(self):
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o-mini"  # Cheapest, fastest

    async def ask(self, system_prompt: str, user_prompt: str) -> dict:
        """Ask OpenAI for decision"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return {"action": "fail", "target": "", "value": str(e)}


class OllamaProvider:
    """Ollama local LLM provider"""

    def __init__(self):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

    async def ask(self, system_prompt: str, user_prompt: str) -> dict:
        """Ask Ollama for decision"""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": False,
                    },
                )

                if response.status_code != 200:
                    raise Exception(f"Ollama error: {response.status_code}")

                result = response.json()
                content = result["message"]["content"]

                # Try to parse JSON from response
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # LLM might return text before/after JSON
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                    raise

        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return {"action": "fail", "target": "", "value": str(e)}


class HybridAgenticTest:
    """Hybrid agentic test using OpenAI or Ollama"""

    def __init__(self):
        self.llm = LLMProvider.create()
        self.max_steps = 10

    async def agent_decide(self, dom_snapshot: str, goal: str) -> dict:
        """Ask LLM agent: what should I do next?"""

        system_prompt = """You are a web automation agent. Analyze the DOM and decide the next action.

Return ONLY valid JSON with this format:
{"action": "click|type|assert", "target": "CSS selector", "value": "text to type or assert"}

Examples:
- Click button: {"action": "click", "target": "button[type='submit']", "value": ""}
- Type text: {"action": "type", "target": "input[name='email']", "value": "test@example.com"}
- Assert success: {"action": "assert", "target": "", "value": "success"}

Return ONLY the JSON, no explanation."""

        user_prompt = f"""DOM Snapshot:
{dom_snapshot}

Goal: {goal}

What should I do next? Return JSON only."""

        return await self.llm.ask(system_prompt, user_prompt)

    async def run_test(self, url: str, goal: str) -> bool:
        """Run the agentic test"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            pytest.skip("Playwright not installed")
            return False

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)

            for step in range(self.max_steps):
                # Get simplified DOM
                dom = await self._get_dom(page)

                # Ask agent
                decision = await self.agent_decide(dom, goal)
                print(f"[Step {step}] {decision}")

                # Execute action
                if decision["action"] == "click":
                    try:
                        await page.click(decision["target"], timeout=5000)
                        await page.wait_for_timeout(1000)
                    except Exception as e:
                        print(f"Click failed: {e}")

                elif decision["action"] == "type":
                    try:
                        await page.fill(decision["target"], decision["value"])
                        await page.wait_for_timeout(500)
                    except Exception as e:
                        print(f"Type failed: {e}")

                elif decision["action"] == "assert":
                    content = await page.content()
                    if decision["value"].lower() in content.lower():
                        print("✅ Goal achieved!")
                        await browser.close()
                        return True

                elif decision["action"] == "fail":
                    print(f"❌ Agent failed: {decision['value']}")
                    break

            await browser.close()
            return False

    async def _get_dom(self, page) -> str:
        """Get simplified DOM snapshot"""
        # Extract visible text and interactive elements
        dom = await page.evaluate(
            """() => {
            const elements = [];
            document.querySelectorAll('input, button, a, h1, h2, h3, label, [role="button"]').forEach(el => {
                if (el.offsetParent !== null) {  // visible
                    elements.push({
                        tag: el.tagName.toLowerCase(),
                        text: el.textContent?.trim().slice(0, 50),
                        type: el.type,
                        name: el.name,
                        id: el.id,
                        placeholder: el.placeholder
                    });
                }
            });
            return elements;
        }"""
        )

        return json.dumps(dom, indent=2)


@pytest.mark.asyncio
@pytest.mark.agentic
async def test_signup_flow_hybrid():
    """
    Hybrid agentic test: Sign up using OpenAI or Ollama

    Set USE_OLLAMA=true to force Ollama
    Otherwise uses OpenAI if OPENAI_API_KEY is set
    """
    tester = HybridAgenticTest()

    result = await tester.run_test(
        url="http://localhost:13390/signup",
        goal="Sign up as a new user with a unique email and verify success message appears",
    )

    assert result, "Agentic signup test failed to achieve goal"


if __name__ == "__main__":
    # Run standalone
    tester = HybridAgenticTest()
    result = asyncio.run(
        tester.run_test(url="http://localhost:13390/signup", goal="Sign up as a new user and confirm success")
    )
    print(f"\n{'✅ Test PASSED' if result else '❌ Test FAILED'}")
