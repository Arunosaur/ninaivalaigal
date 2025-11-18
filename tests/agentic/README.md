# Agentic UI Testing

## Overview

This directory contains **agentic UI tests** that use LLM agents to interact with the application UI. The framework provides a reusable foundation for creating agentic tests with:

- ✅ **Test agent setup** - Base classes for agentic testing
- ✅ **UI interaction automation** - Playwright-based automation
- ✅ **Test scenario generation** - Programmatic scenario creation
- ✅ **Result validation** - Comprehensive validation framework

## Framework Structure

The agentic UI testing framework is organized as follows:

```
tests/agentic/
├── framework/                    # Foundation framework
│   ├── base_agent.py            # Base agent class and core types
│   ├── scenario_generator.py    # Scenario generation utilities
│   ├── validators.py            # Validation framework
│   ├── providers.py             # LLM provider implementations
│   └── __init__.py              # Framework exports
├── test_signup_flow.py          # Original signup test
├── test_signup_hybrid.py        # Hybrid OpenAI/Ollama test
├── test_framework_example.py     # Framework usage examples
├── agentic_signup_test.py       # Simplified signup test
├── utils/                        # Legacy utilities
│   ├── playwright_helpers.py    # DOM extraction utilities
│   └── prompts.py               # LLM prompts
└── README.md                     # This file
```

## How It Works

1. **Playwright** opens your application page
2. Captures the DOM snapshot at each step
3. Sends DOM + goal → **LLM agent** (OpenAI or Ollama)
4. Agent decides: `click`, `type`, `assert`, `navigate`, `wait`, `scroll`
5. Loop continues until the goal is achieved

## Benefits

✅ **No brittle selectors**: Agent can adapt if button text changes
✅ **Test expresses intent**: "Sign up" rather than fixed script
✅ **Can be extended**: "Sign up → Record → Token visible in dashboard"
✅ **E2E sanity checks**: Not pixel-perfect regressions
✅ **Reusable framework**: Easy to create new test scenarios
✅ **Multiple LLM providers**: OpenAI, Ollama, or hybrid

## Setup

### Install Dependencies

```bash
# Core dependencies
pip install playwright pytest-asyncio

# For OpenAI provider
pip install openai

# For Ollama provider (optional)
pip install httpx

# Install Playwright browsers
playwright install chromium
```

### Configure LLM Provider

**Option 1: OpenAI (Recommended for Development)**
```bash
export OPENAI_API_KEY="your-key-here"  # pragma: allowlist secret
```

**Option 2: Ollama (Free, Local)**
```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.ai

# Pull a model
ollama pull llama3.2

# Start Ollama server
ollama serve
```

**Option 3: Hybrid (Auto-selects)**
The framework will automatically use OpenAI if available, otherwise fall back to Ollama.

## Using the Framework

### Basic Example

```python
from tests.agentic.framework import BaseAgenticTest, ScenarioGenerator
from tests.agentic.framework.providers import HybridProvider

# Initialize provider
provider = HybridProvider()

# Create test agent
agent = BaseAgenticTest(provider, headless=True)

# Generate scenario
scenario = ScenarioGenerator.create_signup_scenario(
    base_url="http://localhost:13390",
    email="test@example.com"
)

# Run test
result = await agent.run_scenario(scenario)

# Check result
assert result.success, f"Test failed: {result.error_message}"
```

### Custom Scenario

```python
from tests.agentic.framework import ScenarioGenerator

scenario = ScenarioGenerator.create_custom_scenario(
    name="Custom Flow",
    goal="Complete a multi-step workflow",
    url="http://localhost:13390/start",
    max_steps=20,
    expected_outcomes=["success", "completed"]
)
```

### With Validation

```python
from tests.agentic.framework import ValidationFramework, get_signup_validation_rules

validation = ValidationFramework()
validation.add_rules(get_signup_validation_rules())

# After running scenario, validate results
results = await validation.validate(page, result)
assert all(results.values()), "Validation failed"
```

## Running Tests

```bash
# Run framework example tests
pytest tests/agentic/test_framework_example.py -v

# Run original signup test
pytest tests/agentic/test_signup_flow.py -v

# Run hybrid test (auto-detects provider)
pytest tests/agentic/test_signup_hybrid.py -v

# Run all agentic tests
pytest tests/agentic/ -v
```

## Framework Components

### BaseAgenticTest

The core class for agentic testing. Provides:
- Browser setup and teardown
- DOM snapshot extraction
- Decision execution
- Scenario execution loop
- Result validation

### ScenarioGenerator

Utilities for creating test scenarios:
- `create_signup_scenario()` - Signup flow
- `create_login_scenario()` - Login flow
- `create_admin_dashboard_scenario()` - Admin dashboard
- `create_custom_scenario()` - Custom scenarios
- `create_flow_scenario()` - Multi-step flows

### ValidationFramework

Comprehensive validation system:
- Content validation
- URL validation
- Element visibility validation
- Step count validation
- Execution time validation
- Custom validation rules

### LLM Providers

- **OpenAIProvider** - Uses OpenAI API (gpt-4o-mini recommended)
- **OllamaProvider** - Uses local Ollama server (free)
- **HybridProvider** - Auto-selects best available provider

## Recommended Approach

1. **Keep smoke/API tests deterministic** (fast, stable)
2. **Add light agentic UI test suite** for high-level flows only (signup, record memory, Copilot integration)
3. **Run agentic UI tests nightly or pre-release**, not on every commit (they'll be slower and more variable)

## Example Output

```
[Step 1] click: button[type="submit"]
[Step 2] type: input[name="email"] -> test@example.com
[Step 3] type: input[name="password"] -> SecurePass123!
[Step 4] click: button[type="submit"]
[Step 5] assert: Welcome
✅ Test PASSED
Steps taken: 5
Execution time: 12.34s
```

## Files

### Framework Files
- `framework/base_agent.py` - Base agent class and core types
- `framework/scenario_generator.py` - Scenario generation
- `framework/validators.py` - Validation framework
- `framework/providers.py` - LLM provider implementations
- `test_framework_example.py` - Framework usage examples

### Legacy Files
- `test_signup_flow.py` - Original signup test
- `test_signup_hybrid.py` - Hybrid OpenAI/Ollama test
- `agentic_signup_test.py` - Simplified signup test
- `utils/playwright_helpers.py` - DOM extraction utilities
- `utils/prompts.py` - LLM prompts for agent

## Future Extensions

- Test "Sign up → Record memory → See token in dashboard"
- Test "Login → Navigate to settings → Change password"
- Test "Create team → Invite member → Accept invitation"
- Test "Admin SSO login → Dashboard → Metrics visible"

This way, colleagues can be sure **"the real UI works end-to-end"**, without your team constantly babysitting fragile UI selectors.
