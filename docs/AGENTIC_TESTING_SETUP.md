# Agentic Testing Setup - Hybrid OpenAI/Ollama

**Date:** October 12, 2025
**Status:** ✅ COMPLETE - Hybrid LLM Strategy
**SPEC:** SPEC-084 - Agentic UI Testing Framework

---

## 🎯 Strategy: Smart Hybrid Approach

| Environment | LLM Provider | Cost | Why |
|-------------|--------------|------|-----|
| **Development** | OpenAI API | ~$0.01/test | Fast, reliable, immediate results |
| **CI Nightly** | Ollama | FREE | No API costs for scheduled tests |
| **Fallback** | Ollama | FREE | When OpenAI budget exhausted |

---

## 📦 Infrastructure Setup

### **Shared Ollama Container**

**Container Name:** `ollama` (shared, not project-specific)
**Port:** 11434
**Model:** llama3.2 (2GB)

```bash
# Check if running
container list | grep ollama

# Should show:
# ollama    ollama/ollama:latest    0.0.0.0:11434->11434/tcp
```

**Why Shared Container:**
- ✅ Reuse across all projects
- ✅ Models are expensive to download (2GB+)
- ✅ One LLM server, many clients
- ✅ Resource efficient

---

## 🔧 Quick Start Commands

### **1. Check Ollama Status**
```bash
make test-ollama-status
```

**Expected Output:**
```
✅ Ollama container running
✅ Ollama API responding
llama3.2
```

---

### **2. Run Signup Unit Tests**
```bash
make test-signup
```

**What it tests:**
- User signup with ORM
- Login with JWT tokens
- Password hashing
- Email validation
- UUID serialization (bug we fixed!)
- Database relationships

---

### **3. Run Agentic Tests (Auto-Detect)**
```bash
# With OpenAI API key set
export OPENAI_API_KEY="sk-proj-..."
make test-agentic  # Uses OpenAI

# Without API key
unset OPENAI_API_KEY
make test-agentic  # Uses Ollama
```

---

### **4. Force Specific LLM**

**OpenAI (Fast, Paid):**
```bash
export OPENAI_API_KEY="sk-proj-..."
make test-agentic-openai
```

**Ollama (Free, Local):**
```bash
make test-agentic-ollama
```

---

## 📊 What Agentic Tests Do

### **Test Flow:**
1. **Start browser** (headless Chromium)
2. **Navigate to signup page**
3. **LLM analyzes DOM:**
   ```
   Agent sees: [
     {tag: "input", type: "email", placeholder: "Email address"},
     {tag: "input", type: "password", placeholder: "Password"},
     {tag: "button", text: "Sign up"}
   ]
   ```
4. **LLM decides action:**
   ```json
   {"action": "type", "target": "input[type='email']", "value": "test@example.com"}
   ```
5. **Execute action** (fill email)
6. **Repeat** until goal achieved
7. **Assert success message**

### **Benefits:**
- ✅ No brittle CSS selectors
- ✅ Adapts to UI changes
- ✅ Tests user intent, not implementation
- ✅ Self-healing tests

---

## 💰 Cost Comparison

### **OpenAI API (gpt-4o-mini)**
| Usage | Input | Output | Total |
|-------|-------|--------|-------|
| 1 test | $0.001 | $0.004 | ~$0.005 |
| 100 tests | $0.10 | $0.40 | ~$0.50 |
| 1000 tests | $1.00 | $4.00 | ~$5.00 |

**Pricing:**
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens

**Monthly Budget Estimate:**
- Daily dev runs: 10 tests/day × $0.005 = $0.05/day = **$1.50/month**
- CI Nightly: 0 tests (uses Ollama)

**Very affordable!** ✅

---

### **Ollama (Local LLM)**
| Usage | Cost | Performance |
|-------|------|-------------|
| Any # of tests | FREE | ~2x slower than OpenAI |
| Model download | FREE (one-time, 2GB) | ~2 minutes |
| Running costs | FREE | Uses local compute |

**Trade-offs:**
- ✅ FREE (no API costs)
- ✅ Privacy (data stays local)
- ⏱️ Slightly slower (~2x)
- 🖥️ Uses local GPU/CPU

---

## 🔄 CI/CD Strategy

### **GitHub Actions Workflow**

```yaml
name: Agentic Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM
  workflow_dispatch:      # Manual trigger

jobs:
  agentic-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      # Setup Ollama (free for CI)
      - name: Start Ollama
        run: |
          docker run -d --name ollama \
            -p 11434:11434 \
            ollama/ollama:latest
          docker exec ollama ollama pull llama3.2

      # Run tests with Ollama
      - name: Run Agentic Tests
        run: USE_OLLAMA=true make test-agentic

      # Optional: Use OpenAI for critical tests
      - name: Run Critical Tests with OpenAI
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: make test-agentic-openai
```

**Strategy:**
- ✅ Nightly: Use Ollama (free)
- ✅ Pre-release: Use OpenAI (reliable)
- ✅ On-demand: Developer choice

---

## 📁 File Structure

```
tests/agentic/
├── test_signup_flow.py          # Original OpenAI-only version
├── test_signup_hybrid.py         # NEW: Hybrid OpenAI/Ollama ✅
├── utils/
│   ├── playwright_helpers.py    # DOM extraction
│   └── prompts.py               # LLM prompts
└── README.md                    # Documentation
```

---

## 🧪 Test Examples

### **Unit Tests (Fast, No LLM)**
```bash
# Test signup/login functionality
make test-signup

# Tests:
# ✅ User signup with ORM
# ✅ Login returns JWT token
# ✅ UUID serialization works
# ✅ Password hashing secure
# ✅ Email validation
```

---

### **Agentic Tests (Slow, Uses LLM)**
```bash
# Auto-detect: OpenAI if key set, else Ollama
make test-agentic

# Force OpenAI
make test-agentic-openai

# Force Ollama
make test-agentic-ollama
```

**Example Test Output:**
```
🤖 Running hybrid agentic tests...
   Using: OpenAI API (gpt-4o-mini)

[Step 0] {"action": "type", "target": "input[type='email']", "value": "test@example.com"}
[Step 1] {"action": "type", "target": "input[type='password']", "value": "SecurePass123!"}
[Step 2] {"action": "type", "target": "input[name='name']", "value": "Test User"}
[Step 3] {"action": "click", "target": "button[type='submit']", "value": ""}
[Step 4] {"action": "assert", "target": "", "value": "success"}
✅ Goal achieved!

PASSED tests/agentic/test_signup_hybrid.py::test_signup_flow_hybrid
```

---

## 🐛 Troubleshooting

### **Ollama Not Responding**
```bash
# Check container
container list | grep ollama

# If not running, start it
container run -d --name ollama \
  -p 11434:11434 \
  -v ollama_models:/root/.ollama \
  ollama/ollama:latest

# Pull model if needed
container exec ollama ollama pull llama3.2
```

---

### **OpenAI API Errors**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# If empty, set it
export OPENAI_API_KEY="sk-proj-..."

# Test API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq .
```

---

### **Conda Environment Not Found**
```bash
# Check available environments
conda env list

# Should show:
# nina    /Users/.../miniconda3/envs/nina

# Activate manually
conda activate nina

# Then run tests without make
pytest tests/test_signup.py -v
```

---

## 🎯 Best Practices

### **Development (You)**
✅ **Use OpenAI** for fast iteration
- Set `OPENAI_API_KEY` in shell profile
- Tests run in ~30 seconds
- Immediate feedback

---

### **CI/CD (Automated)**
✅ **Use Ollama** for scheduled tests
- No API costs
- Runs nightly
- Tests run in ~60 seconds

---

### **Budget Management**
✅ **Monitor usage:**
```bash
# Check OpenAI usage
# Visit: https://platform.openai.com/usage
```

✅ **Set budget alerts:**
- Go to: https://platform.openai.com/account/billing/limits
- Set soft limit: $10/month
- Set hard limit: $20/month

✅ **Fallback to Ollama:**
```bash
# When approaching budget
USE_OLLAMA=true make test-agentic
```

---

## 📚 Related Documentation

- **SPEC-084:** Agentic UI Testing Framework
- **JWT Token Usage:** `/docs/JWT_TOKEN_USAGE.md`
- **Signup Fix:** `/docs/SIGNUP_FIX_COMPLETE.md`

---

## ✅ Checklist - Setup Complete

- [x] Ollama container running (shared)
- [x] llama3.2 model downloaded (2GB)
- [x] Hybrid test framework created
- [x] Makefile targets added
- [x] OpenAI API key configured
- [x] Conda environment available
- [x] Documentation complete

---

## 🚀 Next Steps

**Run the tests!**

```bash
# 1. Check everything is ready
make test-ollama-status

# 2. Run unit tests
make test-signup

# 3. Run agentic tests with OpenAI
export OPENAI_API_KEY="sk-proj-..."
make test-agentic

# 4. Try with Ollama (free)
make test-agentic-ollama
```

**The hybrid strategy is ready! 🎉**
