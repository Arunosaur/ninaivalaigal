# Rust Integration Gate Checklist

This gate ensures the Rust Memory Service becomes the default provider only when the platform is ready.

---

## 1. Technical Preconditions

- [x] **FastAPI compatibility**
  - [x] Memory API endpoints accept `request: Request` before dependency defaults (core API + server)
  - [x] Provider factory honors `USE_RUST_MEMORY` gating flag with Postgres fallback
- [ ] **Rust service availability**
  - Health endpoint: `curl http://localhost:13393/health` → 200
  - Metrics endpoint reachable & authenticated as required
- [ ] **JWT passthrough**
  - Python gateway forwards `Authorization` header to Rust service
  - Rust service validates tokens against current auth configuration
- [ ] **Error handling parity**
  - Rust responses mapped to existing Python `MemoryProviderError` patterns
  - Integration tests cover success + failure modes

---

## 2. Test & CI Requirements

- [x] Pytest marker `rust_integration` applied to Rust-dependent tests
- [ ] Default CI pipelines exclude the marker until flag enabled
- [ ] Optional CI job runs full suite with Rust service (nightly or on-demand)
- [ ] Load test baseline captured (Rust vs Postgres provider)

---

## 3. Operational Readiness

- [ ] Runbook for starting/stopping Rust service in dev/prod
- [ ] Observability dashboards include Rust metrics + alerts
- [ ] Rollback plan documented (revert feature flag, reset provider default)
- [ ] Stakeholder sign-off (Platform, Rust, DevOps)

---

## 4. Activation Steps

1. Enable feature flag in staging
2. Execute verification suite (`VERIFICATION_2025-11-AUDIT.md`)
3. Monitor for 24 hours
4. Enable in production once metrics stable
5. Update documentation and SPEC-139 completion summary

---

## 5. Sign-Off

- Platform Architect: ____________________ (date)
- Rust Lead: ____________________ (date)
- DevOps Lead: ____________________ (date)
