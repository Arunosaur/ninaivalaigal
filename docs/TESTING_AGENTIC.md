# Guide: Agentic Testing with Ollama & OpenAI

**Last Updated:** October 12, 2025
**Owner:** QA Team

---

## 1. What are Agentic Tests?

Agentic tests are a form of UI testing where an LLM-powered agent, instead of a human or a rigid script, navigates a web application to perform a task. The test provides a high-level goal (e.g., "Sign up as a new user"), and the agent determines the specific actions (clicking buttons, filling forms) required to achieve it.

### Benefits
- **Resilience:** Less brittle than traditional selector-based tests.
- **Natural Language:** Tests are written in natural language, making them more readable.
- **Real-world Scenarios:** Simulates how a real user would interact with the UI.

---

## 2. When to Use Agentic Tests

Use agentic tests for **critical user journeys** that are prone to UI changes.

✅ **Good Candidates:**
- Signup and login flows
- Core CRUD operations (e.g., creating a memory)
- Onboarding flows
- Complex, multi-step workflows

❌ **Bad Candidates:**
- Unit testing of individual components
- Performance testing
- Pixel-perfect visual regression

---

## 3. Setting up Ollama (Local & Free)

Ollama allows you to run open-source LLMs locally, which is perfect for running agentic tests without incurring API costs.

### Installation

```bash
# Install Ollama
brew install ollama

# Pull a model
ollama pull llama3.2  # Or any other model

# Run the Ollama server
ollama serve
```

### Configuration

No API key is needed for Ollama. The test framework will automatically detect if the Ollama server is running.

---

## 4. Setting up OpenAI (Development)

OpenAI provides high-quality models that are great for development and debugging.

### Installation

```bash
pip install openai
```

### Configuration

```bash
export OPENAI_API_KEY="your-api-key-here"
```

The test framework will use OpenAI if this environment variable is set.

---

## 5. Writing Your First Agentic Test

This example uses Playwright and our custom `llm_agent` fixture.

```python
# tests/agentic/test_signup_agentic.py
import pytest

@pytest.mark.asyncio
async def test_signup_flow_agentic(page, llm_agent):
    """Test the full signup flow using an LLM agent."""

    # 1. Navigate to the page
    await llm_agent.navigate("http://localhost:3000/signup")

    # 2. Define the task
    task = (
        "Sign up as a new user with the following details: "
        "Name: Test User, Email: test.user@example.com, Password: Password123!"
    )

    # 3. Let the agent complete the task
    await llm_agent.complete_task(task)

    # 4. Verify the outcome
    assert await llm_agent.verify("The user is successfully logged in and on the dashboard page.")
```

---

## 6. Hybrid Strategy (OpenAI + Ollama)

We use a hybrid strategy to balance cost and performance:

- **Local Development:** Use OpenAI for fast, reliable feedback.
- **CI/CD (Nightly):** Use Ollama to run tests for free.
- **Fallback:** If the OpenAI API fails, the framework can automatically fall back to Ollama.

### How it Works

The `llm_agent` fixture in `conftest.py` automatically detects which service to use:

```python
# conftest.py (simplified)
@pytest.fixture
def llm_agent(page):
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAIAgent(page)
    elif is_ollama_running():
        return OllamaAgent(page)
    else:
        pytest.skip("No LLM service available")
```

---

## 7. Running Agentic Tests

Use the `Makefile` for easy execution.

```bash
# Auto-detect (OpenAI if key is set, else Ollama)
make test-agentic

# Force OpenAI
make test-agentic-openai

# Force Ollama (free)
make test-agentic-ollama
```

---

## 8. CI/CD Integration

Agentic tests run nightly using a dedicated GitHub Actions workflow.

**File:** `.github/workflows/agentic-nightly.yml`

```yaml
name: Nightly Agentic Tests

on:
  schedule:
    - cron: '0 2 * * *' # Run at 2 AM UTC

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Ollama tests
        run: make test-agentic-ollama
```

---

## 9. Cost Optimization

- **Ollama:** Free (uses local compute).
- **OpenAI:** Pay-per-use. To minimize costs, we use smaller, faster models for agentic tests (e.g., `gpt-4o-mini`).

**Estimated Cost (OpenAI):** ~$0.01 per test run.

---

## 10. Debugging Agentic Tests

- **Verbose Logging:** Run pytest with `-vv -s` to see detailed logs from the agent.
- **Playwright Trace:** Use Playwright's tracing to see a step-by-step execution of the test.
- **Check the Prompts:** The prompts used to guide the LLM are in `tests/agentic/prompts.py`.
