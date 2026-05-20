# Plan: Audit Rigour Tightening

- Trigger: User requested greater auditing rigour with near-zero error tolerance.
- Goal: Enforce fail-closed fact and citation verification across orchestration and audit agents.
- Agent sequence: @security -> @orchestrator -> @technical-validator -> @reference-manager -> @conflict-auditor -> @agent-updater
- Success criteria:
  - Fact verification requires explicit evidence mapping and UNVERIFIED blocking behavior.
  - Citation verification requires key-level, metadata-level, and resolver-level checks.
  - Workflows include mandatory gates that block progression on unresolved verification failures.
- Rollback notes:
  - Revert only the specific updated policy sections in affected files.
  - Preserve unrelated user changes.

- Completion date: 2026-04-18
- Final status: Completed
