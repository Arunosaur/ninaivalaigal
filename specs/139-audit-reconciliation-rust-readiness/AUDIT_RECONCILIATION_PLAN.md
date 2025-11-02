# Audit Reconciliation Plan (SPEC-139)

**Goal:** Normalize the audit-import drop so the repository returns to an intentional, maintainable state without losing useful documentation or tests.

---

## 1. Discovery & Categorization

1. **Inventory audit additions**
   - `specs/039`, `054`, `138` README inflations
   - `tasks/TAIGA_SPEC_027_028_REFACTORING_TASKS.md`, `tasks/active/*` reports
   - `tasks/scripts/*` Taiga automation helpers
   - `tests/integration/**` Rust + API scaffolding
   - `services/memory-service-rust/tests/**`
2. **Classify each artifact**
   - *Keep*: Relevant project documentation/specs still needed (e.g., SPEC history)
   - *Archive*: Historical reports better suited to `docs/audit/` or `.archive/`
   - *Trim*: Overly verbose files that can be summarized
   - *Delete*: Duplicated or clearly out-of-scope assets
3. **Record decisions** in this plan and link actual move/trim commits

---

## 2. Documentation Alignment

1. Update `SPEC_INDEX.md` if the audit created discrepancies (statuses, titles)
2. Ensure new SPEC-139 directory is registered once work begins
3. Cross-reference completion summaries and README files for audit-added SPEC docs
4. For archived artifacts, create `docs/audit/YYYY/` with changelog entries

---

## 3. Test & CI Strategy

1. Catalogue new integration tests and mark those needing environment prerequisites
2. Apply pytest markers (e.g., `@pytest.mark.rust_integration`) to Rust-dependent tests
3. Update `pytest.ini` and CI scripts to exclude gated suites by default
4. Document opt-in instructions in `RUST_INTEGRATION_GATE.md`

---

## 4. Taiga Script Hygiene

1. Review `tasks/scripts/` for hard-coded credentials
2. Refactor to consume environment variables or `.env.local`
3. Add README guidance around usage + secrets handling
4. If scripts are historical only, migrate to `docs/audit/tools/`

---

## 5. Communication & Approvals

1. Share reconciliation findings in `#platform-architecture`
2. Confirm with Documentation and Rust leads before deleting/archive moves
3. Track tasks via new Taiga epic referencing SPEC-139 deliverables

---

## 6. Exit Criteria

- [ ] Artifact disposition documented and executed
- [ ] SPEC index & completion summaries consistent
- [ ] CI passes without Rust service running
- [ ] Taiga tooling either production-ready or archived
- [ ] `VERIFICATION_2025-11-AUDIT.md` captures before/after evidence

---

*Owner:* Platform Architecture
*Collaborators:* Rust Team, Documentation, DevOps
