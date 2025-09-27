# Secret Detectors Matrix

This document catalogs detectors used by the redaction engine. For each detector we provide:
- **Pattern** (simplified)
- **Examples**
- **Scope** (request-body, headers, env, files)
- **Action** (replace, drop, hash)
- **Notes** and **Unit tests** reference

> Guidance: Prefer allow-lists for *where* secrets should appear (e.g., only in config vault), and deny-lists for *what* to redact.

| ID | Provider | Pattern (simplified) | Examples | Scope | Action | Notes | Tests |
|----|----------|----------------------|----------|-------|--------|-------|-------|
| D001 | AWS Access Key | `\b(AKIA|ASIA)[0-9A-Z]{16}\b` | `AKIAIOSFODNN7EXAMPLE` | body, files | replace `<AWS_KEY>` | Also flag paired secrets | `tests/test_detectors.py::test_aws_access_key` |
| D002 | AWS Secret Key | Base64-like, 40 chars | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` | body, files | replace `<AWS_SECRET>` | Entropy > 4.0 | `tests/test_detectors.py::test_aws_secret` |
| D010 | GitHub Token | `gh[pousr]_[0-9a-zA-Z]{36,255}` | `ghp_...` | body, headers | replace `<GITHUB_TOKEN>` | Normalize case | `tests/test_detectors.py::test_github_token` |
| D020 | Slack Bot/User Token | `xox[baprs]-[0-9a-zA-Z-]{10,48}-[0-9a-zA-Z-]{10,48}(?:-[0-9a-zA-Z-]{10,48})?` | `xoxb-...` | body | replace `<SLACK_TOKEN>` | Some variants 3-part | `tests/test_detectors.py::test_slack_token` |
| D030 | JWT (generic) | `\beyJ[A-Za-z0-9_\-]{5,}\. [A-Za-z0-9_\-]{1,}\. [A-Za-z0-9_\-]{10,}\b` (whitespace optional) | header.payload.sig | body, headers | replace `<JWT>` | Support multiline | `tests/test_detectors.py::test_jwt` |
| D040 | Google API Key | `\bAIza[0-9A-Za-z\-_]{35}\b` | `AIzaSy...` | body | replace `<GOOGLE_API_KEY>` | 39 chars | `tests/test_detectors.py::test_google_api_key` |
| D050 | Stripe Secret | `\bsk_(live|test)_[0-9a-zA-Z]{24}\b` | `sk_live_...` | body | replace `<STRIPE_SECRET>` | | `tests/test_detectors.py::test_stripe_secret` |
| D060 | Azure Connection String | `Endpoint=sb://.*;SharedAccessKeyName=.*;SharedAccessKey=.*` | `Endpoint=...;SharedAccessKey=...` | body, files | replace `<AZURE_CONN>` | Parse `;` pairs | `tests/test_detectors.py::test_azure_conn` |
| D070 | PEM Private Key | `-----BEGIN (?:RSA |EC )?PRIVATE KEY-----` ... | PEM block | files, body | drop or hash | Multi-line | `tests/test_detectors.py::test_pem_block` |
| D999 | High-entropy token | shannon entropy > threshold | long random strings | body | replace `<ENTROPIC_SECRET>` | tune threshold per length | `tests/test_detectors.py::test_entropy` |

**Normalization before matching**
- Lowercase provider prefixes
- Collapse zero-width chars & confusables
- Trim whitespace and breaklines; still detect across chunk boundaries

**Redaction policy**
- Replace with deterministic placeholder tokens (e.g., `<AWS_KEY>`), not `[REDACTED]` — aids debugging without leaking.
- Never log raw pre-redaction content in application logs.
