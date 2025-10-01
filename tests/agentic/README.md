# Agentic UI Testing

## Overview

This directory contains **agentic UI tests** that use LLM agents to interact with the application UI.

## How It Works

1. **Playwright** opens your `/signup` page
2. Captures the DOM snapshot at each step
3. Sends DOM + goal → **LLM agent** (GPT-4)
4. Agent decides: `click`, `type`, or `assert`
5. Loop continues until the goal ("welcome message appears") is met

## Benefits

✅ **No brittle selectors**: Agent can adapt if button text changes
✅ **Test expresses intent**: "Sign up" rather than fixed script
✅ **Can be extended**: "Sign up → Record → Token visible in dashboard"
✅ **E2E sanity checks**: Not pixel-perfect regressions

## Setup

```bash
# Install dependencies
pip install playwright openai pytest-asyncio

# Install Playwright browsers
playwright install chromium

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"  # pragma: allowlist secret
```

## Running Tests

```bash
# Run agentic signup test
python tests/agentic/test_signup_flow.py

# Or with pytest
pytest tests/agentic/test_signup_flow.py -v

# Run all agentic tests
pytest tests/agentic/ -v
```

## Recommended Approach

1. **Keep smoke/API tests deterministic** (fast, stable)
2. **Add light agentic UI test suite** for high-level flows only (signup, record memory, Copilot integration)
3. **Run agentic UI tests nightly or pre-release**, not on every commit (they'll be slower and more variable)

## Example Output

```
[Agent Step 0] Decision: {'action': 'type', 'target': 'input[name="email"]', 'value': 'test@example.com'}
[Agent Step 1] Decision: {'action': 'type', 'target': 'input[name="password"]', 'value': 'SecurePass123!'}
[Agent Step 2] Decision: {'action': 'click', 'target': 'button[type="submit"]', 'value': ''}
[Agent Step 3] Decision: {'action': 'assert', 'target': 'body', 'value': 'Welcome'}
✅ Goal achieved! {'action': 'assert', 'target': 'body', 'value': 'Welcome'}
```

## Files

- `test_signup_flow.py` - Main agentic signup test
- `utils/playwright_helpers.py` - DOM extraction utilities
- `utils/prompts.py` - LLM prompts for agent

## Future Extensions

- Test "Sign up → Record memory → See token in dashboard"
- Test "Login → Navigate to settings → Change password"
- Test "Create team → Invite member → Accept invitation"

This way, colleagues can be sure **"the real UI works end-to-end"**, without your team constantly babysitting fragile UI selectors.
