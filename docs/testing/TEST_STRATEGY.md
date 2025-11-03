# Test Strategy Overview

This project follows a three-tier test taxonomy so the default workflow stays fast while keeping deeper
coverage available when backing services are online.

## Tiers

| Tier | Scope | When to run | Notes |
| --- | --- | --- | --- |
| `unit` | Pure Python / Rust logic; in-memory dependencies only | Always (CI + local) | Deterministic, no external services required |
| `integration` | Requires Postgres, Redis, HTTP sidecars, or other infrastructure | Optional (run when services are available) | Covers cross-service behaviour and persistence |
| `e2e` | Full stack smoke/UX flows through gateways and auth layers | Manual or staged pipelines | High latency but validates deployment wiring |

## Pytest usage

The `pytest.ini` configuration now filters to the `unit` tier by default:

```bash
pytest          # runs only tests marked with @pytest.mark.unit
```

To exercise broader coverage:

```bash
pytest -m "unit or integration"        # enable integration suite once services are up
pytest -m integration --maxfail=1      # focus on infra-dependent tests
pytest -m e2e                          # execute end-to-end journeys
```

All integration and e2e directories declare their tier via `pytestmark`, so new modules inherit the
appropriate marker automatically. When adding a fast test that should run in CI, annotate it with
`@pytest.mark.unit` (or `pytestmark = pytest.mark.unit` at the module level).

## CI guidance

* **Pull requests:** rely on the default `pytest` invocation (unit only).
* **Nightly / full stack jobs:** bring up the Docker compose stack and run `pytest -m "unit or integration"`.
* **Manual verification:** run the `e2e` tier before releases or infrastructure changes.

Document any newly introduced external requirements inside the relevant test module, and prefer skipping via
`pytest.skip("Requires <service>", allow_module_level=True)` when a dependency is unavailable.
