"""Playwright Helper Utilities for Agentic Testing."""

from playwright.async_api import Page


async def get_simplified_dom(page: Page) -> str:
    """
    Get a simplified DOM snapshot for the LLM agent.

    Removes scripts, styles, and focuses on interactive elements.
    """
    # Extract only relevant elements for the agent
    dom_script = """
    () => {
        const elements = document.querySelectorAll('input, button, a, form, h1, h2, p');
        return Array.from(elements).map(el => ({
            tag: el.tagName,
            id: el.id,
            class: el.className,
            text: el.textContent?.trim().substring(0, 100),
            placeholder: el.placeholder,
            type: el.type,
            name: el.name
        }));
    }
    """
    elements = await page.evaluate(dom_script)

    # Format for LLM
    dom_text = []
    for el in elements:  # noqa: E501
        parts = [f"<{el['tag'].lower()}"]
        if el.get("id"):
            parts.append(f" id='{el['id']}'")
        if el.get("name"):
            parts.append(f" name='{el['name']}'")
        if el.get("type"):
            parts.append(f" type='{el['type']}'")
        if el.get("placeholder"):
            parts.append(f" placeholder='{el['placeholder']}'")
        parts.append(">")
        if el.get("text"):
            parts.append(el["text"])
        dom_text.append("".join(parts))

    return "\n".join(dom_text)


async def wait_for_navigation_or_change(page: Page, timeout: int = 5000):
    """Wait for either navigation or DOM change."""
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass  # Timeout is ok, just continue
